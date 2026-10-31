# Progres Pengerjaan Praktikum RPC - Bagian Individu

## Status saat ini

- Terakhir diperbarui: 31 Oktober 2026, 16:25 Asia/Jakarta.
- Tahap aktif: **Praktikum 1, Praktikum 2, dan Praktikum 3 SELURUHNYA SELESAI DAN TERVALIDASI**.
- Status audit: komentar kode telah dibersihkan dari rujukan praktikum/modul/dosen tanpa mengubah perilaku program. Dokumentasi dirapikan: seluruh instruksi dipusatkan di README root, sedangkan README per praktikum dan `docs/runbooks/` dihapus.

## Checklist aktual

| Area | Status | Keterangan |
| --- | --- | --- |
| Panduan kerja | Selesai dan tervalidasi | `AGENTS.md` dipatuhi; struktur folder pada panduan sudah disesuaikan. |
| Rencana/checklist | Selesai dan tervalidasi | `docs/PLAN.md` telah dipenuhi seluruhnya. |
| Struktur kode | Selesai | `praktikum1/`, `praktikum2/`, dan `praktikum3/` konsisten dan mandiri. |
| Dokumentasi | Selesai | README root tunggal; README per praktikum dan runbook lama dihapus. |
| Praktikum 1 | **Selesai dan tervalidasi** | L1.1-L1.5, benchmark lokal, analisis payload XML, dan overhead format selesai. |
| Praktikum 2 | **Selesai dan tervalidasi** | Seluruh butir L2.1-L2.5 diimplementasikan dan divalidasi. |
| Praktikum 3 | **Selesai dan tervalidasi** | Seluruh butir L3.1-L3.5 tervalidasi. |

## Validasi terakhir (Praktikum 3)

### L3.1 - Verifikasi 20 Transfer Berulang (`verify_transfer.py`)

- 20 transfer sekuensial @ Rp10 dari A ke B dengan deduplikasi.
- Saldo akhir terverifikasi akurat: A = 800, B = 700, Total = 1500 (A berkurang tepat 200).

### L3.2 - Dampak UUID Baru vs UUID Tetap (`simulate_double_transfer.py`)

- Retry dengan ID sama (idempoten): saldo A berkurang 1x (1000 -> 900).
- Retry dengan ID baru (bug client): saldo A berkurang 2x (900 -> 700) karena server menganggapnya dua transaksi berbeda.

### L3.3 - Uji Concurrency 50 Transfer (`simulate_race_condition.py`)

- 10 thread client mengirim 5 transfer bersamaan (total 50 transfer = Rp500).
  - **Dengan Lock:** konsistensi data 100% (A=500, B=1000, Total=1500).
  - **Tanpa Lock:** terbukti terjadi *lost update* (contoh run: A=880, B=620; distribusi saldo rusak akibat race condition read-modify-write). Nilai dapat berbeda tiap run.

### L3.4 - Benchmark Concurrency GetMahasiswa (`benchmark_workers.py`)

- 200 request, 20 client, `time.sleep(0.1)` di server, variasi worker 1/4/10:
  - 1 worker: waktu 20.32 s, throughput 9.8 req/s, latensi rata-rata 1932.6 ms.
  - 4 workers: waktu 5.07 s, throughput 39.5 req/s (4.0x speedup), latensi rata-rata 485.7 ms.
  - 10 workers: waktu 2.05 s, throughput 97.5 req/s (9.9x speedup), latensi rata-rata 198.9 ms.
- Grafik tersimpan di `docs/reports/l3_4_throughput_latency.png`.

### L3.5 - Failover Dua Server & Analisis Deduplikasi (`client_failover.py`)

- Primary (port 50081) dan backup (port 50082).
- Saat primary dimatikan paksa, client otomatis beralih ke backup tanpa error.
- Restart server membuktikan cache in-memory hilang sehingga request lama diproses ulang; rekomendasi persistensi: WAL/PostgreSQL/SQLite, Redis AOF, atau outbox/event log.

## Audit dokumentasi dan komentar (31 Oktober 2026)

- Rujukan "Praktikum N", "sesuai modul praktikum", "sesuai modul dosen", "halaman 11", dan "sesuai format modul dosen" dihapus dari komentar, docstring, help argparse, dan banner tabel.
- Label butir `L1.x`-`L3.x` dipertahankan sebagai penanda fungsi.
- Teks keluaran program tidak diubah agar bukti validasi yang sudah ada tetap cocok.
- File generated (`*_pb2.py`, `*_pb2_grpc.py`) dan `old_stubs/` tidak disentuh.
- README root ditulis ulang dan menjadi satu-satunya panduan eksekusi; README per praktikum dihapus.
- `docs/runbooks/praktikum1.md`, `praktikum2.md`, dan `praktikum3.md` dihapus; seluruh perintah, opsi CLI, port, dan hasil yang diharapkan dipindahkan ke README root.
- `.gitignore` ditambahkan untuk `.venv/`, `__pycache__/`, file `.pyc`, dan artefak lokal lain.
- `numpy` dicatat eksplisit di `requirements.txt` karena `benchmark_workers.py` mengimpornya langsung.

## Verifikasi pasca-audit (31 Oktober 2026)

- `py_compile` 17 file Python non-generated: **OK**.
- Unit test Praktikum 1: **5 test lulus**.
- `verify_transfer.py`: **LULUS** - A=800, B=700, total 1500, dedup 20 entri.
- `simulate_double_transfer.py`: **LULUS** - ID sama A=900; ID baru A=700.
- `simulate_race_condition.py`: **LULUS** - dengan lock A=500/B=1000; tanpa lock A=780/B=720 (lost update, nilai berbeda dari run sebelumnya sehingga mengonfirmasi sifat non-deterministik).
- `compare_message_size.py`: keluaran tetap 37/432, 37/396, 4/190, dan 93/911 byte.

## File standar

### Root

- `README.md` (ringkasan, setup, peta butir, port, hasil ukur, troubleshooting)
- `requirements.txt`
- `.gitignore`

### Praktikum 1

- `praktikum1/calculator_service.py`
- `praktikum1/server_calculator.py`
- `praktikum1/client_calculator.py`
- `praktikum1/benchmark_latency.py`
- `praktikum1/test_calculator_service.py`

### Praktikum 2

- `praktikum2/akademik.proto`
- `praktikum2/akademik_pb2.py` & `akademik_pb2_grpc.py`
- `praktikum2/server_grpc.py`
- `praktikum2/client_grpc.py`
- `praktikum2/client_async.py`
- `praktikum2/compare_message_size.py`
- `praktikum2/test_backward_compat.py`
- `praktikum2/old_stubs/`

### Praktikum 3

- `praktikum3/bank.proto`
- `praktikum3/bank_pb2.py` & `bank_pb2_grpc.py`
- `praktikum3/server_transfer.py`
- `praktikum3/client_transfer.py`
- `praktikum3/verify_transfer.py`
- `praktikum3/simulate_double_transfer.py`
- `praktikum3/simulate_race_condition.py`
- `praktikum3/benchmark_workers.py`
- `praktikum3/client_failover.py`

### Bukti

- `docs/reports/praktikum1-validation.md`
- `docs/reports/praktikum2-validation.md`
- `docs/reports/praktikum2-foundation-validation.md`
- `docs/reports/praktikum3-validation.md`
- `docs/reports/l3_4_throughput_latency.png`

## Risiko dan catatan teknis

1. **Timeout simulation memegang lock** - `server_transfer.py` menunda respons 3 detik di dalam critical section saat `--simulate-timeout-prob` aktif, sehingga RPC lain ikut menunggu. Tidak dipakai pada skrip validasi L3.1-L3.5, tetapi perlu dipindahkan ke luar lock bila fitur ini dipakai.
2. **Import tak terpakai** - `verify_transfer.py` masih mengimpor `bank_pb2 as pb` tanpa pemakaian. Tidak memengaruhi hasil.
3. **Ketergantungan lintas praktikum** - `benchmark_workers.py` memakai `LayananNilai` dari `../praktikum2`. Disengaja agar data akademik konsisten, tetapi membuat Praktikum 3 tidak sepenuhnya mandiri.
4. **Deduplikasi in-memory** - cache `request_id` hilang saat restart. Rekomendasi persistensi sudah dicatat di README root dan laporan validasi.
5. **Hasil L3.3 tanpa lock tidak deterministik** - besar penyimpangan bergantung pada interleaving thread.

## Langkah berikutnya

1. Tidak ada blocker untuk pelaporan; seluruh butir selesai dan bukti tersedia.
2. Opsional: pindahkan `time.sleep(3.0)` simulasi timeout ke luar lock pada `server_transfer.py`, lalu ulangi L3.1 dan L3.5.
3. Opsional: hapus import tak terpakai di `verify_transfer.py` dan jalankan ulang skrip tersebut.
