"""Server gRPC bank: transfer, deduplikasi request_id, dan concurrency."""

from __future__ import annotations

import argparse
import random
import threading
import time
from concurrent import futures

import grpc

import bank_pb2 as pb
import bank_pb2_grpc as pb_grpc

DEFAULT_BALANCES: dict[str, float] = {"A": 1000.0, "B": 500.0}


class LayananBank(pb_grpc.LayananBankServicer):
    """Transfer service with request_id deduplication and configurable locking."""

    def __init__(
        self,
        balances: dict[str, float] | None = None,
        use_lock: bool = True,
        simulated_delay: float = 0.0,
        timeout_sim_prob: float = 0.0,
    ) -> None:
        self._balances: dict[str, float] = dict(balances or DEFAULT_BALANCES)
        self._dedup_cache: dict[str, pb.TransferResponse] = {}
        self._use_lock = use_lock
        self._lock = threading.Lock()
        self._simulated_delay = simulated_delay
        self._timeout_sim_prob = timeout_sim_prob

    @property
    def balances(self) -> dict[str, float]:
        """Akses langsung untuk pengujian."""
        return dict(self._balances)

    @property
    def dedup_cache_size(self) -> int:
        return len(self._dedup_cache)

    def Transfer(self, request: pb.TransferRequest, context: grpc.ServicerContext) -> pb.TransferResponse:
        # Simulasi delay pemrosesan (untuk pengujian timeout).
        if self._simulated_delay > 0:
            delay = random.uniform(0, self._simulated_delay)
            time.sleep(delay)

        if self._use_lock:
            self._lock.acquire()
        try:
            return self._do_transfer(request, context)
        finally:
            if self._use_lock:
                self._lock.release()

    def _do_transfer(self, request: pb.TransferRequest, context: grpc.ServicerContext) -> pb.TransferResponse:
        # Cek cache deduplikasi: request_id yang sama menghasilkan respons identik.
        if request.request_id in self._dedup_cache:
            return self._dedup_cache[request.request_id]

        # Validasi akun dan jumlah.
        if request.pengirim not in self._balances:
            context.abort(grpc.StatusCode.NOT_FOUND, f"Akun '{request.pengirim}' tidak ditemukan.")
        if request.penerima not in self._balances:
            context.abort(grpc.StatusCode.NOT_FOUND, f"Akun '{request.penerima}' tidak ditemukan.")
        if request.jumlah <= 0:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Jumlah transfer harus positif.")
        if self._balances[request.pengirim] < request.jumlah:
            context.abort(
                grpc.StatusCode.FAILED_PRECONDITION,
                f"Saldo {request.pengirim} tidak cukup "
                f"({self._balances[request.pengirim]:.2f} < {request.jumlah:.2f}).",
            )

        # Eksekusi transfer.
        # Tanpa lock: read-modify-write terpisah memunculkan race condition.
        if not self._use_lock:
            saldo_kirim = self._balances[request.pengirim]
            saldo_terima = self._balances[request.penerima]
            time.sleep(0.001)  # Perbesar jendela race condition.
            self._balances[request.pengirim] = saldo_kirim - request.jumlah
            self._balances[request.penerima] = saldo_terima + request.jumlah
        else:
            self._balances[request.pengirim] -= request.jumlah
            self._balances[request.penerima] += request.jumlah

        response = pb.TransferResponse(
            sukses=True,
            pesan=f"Transfer {request.jumlah:.0f} dari {request.pengirim} ke {request.penerima} berhasil.",
            request_id=request.request_id,
            saldo_pengirim=self._balances[request.pengirim],
            saldo_penerima=self._balances[request.penerima],
        )

        self._dedup_cache[request.request_id] = response

        # Tunda pengiriman respons setelah transfer tersimpan untuk memicu timeout client.
        if self._timeout_sim_prob > 0 and random.random() < self._timeout_sim_prob:
            time.sleep(3.0)

        return response

    def GetSaldo(self, request: pb.SaldoRequest, context: grpc.ServicerContext) -> pb.SaldoResponse:
        if self._use_lock:
            self._lock.acquire()
        try:
            if request.nama not in self._balances:
                context.abort(grpc.StatusCode.NOT_FOUND, f"Akun '{request.nama}' tidak ditemukan.")
            return pb.SaldoResponse(nama=request.nama, saldo=self._balances[request.nama])
        finally:
            if self._use_lock:
                self._lock.release()


def build_server(
    host: str = "127.0.0.1",
    port: int = 50051,
    max_workers: int = 10,
    use_lock: bool = True,
    simulated_delay: float = 0.0,
    timeout_sim_prob: float = 0.0,
    balances: dict[str, float] | None = None,
) -> tuple[grpc.Server, LayananBank]:
    """Membuat server gRPC dan mengembalikan instance server serta servicer."""
    servicer = LayananBank(
        balances=balances,
        use_lock=use_lock,
        simulated_delay=simulated_delay,
        timeout_sim_prob=timeout_sim_prob,
    )
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    pb_grpc.add_LayananBankServicer_to_server(servicer, server)
    server.add_insecure_port(f"{host}:{port}")
    return server, servicer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Server gRPC bank.")
    parser.add_argument("--host", default="127.0.0.1", help="Host bind (default: 127.0.0.1).")
    parser.add_argument("--port", default=50051, type=int, help="Port gRPC (default: 50051).")
    parser.add_argument("--max-workers", default=10, type=int, help="Jumlah worker (default: 10).")
    parser.add_argument("--no-lock", action="store_true", help="Nonaktifkan locking untuk demonstrasi race condition.")
    parser.add_argument("--delay", default=0.0, type=float, help="Simulasi delay maks dalam detik (default: 0).")
    parser.add_argument(
        "--simulate-timeout-prob",
        default=0.0,
        type=float,
        help="Probabilitas simulasi timeout (sleep 3 detik setelah transfer).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server, servicer = build_server(
        host=args.host,
        port=args.port,
        max_workers=args.max_workers,
        use_lock=not args.no_lock,
        simulated_delay=args.delay,
        timeout_sim_prob=args.simulate_timeout_prob,
    )
    server.start()
    lock_status = "TANPA LOCK (race condition mode)" if args.no_lock else "dengan lock"
    print(f"Server bank berjalan di {args.host}:{args.port} "
          f"(workers={args.max_workers}, {lock_status}, delay={args.delay}s).")
    print(f"Saldo awal: {servicer.balances}")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
        server.stop(grace=0)


if __name__ == "__main__":
    main()
