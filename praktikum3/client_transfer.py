"""Praktikum RPC - Komputasi Paralel dan Terdistribusi

Nama : Muhammad Fadhlan Aminullah
NPM  : 247006111151

Client gRPC bank dengan retry exponential backoff dan failover."""

from __future__ import annotations

import argparse
import time
import uuid

import grpc

import bank_pb2 as pb
import bank_pb2_grpc as pb_grpc


def transfer_with_retry(
    stub: pb_grpc.LayananBankStub,
    request_id: str,
    pengirim: str,
    penerima: str,
    jumlah: float,
    max_retries: int = 3,
    base_delay: float = 0.5,
    timeout: float = 2.0,
    new_request_id_on_retry: bool = False,
) -> pb.TransferResponse:
    """Mengirim Transfer RPC dengan retry dan exponential backoff.

    Jika new_request_id_on_retry=False (default): menggunakan request_id yang SAMA
    untuk setiap percobaan ulang (at-most-once semantics, mencegah transfer ganda).
    Jika new_request_id_on_retry=True: men-generate request_id baru di setiap retry
    (simulasi bug client yang menyebabkan transfer ganda).
    """
    last_error = None
    current_req_id = request_id

    for attempt in range(max_retries + 1):
        if attempt > 0 and new_request_id_on_retry:
            current_req_id = str(uuid.uuid4())
            print(f"  [BUG SIMULATION] Menggunakan request_id BARU pada retry: {current_req_id[:8]}...")

        try:
            response = stub.Transfer(
                pb.TransferRequest(
                    request_id=current_req_id,
                    pengirim=pengirim,
                    penerima=penerima,
                    jumlah=jumlah,
                ),
                timeout=timeout,
            )
            return response
        except grpc.RpcError as error:
            last_error = error
            retryable = error.code() in (
                grpc.StatusCode.UNAVAILABLE,
                grpc.StatusCode.DEADLINE_EXCEEDED,
            )
            if retryable and attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                print(f"  [retry {attempt + 1}/{max_retries}] {error.code().name}, "
                      f"menunggu {delay:.1f}s...")
                time.sleep(delay)
            else:
                raise
    raise last_error  # Tidak seharusnya tercapai.


def get_saldo(stub: pb_grpc.LayananBankStub, nama: str, timeout: float = 2.0) -> float:
    response = stub.GetSaldo(pb.SaldoRequest(nama=nama), timeout=timeout)
    return response.saldo


def run_demo(host: str, port: int) -> None:
    """Demo sederhana: satu transfer dan cek saldo."""
    with grpc.insecure_channel(f"{host}:{port}") as channel:
        stub = pb_grpc.LayananBankStub(channel)

        print("Saldo sebelum transfer:")
        for nama in ("A", "B"):
            print(f"  {nama}: {get_saldo(stub, nama):.2f}")

        req_id = str(uuid.uuid4())
        print(f"\nTransfer 100 dari A ke B (request_id={req_id[:8]}...):")
        response = transfer_with_retry(stub, req_id, "A", "B", 100.0)
        print(f"  {response.pesan}")

        print("\nSaldo setelah transfer:")
        for nama in ("A", "B"):
            print(f"  {nama}: {get_saldo(stub, nama):.2f}")

        # Kirim request_id yang sama lagi (deduplikasi).
        print(f"\nRetry dengan request_id yang SAMA ({req_id[:8]}...):")
        response2 = transfer_with_retry(stub, req_id, "A", "B", 100.0)
        print(f"  {response2.pesan}")
        print(f"  Saldo A tetap: {get_saldo(stub, 'A'):.2f} (deduplikasi berhasil)")


class FailoverBankClient:
    """Client bank dengan dukungan failover otomatis antar endpoint server."""

    def __init__(self, endpoints: list[str]) -> None:
        if not endpoints:
            raise ValueError("Daftar endpoints tidak boleh kosong.")
        self.endpoints = list(endpoints)
        self.active_index = 0

    @property
    def current_endpoint(self) -> str:
        return self.endpoints[self.active_index]

    def _get_stub(self, endpoint: str) -> tuple[grpc.Channel, pb_grpc.LayananBankStub]:
        channel = grpc.insecure_channel(endpoint)
        stub = pb_grpc.LayananBankStub(channel)
        return channel, stub

    def transfer(
        self,
        request_id: str,
        pengirim: str,
        penerima: str,
        jumlah: float,
        timeout: float = 2.0,
    ) -> pb.TransferResponse:
        """Mengirim transfer dengan failover ke server cadangan jika server aktif mati."""
        attempts = 0
        total_endpoints = len(self.endpoints)
        last_error = None

        while attempts < total_endpoints:
            endpoint = self.current_endpoint
            channel, stub = self._get_stub(endpoint)
            try:
                # Coba kirim RPC ke endpoint saat ini
                res = stub.Transfer(
                    pb.TransferRequest(
                        request_id=request_id,
                        pengirim=pengirim,
                        penerima=penerima,
                        jumlah=jumlah,
                    ),
                    timeout=timeout,
                )
                channel.close()
                return res
            except grpc.RpcError as err:
                channel.close()
                last_error = err
                if err.code() in (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED):
                    print(f"  [Failover Alert] Server {endpoint} tidak tersedia ({err.code().name}).")
                    # Beralih ke endpoint berikutnya
                    self.active_index = (self.active_index + 1) % total_endpoints
                    attempts += 1
                    next_endpoint = self.current_endpoint
                    print(f"  [Failover Alert] Mencoba endpoint cadangan: {next_endpoint}...")
                else:
                    # Error bisnis (e.g. FAILED_PRECONDITION / INVALID_ARGUMENT), jangan failover
                    raise
        raise last_error

    def get_saldo(self, nama: str, timeout: float = 2.0) -> float:
        """Mengambil saldo dengan failover otomatis jika endpoint aktif gagal."""
        for _ in range(len(self.endpoints)):
            endpoint = self.current_endpoint
            channel, stub = self._get_stub(endpoint)
            try:
                res = stub.GetSaldo(pb.SaldoRequest(nama=nama), timeout=timeout)
                channel.close()
                return res.saldo
            except grpc.RpcError as err:
                channel.close()
                if err.code() in (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED):
                    self.active_index = (self.active_index + 1) % len(self.endpoints)
                else:
                    raise
        raise RuntimeError("Semua endpoint tidak dapat dihubungi.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Client bank gRPC dengan retry dan failover.")
    parser.add_argument("--host", default="127.0.0.1", help="Host gRPC server.")
    parser.add_argument("--port", default=50051, type=int, help="Port gRPC server.")
    parser.add_argument(
        "--action",
        choices=["demo", "transfer", "saldo"],
        default="demo",
        help="Aksi yang dijalankan (default: demo).",
    )
    parser.add_argument("--pengirim", default="A", help="Nama pengirim transfer (default: A).")
    parser.add_argument("--penerima", default="B", help="Nama penerima transfer (default: B).")
    parser.add_argument("--jumlah", default=100.0, type=float, help="Jumlah uang yang ditransfer (default: 100).")
    parser.add_argument("--nama", default="A", help="Nama akun untuk cek saldo (default: A).")
    parser.add_argument(
        "--failover-endpoints",
        default="",
        help="Daftar endpoint dipisah koma (misal: '127.0.0.1:50051,127.0.0.1:50052').",
    )
    parser.add_argument(
        "--new-uuid-on-retry",
        action="store_true",
        help="Gunakan UUID baru setiap kali retry (simulasi transfer ganda).",
    )
    return parser.parse_args()


def tampilkan_header(judul: str, peran: str | None = None) -> None:
    print("=" * 60)
    print(judul)
    print("Mata Kuliah : Komputasi Paralel dan Terdistribusi")
    print("Nama        : Muhammad Fadhlan Aminullah")
    print("NPM         : 247006111151")
    if peran:
        print(f"Peran       : {peran}")
    print("=" * 60)


def main() -> None:
    args = parse_args()
    tampilkan_header("PRAKTIKUM 3 - CLIENT BANK gRPC (L3.1-L3.5)", "Client")

    # Mode Failover Multi-Endpoint
    if args.failover_endpoints:
        endpoints = [ep.strip() for ep in args.failover_endpoints.split(",") if ep.strip()]
        client = FailoverBankClient(endpoints=endpoints)
        print(f"Menghubungkan ke failover cluster: {endpoints}")
        if args.action == "saldo":
            saldo = client.get_saldo(args.nama)
            print(f"Saldo {args.nama}: {saldo:.2f}")
        else:
            req_id = str(uuid.uuid4())
            res = client.transfer(req_id, args.pengirim, args.penerima, args.jumlah)
            print(f"Hasil: {res.pesan} (A={res.saldo_pengirim:.2f}, B={res.saldo_penerima:.2f})")
        return

    # Mode Standar Tunggal
    try:
        if args.action == "demo":
            run_demo(args.host, args.port)
        elif args.action == "saldo":
            with grpc.insecure_channel(f"{args.host}:{args.port}") as channel:
                stub = pb_grpc.LayananBankStub(channel)
                saldo = get_saldo(stub, args.nama)
                print(f"Saldo {args.nama}: {saldo:.2f}")
        elif args.action == "transfer":
            with grpc.insecure_channel(f"{args.host}:{args.port}") as channel:
                stub = pb_grpc.LayananBankStub(channel)
                req_id = str(uuid.uuid4())
                res = transfer_with_retry(
                    stub,
                    request_id=req_id,
                    pengirim=args.pengirim,
                    penerima=args.penerima,
                    jumlah=args.jumlah,
                    new_request_id_on_retry=args.new_uuid_on_retry,
                )
                print(f"Hasil: {res.pesan}")
                print(f"Saldo {args.pengirim}: {res.saldo_pengirim:.2f} | Saldo {args.penerima}: {res.saldo_penerima:.2f}")
    except grpc.RpcError as error:
        print(f"gRPC gagal: {error.code().name} - {error.details()}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
