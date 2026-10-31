"""Simulasi race condition pada transfer konkuren: dengan lock vs tanpa lock (L3.3).

Membuktikan:
1. Dengan lock: Konsistensi data terjaga penuh (total saldo tetap 1500, saldo A=500, B=1000).
2. Tanpa lock: Terjadi race condition (lost update) akibat operasi read-modify-write
   yang disela oleh thread lain, merusak integritas saldo.
"""

from __future__ import annotations

import concurrent.futures
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(__file__))

import grpc
import bank_pb2 as pb
import bank_pb2_grpc as pb_grpc
from server_transfer import build_server
from client_transfer import get_saldo

NUM_CLIENTS = 10
TRANSFERS_PER_CLIENT = 5
TOTAL_TRANSFERS = NUM_CLIENTS * TRANSFERS_PER_CLIENT  # 50
AMOUNT = 10.0


def run_concurrent_transfers(port: int, use_lock: bool) -> tuple[float, float, float]:
    """Menjalankan server dan 50 transfer konkuren dari 10 thread client."""
    server, servicer = build_server(
        port=port,
        max_workers=NUM_CLIENTS,
        use_lock=use_lock,
        balances={"A": 1000.0, "B": 500.0},
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
                        timeout=5.0,
                    )
                    successes.append(res.sukses)
                except grpc.RpcError as err:
                    print(f"  [Client {client_id}] error: {err.code()}")
                    successes.append(False)
        return successes

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_CLIENTS) as executor:
            futs = [executor.submit(client_worker, i) for i in range(NUM_CLIENTS)]
            all_results = [f.result() for f in futs]

        # Cek saldo akhir langsung dari servicer
        saldo_a = servicer.balances["A"]
        saldo_b = servicer.balances["B"]
        total = saldo_a + saldo_b
        return saldo_a, saldo_b, total
    finally:
        server.stop(grace=0)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print(f"=== L3.3: Concurrency Test (simulate_race_condition) ===\n")
    print(f"Konfigurasi: {NUM_CLIENTS} threads x {TRANSFERS_PER_CLIENT} transfer = {TOTAL_TRANSFERS} transfer.")
    print(f"Saldo awal: A=1000, B=500 (Total: 1500).")
    print(f"Jika 50 x {AMOUNT:.0f} transfer berhasil:")
    print(f"  Expected saldo A = 1000 - 500 = 500")
    print(f"  Expected saldo B = 500 + 500 = 1000")
    print(f"  Expected total   = 1500\n")

    # 1. Uji DENGAN LOCK
    print("--- 1. Pengujian DENGAN LOCK (Thread-Safe) ---")
    saldo_a_lock, saldo_b_lock, total_lock = run_concurrent_transfers(port=50073, use_lock=True)
    print(f"Hasil Dengan Lock:")
    print(f"  Saldo A : {saldo_a_lock:.0f}")
    print(f"  Saldo B : {saldo_b_lock:.0f}")
    print(f"  Total   : {total_lock:.0f}")

    assert saldo_a_lock == 500.0, f"Saldo A salah: {saldo_a_lock}"
    assert saldo_b_lock == 1000.0, f"Saldo B salah: {saldo_b_lock}"
    assert total_lock == 1500.0, f"Total saldo berubah: {total_lock}"
    print("  -> [OK] Integritas data terjaga 100% sempurna dengan Lock!\n")

    # 2. Uji TANPA LOCK
    print("--- 2. Pengujian TANPA LOCK (Race Condition Demo) ---")
    saldo_a_nolock, saldo_b_nolock, total_nolock = run_concurrent_transfers(port=50074, use_lock=False)
    print(f"Hasil Tanpa Lock:")
    print(f"  Saldo A : {saldo_a_nolock:.0f}")
    print(f"  Saldo B : {saldo_b_nolock:.0f}")
    print(f"  Total   : {total_nolock:.0f}")

    has_race = (saldo_a_nolock != 500.0) or (saldo_b_nolock != 1000.0) or (total_nolock != 1500.0)
    if has_race:
        print(f"  -> [TERBUKTI] Terjadi Lost Update! Saldo rusak akibat race condition:")
        if total_nolock != 1500.0:
            print(f"     Penyimpangan total uang: {total_nolock - 1500.0:+.0f} (uang tercipta atau hilang!)")
        if saldo_a_nolock != 500.0:
            print(f"     Penyimpangan saldo A: {saldo_a_nolock - 500.0:+.0f}")
        if saldo_b_nolock != 1000.0:
            print(f"     Penyimpangan saldo B: {saldo_b_nolock - 1000.0:+.0f}")
    else:
        print("  -> Catatan: Race condition tidak terjadi pada run ini (kebetulan urutan instruksi).")

    print("\n[OK] L3.3 TERVALIDASI: Locking mutlak diperlukan pada server gRPC multi-threaded.")


if __name__ == "__main__":
    main()
