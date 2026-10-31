"""Simulasi double transfer: efek request_id baru di setiap retry vs request_id tetap (L3.2).

Membuktikan:
1. Skenario benar (at-most-once): retry dengan request_id SAMA tidak menyebabkan transfer ganda.
2. Skenario salah: retry dengan request_id BARU menyebabkan transfer ganda (double spending).
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
from client_transfer import get_saldo

PORT = 50072


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=== L3.2: Efek Request ID pada Retry dan Transfer Ganda (simulate_double_transfer) ===\n")

    server, servicer = build_server(port=PORT, balances={"A": 1000.0, "B": 500.0})
    server.start()
    print(f"Server berjalan di port {PORT}.")
    print(f"Saldo awal: {servicer.balances}\n")

    try:
        with grpc.insecure_channel(f"127.0.0.1:{PORT}") as channel:
            stub = pb_grpc.LayananBankStub(channel)

            # ---------------------------------------------------------
            # Skenario 1: Retry dengan request_id yang SAMA (Idempoten)
            # ---------------------------------------------------------
            print("--- Skenario 1: Retry dengan Request ID yang SAMA ---")
            same_id = f"tx-safe-{uuid.uuid4().hex[:8]}"
            print(f"Mengirim transfer pertama (ID: {same_id})...")
            res1 = stub.Transfer(
                pb.TransferRequest(
                    request_id=same_id, pengirim="A", penerima="B", jumlah=100.0
                )
            )
            print(f"  Hasil 1: {res1.pesan} (Saldo A={res1.saldo_pengirim:.0f}, B={res1.saldo_penerima:.0f})")

            print(f"Simulasi retry (karena client timeout/reconnect) dengan ID SAMA ({same_id})...")
            res2 = stub.Transfer(
                pb.TransferRequest(
                    request_id=same_id, pengirim="A", penerima="B", jumlah=100.0
                )
            )
            print(f"  Hasil 2 (retry): {res2.pesan} (Saldo A={res2.saldo_pengirim:.0f}, B={res2.saldo_penerima:.0f})")

            saldo_a_1 = get_saldo(stub, "A")
            saldo_b_1 = get_saldo(stub, "B")
            print(f"Saldo setelah retry ID sama: A={saldo_a_1:.0f}, B={saldo_b_1:.0f}")
            assert saldo_a_1 == 900.0, f"Saldo A harus 900, aktual: {saldo_a_1}"
            assert saldo_b_1 == 600.0, f"Saldo B harus 600, aktual: {saldo_b_1}"
            print("  -> HASIL: Saldo hanya berkurang 1x (100). Deduplikasi berhasil mencegat transfer ganda!\n")

            # ---------------------------------------------------------
            # Skenario 2: Retry dengan request_id BARU (Non-idempoten / BUG)
            # ---------------------------------------------------------
            print("--- Skenario 2: Retry dengan Request ID BARU (Transfer Ganda) ---")
            id_attempt1 = f"tx-bad-{uuid.uuid4().hex[:8]}"
            id_attempt2 = f"tx-bad-{uuid.uuid4().hex[:8]}"  # ID baru saat retry!

            print(f"Percobaan 1 (ID: {id_attempt1})...")
            res3 = stub.Transfer(
                pb.TransferRequest(
                    request_id=id_attempt1, pengirim="A", penerima="B", jumlah=100.0
                )
            )
            print(f"  Hasil 1: {res3.pesan} (Saldo A={res3.saldo_pengirim:.0f}, B={res3.saldo_penerima:.0f})")

            print(f"Simulasi retry dengan ID BARU ({id_attempt2}) akibat bug pada client...")
            res4 = stub.Transfer(
                pb.TransferRequest(
                    request_id=id_attempt2, pengirim="A", penerima="B", jumlah=100.0
                )
            )
            print(f"  Hasil 2: {res4.pesan} (Saldo A={res4.saldo_pengirim:.0f}, B={res4.saldo_penerima:.0f})")

            saldo_a_2 = get_saldo(stub, "A")
            saldo_b_2 = get_saldo(stub, "B")
            print(f"Saldo setelah retry ID baru: A={saldo_a_2:.0f}, B={saldo_b_2:.0f}")

            # Saldo awal skenario 2 adalah 900. Karena transfer 100 dieksekusi 2 kali (transfer ganda),
            # saldo akhir menjadi 900 - 200 = 700.
            assert saldo_a_2 == 700.0, f"Saldo A seharusnya 700 karena transfer ganda 2x100, aktual: {saldo_a_2}"
            print("  -> BAHAYA: Saldo berkurang 2x (total 200) padahal pengguna hanya berniat transfer 1x!")
            print("  -> Saldo A awal skenario 2: 900, setelah 2 transfer: 700 (A berkurang 200 alih-alih 100).")
            print("  -> Penyebab: Server tidak mengenali bahwa request kedua adalah retry karena ID berbeda.\n")

            print("[OK] L3.2 TERVALIDASI: ID tetap menjamin idempotensi, ID baru memicu transfer ganda.")

    finally:
        server.stop(grace=0)
        print("Server dihentikan.")


if __name__ == "__main__":
    main()
