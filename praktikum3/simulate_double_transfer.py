"""Simulasi double transfer: efek request_id baru di setiap retry vs request_id tetap (L3.2).

Membuktikan:
1. Skenario benar (at-most-once): retry dengan request_id SAMA tidak menyebabkan
   transfer ganda, dan respons yang dikembalikan identik.
2. Skenario salah: retry dengan request_id BARU menyebabkan transfer ganda
   (double spending).
3. Skenario timeout: server menyimpan transaksi lalu menunda respons di luar lock;
   retry dengan ID yang sama mendapat cache hit tanpa eksekusi kedua.
"""

from __future__ import annotations

import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(__file__))

import grpc
import bank_pb2 as pb
import bank_pb2_grpc as pb_grpc
from server_transfer import build_server
from client_transfer import get_saldo, transfer_with_retry

PORT = 50072
PORT_TIMEOUT = 50078


def run_timeout_retry_scenario() -> None:
    """Membuktikan retry setelah timeout tidak mengeksekusi transfer dua kali."""
    print("--- Skenario 3: Timeout Setelah Commit, Retry dengan ID SAMA ---")
    server, servicer = build_server(
        port=PORT_TIMEOUT,
        balances={"A": 1000.0, "B": 500.0},
        timeout_sim_prob=1.0,
    )
    server.start()
    print(f"Server timeout-test berjalan di port {PORT_TIMEOUT} "
          "(respons pertama selalu ditunda 3 detik).")

    try:
        with grpc.insecure_channel(f"127.0.0.1:{PORT_TIMEOUT}") as channel:
            stub = pb_grpc.LayananBankStub(channel)
            request_id = f"tx-timeout-{uuid.uuid4().hex[:8]}"
            started_at = time.perf_counter()
            response = transfer_with_retry(
                stub,
                request_id,
                "A",
                "B",
                100.0,
                max_retries=2,
                base_delay=0.2,
                timeout=0.5,
            )
            elapsed = time.perf_counter() - started_at

            saldo_a = get_saldo(stub, "A")
            saldo_b = get_saldo(stub, "B")
            print(f"  Respons akhir : {response.pesan}")
            print(f"  Saldo A/B     : {saldo_a:.0f}/{saldo_b:.0f}")
            print(f"  Cache entries : {servicer.dedup_cache_size}")
            print(f"  Waktu total   : {elapsed:.2f} s (termasuk retry)")

            assert response.sukses, "Transfer timeout-test gagal."
            assert saldo_a == 900.0, (
                f"Saldo A seharusnya 900 (satu eksekusi), aktual: {saldo_a}"
            )
            assert saldo_b == 600.0, (
                f"Saldo B seharusnya 600 (satu eksekusi), aktual: {saldo_b}"
            )
            assert servicer.dedup_cache_size == 1, (
                f"Cache seharusnya 1 entri, aktual: {servicer.dedup_cache_size}"
            )

        print("  -> [OK] Retry setelah timeout memakai cache; transfer tidak dijalankan ulang.")
        print("  -> Catatan: ini at-most-once selama cache server masih hidup.\n")
    finally:
        server.stop(grace=0)


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

            assert res1 == res2, (
                "Respons retry dengan request_id sama harus identik.\n"
                f"  pertama: {res1}\n  kedua  : {res2}"
            )

            saldo_a_1 = get_saldo(stub, "A")
            saldo_b_1 = get_saldo(stub, "B")
            print(f"Saldo setelah retry ID sama: A={saldo_a_1:.0f}, B={saldo_b_1:.0f}")
            assert saldo_a_1 == 900.0, f"Saldo A harus 900, aktual: {saldo_a_1}"
            assert saldo_b_1 == 600.0, f"Saldo B harus 600, aktual: {saldo_b_1}"
            assert servicer.dedup_cache_size == 1, (
                f"Cache seharusnya 1 entri, aktual: {servicer.dedup_cache_size}"
            )
            print("  -> HASIL: Saldo hanya berkurang 1x (100). Deduplikasi mencegat transfer ganda.\n")

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

            # Saldo awal skenario 2 adalah 900. Karena transfer 100 dieksekusi 2 kali,
            # saldo akhir menjadi 900 - 200 = 700.
            assert saldo_a_2 == 700.0, f"Saldo A seharusnya 700 karena transfer ganda 2x100, aktual: {saldo_a_2}"
            print("  -> BAHAYA: Saldo berkurang 2x (total 200) padahal pengguna hanya berniat transfer 1x!")
            print("  -> Saldo A awal skenario 2: 900, setelah 2 transfer: 700 (A berkurang 200 alih-alih 100).")
            print("  -> Penyebab: Server tidak mengenali bahwa request kedua adalah retry karena ID berbeda.\n")

        # Skenario timeout dijalankan pada server terpisah setelah server utama selesai.
        run_timeout_retry_scenario()

        print("[OK] L3.2 TERVALIDASI: ID tetap menjamin idempotensi, ID baru memicu transfer ganda.")
        print("[OK] Retry setelah timeout dengan ID sama tidak mengeksekusi transfer kedua.")

    finally:
        server.stop(grace=0)
        print("Server dihentikan.")


if __name__ == "__main__":
    main()
