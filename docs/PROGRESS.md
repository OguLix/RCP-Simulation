# Progres Pengerjaan Praktikum RPC - Bagian Individu

## Status saat ini

- Terakhir diperbarui: 31 Oktober 2026, 15:15 Asia/Jakarta.
- Tahap aktif: **Praktikum 1, Praktikum 2, dan Praktikum 3 SELURUHNYA SELESAI, TERSTANDARISASI, DAN TERVALIDASI**.
- Status audit: Penamaan file telah diseragamkan mengikuti pola deskriptif Praktikum 1 & 2 (tanpa awalan `test_l3_*.py`). Pengukuran L3.4 telah diselaraskan dengan parameter modul resmi dosen (`time.sleep(0.1)`).

## Checklist aktual

| Area | Status | Keterangan |
| --- | --- | --- |
| Panduan kerja | Selesai dan tervalidasi | `AGENTS.md` telah dipatuhi penuh. |
| Rencana/checklist | Selesai dan tervalidasi | `docs/PLAN.md` telah dipenuhi seluruhnya. |
| Struktur kode | Selesai | `praktikum1/`, `praktikum2/`, dan `praktikum3/` konsisten, mandiri, dan bersih. |
| Praktikum 1 | **Selesai dan tervalidasi** | L1.1-L1.3, L1.5 tervalidasi; L1.4 benchmark lokal tervalidasi; analisis payload XML dan overhead format selesai. |
| Praktikum 2 | **Selesai dan tervalidasi** | Seluruh butir L2.1-L2.5 diimplementasikan dan divalidasi. |
| Praktikum 3 | **Selesai dan tervalidasi** | Seluruh butir L3.1-L3.5 tervalidasi dengan nama file standar (`verify_transfer`, `simulate_double_transfer`, `simulate_race_condition`, `benchmark_workers`, `client_failover`). |

## Validasi Terakhir (Praktikum 3 Terstandarisasi)

### L3.1 - Verifikasi 20 Transfer Berulang (`verify_transfer.py`)
- 20 transfer sekuensial @ Rp10 dari A ke B dengan deduplikasi.
- Saldo akhir terverifikasi akurat: A = 800, B = 700, Total = 1500 (A berkurang tepat 200).

### L3.2 - Dampak UUID Baru vs UUID Tetap (`simulate_double_transfer.py`)
- Retry dengan ID sama (idempoten): saldo A berkurang 1x (1000 -> 900).
- Retry dengan ID baru (bug client): saldo A berkurang 2x (900 -> 700) akibat server menganggapnya dua transaksi berbeda.

### L3.3 - Uji Concurrency 50 Transfer (`simulate_race_condition.py`)
- 10 thread client mengirim 5 transfer bersamaan (total 50 transfer = Rp500).
  - **Dengan Lock:** Konsistensi data 100% sempurna (A=500, B=1000, Total=1500).
  - **Tanpa Lock:** Terbukti terjadi *Lost Update* (A=880, B=620; penyimpangan saldo Rp380 akibat race condition read-modify-write).

### L3.4 - Benchmark Concurrency GetMahasiswa (`benchmark_workers.py`)
- Pengukuran performa server sesuai modul resmi (`time.sleep(0.1)` di server, 200 request, 20 client):
  - 1 worker: Waktu 20.32 s, Throughput 9.8 req/s, Latensi rata-rata 1932.6 ms.
  - 4 workers: Waktu 5.07 s, Throughput 39.5 req/s (4.0x speedup), Latensi rata-rata 485.7 ms.
  - 10 workers: Waktu 2.05 s, Throughput 97.5 req/s (9.9x speedup), Latensi rata-rata 198.9 ms.
- Grafik visualisasi performa tersimpan di `docs/reports/l3_4_throughput_latency.png`.

### L3.5 - Failover Dua Server & Analisis Deduplikasi (`client_failover.py`)
- Server Primary (port 50081) dan Backup (port 50082).
- Saat Primary dimatikan paksa, client otomatis beralih ke Server Backup tanpa error.
- Demonstrasi dampak restart server: membuktikan hilangnya cache in-memory pasca crash/restart sehingga request lama diproses ulang; menyertakan rekomendasi persistensi (WAL/PostgreSQL/Redis).

## File Standar Praktikum 3

- `praktikum3/bank.proto` (Kontrak RPC Transfer, Saldo, dan deduplikasi)
- `praktikum3/bank_pb2.py` & `praktikum3/bank_pb2_grpc.py` (Kompilasi stub gRPC)
- `praktikum3/server_transfer.py` (Server bank dengan locking, simulated delay, timeout simulation, dan dedup cache)
- `praktikum3/client_transfer.py` (Client transfer lengkap dengan CLI arguments, retry exponential backoff & FailoverBankClient)
- `praktikum3/verify_transfer.py` (Verifikasi 20 transfer berulang L3.1)
- `praktikum3/simulate_double_transfer.py` (Simulasi transfer ganda vs idempotensi L3.2)
- `praktikum3/simulate_race_condition.py` (Simulasi race condition lock vs no-lock L3.3)
- `praktikum3/benchmark_workers.py` (Benchmark 200 req / 20 client, sleep=0.1s, worker 1/4/10 + grafik L3.4)
- `praktikum3/client_failover.py` (Failover 2 server dan pembuktian kerentanan restart L3.5)
- `docs/reports/praktikum3-validation.md` (Laporan validasi komprehensif)
- `docs/runbooks/praktikum3.md` (Panduan eksekusi manual dan otomatis)
- `docs/reports/l3_4_throughput_latency.png` (Grafik throughput dan latensi)
