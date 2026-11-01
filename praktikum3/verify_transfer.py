"""Praktikum RPC - Komputasi Paralel dan Terdistribusi

Nama : Muhammad Fadhlan Aminullah
NPM  : 247006111151

Verifikasi 20 transfer berulang A ke B dengan deduplikasi (L3.1).

Setiap transfer mengirim 10 dari A ke B. Setelah 20 transfer:
- A = 1000 - 200 = 800
- B = 500 + 200 = 700
- Total saldo tetap 1500

Skrip juga memverifikasi bahwa request_id kosong/spasi ditolak dengan
INVALID_ARGUMENT sebelum menyentuh saldo.
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


def assert_empty_request_id_rejected(stub: pb_grpc.LayananBankStub) -> None:
    """Memastikan request_id kosong/spasi ditolak tanpa mengubah saldo."""
    for bad_id in ("", "   "):
        try:
            stub.Transfer(
                pb.TransferRequest(
                    request_id=bad_id,
                    pengirim="A",
                    penerima="B",
                    jumlah=AMOUNT_PER_TRANSFER,
                ),
                timeout=3.0,
            )
        except grpc.RpcError as error:
            if error.code() != grpc.StatusCode.INVALID_ARGUMENT:
                raise AssertionError(
                    f"request_id {bad_id!r} menghasilkan {error.code().name}, "
                    "seharusnya INVALID_ARGUMENT."
                ) from error
            print(f"  [OK] request_id {bad_id!r} ditolak: {error.code().name}")
        else:
            raise AssertionError(
                f"request_id {bad_id!r} diterima, seharusnya ditolak."
            )


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
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    tampilkan_header("PRAKTIKUM 3.1 - PENGUJIAN RETRY DENGAN REQUEST ID DAN AT-MOST-ONCE", "Test")
    print("=== L3.1: 20 Transfer A->B dengan Deduplikasi (verify_transfer) ===\n")

    # Start server secara programatik.
    server, servicer = build_server(port=PORT)
    server.start()
    print(f"Server berjalan di port {PORT}.")
    print(f"Saldo awal: {servicer.balances}\n")

    try:
        with grpc.insecure_channel(f"127.0.0.1:{PORT}") as channel:
            stub = pb_grpc.LayananBankStub(channel)

            print("--- Validasi request_id ---")
            assert_empty_request_id_rejected(stub)
            saldo_setelah_validasi = get_saldo(stub, "A")
            assert saldo_setelah_validasi == 1000.0, (
                f"request_id tidak valid mengubah saldo A: {saldo_setelah_validasi}"
            )
            print()

            print("--- 20 transfer dengan request_id unik ---")
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

        print("\n--- Hasil ---")
        print(f"Saldo A : {saldo_a:.0f} (diharapkan: 800)")
        print(f"Saldo B : {saldo_b:.0f} (diharapkan: 700)")
        print(f"Total   : {saldo_a + saldo_b:.0f} (diharapkan: 1500)")
        print(f"Dedup cache: {servicer.dedup_cache_size} entries")

        assert saldo_a == 800.0, f"Saldo A salah: {saldo_a}"
        assert saldo_b == 700.0, f"Saldo B salah: {saldo_b}"
        assert saldo_a + saldo_b == 1500.0, f"Total salah: {saldo_a + saldo_b}"
        assert servicer.dedup_cache_size == NUM_TRANSFERS, (
            f"Dedup cache seharusnya {NUM_TRANSFERS} entri, "
            f"aktual {servicer.dedup_cache_size}."
        )

        print("\n[OK] LULUS: Saldo total tetap 1500, A berkurang tepat 200.")
        print("[OK] request_id kosong/spasi ditolak tanpa mengubah saldo.")

    finally:
        server.stop(grace=0)
        print("Server dihentikan.")


if __name__ == "__main__":
    main()
