"""Verifikasi 20 transfer berulang A ke B dengan deduplikasi (L3.1).

Setiap transfer mengirim 10 dari A ke B. Setelah 20 transfer:
- A = 1000 - 200 = 800
- B = 500 + 200 = 700
- Total saldo tetap 1500
"""

from __future__ import annotations

import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(__file__))

import grpc

import bank_pb2 as pb
import bank_pb2_grpc as pb_grpc
from server_transfer import build_server
from client_transfer import transfer_with_retry, get_saldo

PORT = 50071
NUM_TRANSFERS = 20
AMOUNT_PER_TRANSFER = 10.0


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=== L3.1: 20 Transfer A->B dengan Deduplikasi (verify_transfer) ===\n")

    # Start server secara programatik.
    server, servicer = build_server(port=PORT)
    server.start()
    print(f"Server berjalan di port {PORT}.")
    print(f"Saldo awal: {servicer.balances}\n")

    try:
        with grpc.insecure_channel(f"127.0.0.1:{PORT}") as channel:
            stub = pb_grpc.LayananBankStub(channel)

            for i in range(NUM_TRANSFERS):
                req_id = str(uuid.uuid4())
                response = transfer_with_retry(
                    stub, req_id, "A", "B", AMOUNT_PER_TRANSFER,
                )
                print(f"  [{i + 1:2d}] {response.pesan} "
                      f"(A={response.saldo_pengirim:.0f}, B={response.saldo_penerima:.0f})")

            # Verifikasi saldo akhir.
            saldo_a = get_saldo(stub, "A")
            saldo_b = get_saldo(stub, "B")

        print(f"\n--- Hasil ---")
        print(f"Saldo A : {saldo_a:.0f} (diharapkan: 800)")
        print(f"Saldo B : {saldo_b:.0f} (diharapkan: 700)")
        print(f"Total   : {saldo_a + saldo_b:.0f} (diharapkan: 1500)")
        print(f"Dedup cache: {servicer.dedup_cache_size} entries")

        assert saldo_a == 800.0, f"Saldo A salah: {saldo_a}"
        assert saldo_b == 700.0, f"Saldo B salah: {saldo_b}"
        assert saldo_a + saldo_b == 1500.0, f"Total salah: {saldo_a + saldo_b}"

        print("\n[OK] LULUS: Saldo total tetap 1500, A berkurang tepat 200.")

    finally:
        server.stop(grace=0)
        print("Server dihentikan.")


if __name__ == "__main__":
    main()
