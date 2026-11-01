"""Praktikum RPC - Komputasi Paralel dan Terdistribusi

Nama : Muhammad Fadhlan Aminullah
NPM  : 247006111151

Demonstrasi failover dua server dan batas deduplikasi in-memory (L3.5).

Membuktikan:
1. Dua server berjalan: primary di 50081 dan backup di 50082.
2. Saat primary dimatikan, client otomatis failover ke backup tanpa crash.
3. State kedua server tidak direplikasi: request yang sudah dieksekusi di primary
   akan dieksekusi LAGI di backup bila dikirim dengan request_id yang sama.
4. Deduplikasi bersifat per-server: pengulangan di server yang sama menghasilkan
   respons cache yang identik.
5. Restart server menghapus cache in-memory; retry dengan request_id yang sama
   setelah restart mengeksekusi transfer lagi meskipun saldo dipulihkan.

Catatan penting: skenario ini membuktikan bahwa sistem TIDAK memberikan
exactly-once lintas server atau lintas restart. Yang tersedia hanya
at-most-once selama cache server yang sama masih hidup.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import grpc
import bank_pb2 as pb
import bank_pb2_grpc as pb_grpc
from server_transfer import build_server
from client_transfer import FailoverBankClient

PORT_PRIMARY = 50081
PORT_BACKUP = 50082
SHARED_REQUEST_ID = "tx-shared-001"
TRANSFER_AMOUNT = 50.0


def assert_empty_request_id_rejected(stub: pb_grpc.LayananBankStub) -> None:
    for bad_id in ("", "   "):
        try:
            stub.Transfer(
                pb.TransferRequest(
                    request_id=bad_id,
                    pengirim="A",
                    penerima="B",
                    jumlah=TRANSFER_AMOUNT,
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
            raise AssertionError(f"request_id {bad_id!r} diterima, seharusnya ditolak.")


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

    tampilkan_header("PRAKTIKUM 3.5 - PENGUJIAN FAILOVER ANTARSERVER (PENGAYAAN)", "Test")
    print("=== L3.5: Failover Dua Server & Batas Deduplikasi (client_failover) ===\n")

    server_primary, servicer_primary = build_server(
        port=PORT_PRIMARY, balances={"A": 1000.0, "B": 500.0}
    )
    server_backup, servicer_backup = build_server(
        port=PORT_BACKUP, balances={"A": 1000.0, "B": 500.0}
    )
    restarted_server = None

    server_primary.start()
    server_backup.start()
    print(f"[STATUS] Primary aktif di 127.0.0.1:{PORT_PRIMARY}")
    print(f"[STATUS] Backup  aktif di 127.0.0.1:{PORT_BACKUP}\n")

    try:
        endpoints = [f"127.0.0.1:{PORT_PRIMARY}", f"127.0.0.1:{PORT_BACKUP}"]
        client = FailoverBankClient(endpoints=endpoints)

        # -------------------------------------------------------------
        # Tahap 0: validasi request_id kosong
        # -------------------------------------------------------------
        print("--- Tahap 0: Validasi request_id ---")
        with grpc.insecure_channel(f"127.0.0.1:{PORT_PRIMARY}") as channel:
            stub_primary = pb_grpc.LayananBankStub(channel)
            assert_empty_request_id_rejected(stub_primary)
        print("  Saldo tidak berubah setelah request tidak valid.\n")

        # -------------------------------------------------------------
        # Tahap 1: request ke primary, state hanya berubah di primary
        # -------------------------------------------------------------
        print("--- Tahap 1: Transfer ke Primary ---")
        res1 = client.transfer(SHARED_REQUEST_ID, "A", "B", TRANSFER_AMOUNT)
        print(f"  Hasil: {res1.pesan}")
        print(f"  Endpoint aktif: {client.current_endpoint}")
        print(f"  Saldo primary : {servicer_primary.balances}")
        print(f"  Saldo backup  : {servicer_backup.balances}")

        assert client.current_endpoint == endpoints[0], "Seharusnya masih di primary."
        assert servicer_primary.balances == {"A": 950.0, "B": 550.0}, (
            f"Saldo primary salah: {servicer_primary.balances}"
        )
        assert servicer_backup.balances == {"A": 1000.0, "B": 500.0}, (
            f"Backup tidak boleh ikut berubah: {servicer_backup.balances}"
        )
        print("  -> [OK] Hanya primary yang mengeksekusi; state tidak direplikasi.\n")

        # -------------------------------------------------------------
        # Tahap 2: primary mati, failover dengan request_id yang SAMA
        # -------------------------------------------------------------
        print("--- Tahap 2: Primary Mati, Failover dengan ID SAMA ---")
        print(f"  Mematikan primary (port {PORT_PRIMARY})...")
        server_primary.stop(grace=0)
        print("  Primary berhenti.")

        res2 = client.transfer(SHARED_REQUEST_ID, "A", "B", TRANSFER_AMOUNT)
        print(f"  Hasil setelah failover: {res2.pesan}")
        print(f"  Endpoint aktif: {client.current_endpoint}")
        print(f"  Saldo backup  : {servicer_backup.balances}")

        assert client.current_endpoint == endpoints[1], "Seharusnya failover ke backup."
        assert res2.sukses, "Transfer di backup gagal."
        assert servicer_backup.balances == {"A": 950.0, "B": 550.0}, (
            f"Backup seharusnya mengeksekusi transfer: {servicer_backup.balances}"
        )
        print("  -> [BUKTI] ID yang sama dieksekusi LAGI di backup karena cache")
        print("     primary tidak ikut pindah. Ini adalah double execution lintas server.\n")

        # -------------------------------------------------------------
        # Tahap 3: deduplikasi per-server di backup
        # -------------------------------------------------------------
        print("--- Tahap 3: Pengulangan ID SAMA di Backup (Dedup Per-Server) ---")
        res3 = client.transfer(SHARED_REQUEST_ID, "A", "B", TRANSFER_AMOUNT)
        print(f"  Hasil: {res3.pesan}")
        print(f"  Saldo backup  : {servicer_backup.balances}")
        print(f"  Cache entries : {servicer_backup.dedup_cache_size}")

        assert res3 == res2, "Respons cache harus identik dengan respons eksekusi pertama."
        assert servicer_backup.balances == {"A": 950.0, "B": 550.0}, (
            f"Retry di server yang sama tidak boleh mengubah saldo: {servicer_backup.balances}"
        )
        assert servicer_backup.dedup_cache_size == 1, (
            f"Cache seharusnya 1 entri, aktual: {servicer_backup.dedup_cache_size}"
        )
        print("  -> [OK] Deduplikasi bekerja selama cache server yang sama masih hidup.\n")

        # -------------------------------------------------------------
        # Tahap 4: restart backup, cache hilang, retry mengeksekusi ulang
        # -------------------------------------------------------------
        print("--- Tahap 4: Restart Backup & Pembuktian Cache Hilang ---")
        balances_before_restart = servicer_backup.balances
        print(f"  Saldo sebelum restart: {balances_before_restart}")
        print(f"  Cache sebelum restart: {servicer_backup.dedup_cache_size} entri")

        server_backup.stop(grace=0)
        restarted_server, restarted_servicer = build_server(
            port=PORT_BACKUP,
            balances=balances_before_restart,
        )
        restarted_server.start()
        print(f"  Saldo setelah restart: {restarted_servicer.balances} (dipulihkan manual)")
        print(f"  Cache setelah restart: {restarted_servicer.dedup_cache_size} entri")

        assert restarted_servicer.dedup_cache_size == 0, "Cache seharusnya kosong setelah restart."
        assert restarted_servicer.balances == balances_before_restart, (
            "Skenario ini sengaja memulihkan saldo agar efek cache hilang terisolasi."
        )

        with grpc.insecure_channel(f"127.0.0.1:{PORT_BACKUP}") as channel:
            stub_restarted = pb_grpc.LayananBankStub(channel)
            res4 = stub_restarted.Transfer(
                pb.TransferRequest(
                    request_id=SHARED_REQUEST_ID,
                    pengirim="A",
                    penerima="B",
                    jumlah=TRANSFER_AMOUNT,
                ),
                timeout=3.0,
            )

        print(f"  Hasil retry setelah restart: {res4.pesan}")
        print(f"  Saldo akhir: {restarted_servicer.balances}")
        print(f"  Cache akhir: {restarted_servicer.dedup_cache_size} entri")

        assert res4.sukses, "Retry setelah restart gagal."
        assert restarted_servicer.balances == {"A": 900.0, "B": 600.0}, (
            f"Retry setelah restart seharusnya mengeksekusi lagi: "
            f"{restarted_servicer.balances}"
        )
        assert restarted_servicer.dedup_cache_size == 1, (
            f"Cache seharusnya berisi 1 entri baru, aktual: {restarted_servicer.dedup_cache_size}"
        )
        print("  -> [BUKTI] Cache in-memory hilang saat restart; retry dengan ID yang")
        print("     sama mengeksekusi transfer lagi (A berkurang 50 untuk kedua kalinya).\n")

        print("=== Kesimpulan & Rekomendasi ===")
        print("- Failover memindahkan request ke server lain, tetapi tidak mereplikasi")
        print("  saldo maupun cache deduplikasi.")
        print("- Deduplikasi in-memory hanya memberi at-most-once selama proses server")
        print("  yang sama hidup; tidak ada jaminan exactly-once lintas server/restart.")
        print("- Untuk kebutuhan produksi, gunakan penyimpanan transaksi persisten dengan")
        print("  unique constraint pada request_id (mis. PostgreSQL/SQLite), WAL, atau")
        print("  cache terdistribusi dengan persistence (mis. Redis AOF).")
        print("- Jika konsistensi lintas server diperlukan, state dan cache harus")
        print("  direplikasi atau dipusatkan pada satu penyimpanan bersama.\n")

        print("[OK] L3.5 TERVALIDASI: failover, dedup per-server, dan kehilangan cache")
        print("     saat restart dibuktikan dengan state nyata.")

    finally:
        server_primary.stop(grace=0)
        if restarted_server is not None:
            restarted_server.stop(grace=0)
        else:
            server_backup.stop(grace=0)
        print("Semua server dimatikan.")


if __name__ == "__main__":
    main()
