"""Demonstrasi Failover dua server gRPC dan Analisis Deduplikasi Pasca-Restart (L3.5).

Membuktikan:
1. Dua server berjalan (Server 1 Utama di 50051/50081, Server 2 Cadangan di 50052/50082).
2. Ketika Server 1 dimatikan mendadak, client otomatis melakukan failover ke Server 2 tanpa crash.
3. Analisis dampak restart server terhadap deduplikasi in-memory dan pembuktian hilangnya cache.
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
from client_transfer import FailoverBankClient

PORT_PRIMARY = 50081
PORT_BACKUP = 50082


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=== L3.5: Failover Dua Server & Analisis Deduplikasi (client_failover) ===\n")

    # 1. Start Server 1 (Primary) dan Server 2 (Backup)
    server_primary, servicer_primary = build_server(port=PORT_PRIMARY, balances={"A": 1000.0, "B": 500.0})
    server_backup, servicer_backup = build_server(port=PORT_BACKUP, balances={"A": 1000.0, "B": 500.0})

    server_primary.start()
    server_backup.start()
    print(f"[STATUS] Server 1 (Primary) aktif di 127.0.0.1:{PORT_PRIMARY}")
    print(f"[STATUS] Server 2 (Backup)  aktif di 127.0.0.1:{PORT_BACKUP}\n")

    try:
        endpoints = [f"127.0.0.1:{PORT_PRIMARY}", f"127.0.0.1:{PORT_BACKUP}"]
        client = FailoverBankClient(endpoints=endpoints)

        # -------------------------------------------------------------
        # Tahap 1: Request ke Server Utama saat kondisi normal
        # -------------------------------------------------------------
        print("--- Tahap 1: Operasi Normal ke Server Utama ---")
        tx1_id = str(uuid.uuid4())
        res1 = client.transfer(tx1_id, "A", "B", 50.0)
        print(f"Hasil transfer 1: {res1.pesan}")
        print(f"Endpoint aktif sekarang: {client.current_endpoint}")
        assert client.current_endpoint == endpoints[0], "Seharusnya masih di primary server"
        print("-> [OK] Server Utama berhasil melayani request.\n")

        # -------------------------------------------------------------
        # Tahap 2: Simulasi Server Utama Mati (Failover)
        # -------------------------------------------------------------
        print("--- Tahap 2: Server Utama Mati & Pengujian Failover Otomatis ---")
        print(f"Mematikan Server 1 (port {PORT_PRIMARY}) secara paksa...")
        server_primary.stop(grace=0)
        print("Server 1 telah berhenti.")

        tx2_id = str(uuid.uuid4())
        print(f"Client mengirim transfer baru (ID: {tx2_id[:8]}...)...")
        res2 = client.transfer(tx2_id, "A", "B", 100.0)
        print(f"Hasil transfer 2: {res2.pesan}")
        print(f"Endpoint aktif sekarang: {client.current_endpoint}")
        assert client.current_endpoint == endpoints[1], "Seharusnya telah failover ke backup server"
        print("-> [OK] Failover berhasil! Client otomatis beralih ke Server 2 dan transaksi sukses.\n")

        # -------------------------------------------------------------
        # Tahap 3: Analisis Kerentanan Deduplikasi In-Memory Pasca-Restart
        # -------------------------------------------------------------
        print("--- Tahap 3: Demonstrasi Dampak Restart Server terhadap Deduplikasi In-Memory ---")
        # Simpan transaksi pada server 2
        id_restart_demo = "tx-restart-999"
        res3 = client.transfer(id_restart_demo, "A", "B", 50.0)
        print(f"Transfer awal dikirim ke Server 2: {res3.pesan} (Saldo A: {res3.saldo_pengirim:.0f})")
        print(f"Ukuran dedup_cache server 2 saat ini: {servicer_backup.dedup_cache_size} entri.")

        print("\n[SIMULASI RESTART] Server 2 mengalami crash dan direstart ulang...")
        server_backup.stop(grace=0)

        # Server 2 restart (proses baru / memori baru)
        restarted_server, restarted_servicer = build_server(port=PORT_BACKUP, balances={"A": 850.0, "B": 650.0})
        restarted_server.start()
        print(f"Server 2 berhasil restart. Ukuran dedup_cache pasca-restart: {restarted_servicer.dedup_cache_size} entri (KOSONG!).")

        print("\nClient melakukan retry dengan request_id yang SAMA ('tx-restart-999')...")
        channel_restarted = grpc.insecure_channel(f"127.0.0.1:{PORT_BACKUP}")
        stub_restarted = pb_grpc.LayananBankStub(channel_restarted)

        # Resend same request
        res_after_restart = stub_restarted.Transfer(
            pb.TransferRequest(
                request_id=id_restart_demo,
                pengirim="A",
                penerima="B",
                jumlah=50.0,
            )
        )
        print(f"Hasil setelah restart: {res_after_restart.pesan}")
        print(f"Saldo A setelah restart retry: {res_after_restart.saldo_pengirim:.0f}")

        # Karena cache hilang di memory, transaksi dieksekusi lagi!
        assert res_after_restart.saldo_pengirim == 800.0, "Saldo berkurang lagi karena dedup cache hilang saat restart"
        print("-> [TERBUKTI] Dampak Restart: Deduplikasi in-memory HILANG sehingga retry memicu transaksi ganda!\n")

        print("=== Rekomendasi Solusi Penyimpanan Persisten ===")
        print("1. WAL (Write-Ahead Logging) atau Database ACID (PostgreSQL / SQLite).")
        print("2. Distribusi Cache Persisten seperti Redis dengan AOF (Append-Only File) persistence.")
        print("3. Pencatatan transaksi dalam tabel 'processed_transactions' dengan unique constraint pada 'request_id'.")

        restarted_server.stop(grace=0)
        channel_restarted.close()

    finally:
        server_primary.stop(grace=0)
        server_backup.stop(grace=0)
        print("\nSemua server dimatikan.")

    print("\n[OK] L3.5 TERVALIDASI: Failover dan analisis ketahanan restart selesai.")


if __name__ == "__main__":
    main()
