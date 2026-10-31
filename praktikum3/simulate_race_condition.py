"""Simulasi race condition pada transfer konkuren: dengan lock vs tanpa lock (L3.3).

Mode tanpa lock memakai threading.Barrier sebagai hook pengujian. Barrier membuat
sekelompok thread membaca saldo yang sama sebelum ada yang menulis, sehingga
lost update dapat direproduksi secara terkontrol, bukan bergantung pada keberuntungan
penjadwalan. Barrier tidak dipakai pada mode produksi.

Pembuktian:
1. Dengan lock: setiap ronde harus menghasilkan A=500, B=1000, total=1500.
2. Tanpa lock + barrier: setiap ronde harus menghasilkan A>500 dan B<1000 karena
   sebagian pembaruan saldo tertimpa (lost update).
"""

from __future__ import annotations

import concurrent.futures
import os
import sys
import threading
import uuid

sys.path.insert(0, os.path.dirname(__file__))

import grpc
import bank_pb2 as pb
import bank_pb2_grpc as pb_grpc
from server_transfer import build_server

NUM_CLIENTS = 10
TRANSFERS_PER_CLIENT = 5
TOTAL_TRANSFERS = NUM_CLIENTS * TRANSFERS_PER_CLIENT  # 50
AMOUNT = 10.0
ROUNDS = 3
INITIAL_A = 1000.0
INITIAL_B = 500.0
EXPECTED_A = INITIAL_A - TOTAL_TRANSFERS * AMOUNT  # 500
EXPECTED_B = INITIAL_B + TOTAL_TRANSFERS * AMOUNT  # 1000


def run_concurrent_transfers(
    port: int,
    use_lock: bool,
    race_barrier: threading.Barrier | None = None,
) -> tuple[float, float, float]:
    """Menjalankan server dan 50 transfer konkuren dari 10 thread client."""
    server, servicer = build_server(
        port=port,
        max_workers=NUM_CLIENTS,
        use_lock=use_lock,
        balances={"A": INITIAL_A, "B": INITIAL_B},
        race_barrier=race_barrier,
    )
    server.start()

    def client_worker(client_id: int) -> list[bool]:
        successes = []
        with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
            stub = pb_grpc.LayananBankStub(channel)
            for j in range(TRANSFERS_PER_CLIENT):
                req_id = f"c{client_id}-tx{j}-{uuid.uuid4().hex[:6]}"
                try:
                    res = stub.Transfer(
                        pb.TransferRequest(
                            request_id=req_id,
                            pengirim="A",
                            penerima="B",
                            jumlah=AMOUNT,
                        ),
                        timeout=10.0,
                    )
                    successes.append(res.sukses)
                except grpc.RpcError as err:
                    print(f"  [Client {client_id}] error: {err.code()}")
                    successes.append(False)
        return successes

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_CLIENTS) as executor:
            futures = [executor.submit(client_worker, i) for i in range(NUM_CLIENTS)]
            all_results = [future.result() for future in futures]

        if not all(all(result) for result in all_results):
            raise AssertionError("Ada transfer yang gagal; hasil race tidak dapat ditafsirkan.")

        saldo_a = servicer.balances["A"]
        saldo_b = servicer.balances["B"]
        total = saldo_a + saldo_b
        return saldo_a, saldo_b, total
    finally:
        server.stop(grace=0)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=== L3.3: Concurrency Test (simulate_race_condition) ===\n")
    print(f"Konfigurasi: {NUM_CLIENTS} threads x {TRANSFERS_PER_CLIENT} transfer = {TOTAL_TRANSFERS} transfer.")
    print(f"Saldo awal: A={INITIAL_A:.0f}, B={INITIAL_B:.0f} (total {INITIAL_A + INITIAL_B:.0f}).")
    print(f"Jika semua transfer diterapkan: A={EXPECTED_A:.0f}, B={EXPECTED_B:.0f}.")
    print(f"Ronde pengujian: {ROUNDS} dengan lock + {ROUNDS} tanpa lock (barrier terkontrol).\n")

    # 1. Uji DENGAN LOCK - invariant harus selalu tepat.
    print("--- 1. Pengujian DENGAN LOCK (Thread-Safe) ---")
    for round_index in range(1, ROUNDS + 1):
        saldo_a, saldo_b, total = run_concurrent_transfers(port=50073, use_lock=True)
        print(f"  Ronde {round_index}: A={saldo_a:.0f}, B={saldo_b:.0f}, total={total:.0f}")
        assert saldo_a == EXPECTED_A, f"Ronde {round_index}: saldo A salah: {saldo_a}"
        assert saldo_b == EXPECTED_B, f"Ronde {round_index}: saldo B salah: {saldo_b}"
        assert total == INITIAL_A + INITIAL_B, f"Ronde {round_index}: total saldo berubah: {total}"
    print("  -> [OK] Dengan lock, seluruh ronde konsisten.\n")

    # 2. Uji TANPA LOCK dengan barrier: paksa beberapa thread membaca nilai sama.
    print("--- 2. Pengujian TANPA LOCK (barrier mengontrol interleaving) ---")
    for round_index in range(1, ROUNDS + 1):
        barrier = threading.Barrier(NUM_CLIENTS)
        saldo_a, saldo_b, total = run_concurrent_transfers(
            port=50074,
            use_lock=False,
            race_barrier=barrier,
        )
        print(f"  Ronde {round_index}: A={saldo_a:.0f}, B={saldo_b:.0f}, total={total:.0f}")
        assert saldo_a > EXPECTED_A, (
            f"Ronde {round_index}: lost update tidak terdeteksi pada A "
            f"(A={saldo_a}, seharusnya > {EXPECTED_A})."
        )
        assert saldo_b < EXPECTED_B, (
            f"Ronde {round_index}: lost update tidak terdeteksi pada B "
            f"(B={saldo_b}, seharusnya < {EXPECTED_B})."
        )

    print("  -> [OK] Setiap ronde tanpa lock membuktikan lost update secara terkontrol.")
    print("     Barrier adalah hook pengujian, bukan mekanisme produksi.\n")

    print("[OK] L3.3 TERVALIDASI: Locking menjaga invariant; tanpa lock + barrier")
    print("     saldo A/B menyimpang secara konsisten dan dapat diulang.")


if __name__ == "__main__":
    main()
