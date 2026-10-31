# Progres Pengerjaan Praktikum RPC - Bagian Individu

## Status saat ini

- Terakhir diperbarui: 31 Oktober 2026, 17:01 Asia/Jakarta.
- Tahap aktif: perbaikan evaluasi selesai untuk L1.4, L2.4, L2.5, L3.1, L3.2, L3.3, L3.4, dan L3.5.
- Status keseluruhan: seluruh butir L1.1-L1.5, L2.1-L2.5, dan L3.1-L3.5 sudah diimplementasikan. Semua pengujian yang dapat dijalankan ulang pada mesin ini lulus. **L1.4 lintas komputer belum dilakukan** dan tetap ditandai belum selesai untuk bagian tersebut.

## Checklist aktual

| Area | Status | Keterangan |
| --- | --- | --- |
| Panduan kerja | Selesai dan tervalidasi | `AGENTS.md` dipatuhi; tidak ada commit/push; perubahan hanya di working tree. |
| Rencana/checklist | Selesai dan tervalidasi | `docs/PLAN.md` diperbarui sesuai status L1.4. |
| Struktur kode | Selesai | `praktikum1/`, `praktikum2/`, dan `praktikum3/` konsisten dan mandiri. |
| Dokumentasi | Selesai | README root tunggal; hasil ukur dan batasan diperbarui. |
| Praktikum 1 | **Selesai dan tervalidasi (localhost)** | L1.1-L1.3, L1.5, benchmark lokal, dan analisis payload tervalidasi. L1.4 lintas komputer **belum**. |
| Praktikum 2 | **Selesai dan tervalidasi** | L2.1-L2.5 diimplementasikan; L2.3, L2.4, dan L2.5 dijalankan ulang. |
| Praktikum 3 | **Selesai dan tervalidasi** | L3.1-L3.5 dijalankan ulang dengan hasil aktual. |

## Validasi terbaru (setelah perbaikan evaluasi)

Lingkungan: Windows 11 64-bit, Python 3.14.7, `.venv`, `127.0.0.1`.

### Praktikum 1

- `py_compile`: seluruh file yang diubah berhasil dikompilasi.
- Unit test: **5 test lulus** (`python -m unittest -v test_calculator_service.py` dari `praktikum1/`).
- L1.4, 100 sampel + 10 pemanasan, server port 8000:
  - Lokal: total 0.0311 ms, rata-rata 0.0003 ms, median 0.0003 ms, stdev 0.0001 ms.
  - XML-RPC: total 170.9735 ms, rata-rata 1.7097 ms, median 1.6215 ms, stdev 0.3110 ms.
  - Rasio sekitar 5497x; hanya berlaku di localhost dan dekat resolusi timer.
  - **Uji lintas komputer belum dilakukan.**
- L1.5: tanpa server, client `--expect-offline` menangkap `WinError 10061` dan tidak crash.

### Praktikum 2

- L2.4 (payload, bukan paket jaringan):
  - GetMahasiswa response: 37 byte Protobuf vs 432 byte XML-RPC (11.7x).
  - TambahNilai request: 37 vs 396 byte (10.7x).
  - `tambah(5, 3)`: 4 byte ilustrasi varint vs 190 byte (47.5x).
  - 4 pesan `Nilai` vs 4 respons XML-RPC terpisah: 93 vs 1145 byte (12.3x).
  - Header HTTP dan framing HTTP/2 tidak dihitung.
- L2.5, 10 request future, server port 50051:
  - 9 sukses, 1 gagal `NOT_FOUND`.
  - Wall-clock 14.6 ms; fase submit 5.8 ms.
  - Latency individual: min 4.3 / mean 8.4 / median 9.1 / p95 12.1 / max 12.1 ms.
  - Throughput 683.9 request/detik; concurrency factor 5.71x.
  - Concurrency factor dijelaskan sebagai indikator overlap, bukan jumlah thread aktif.
- L2.3 dijalankan ulang: stub lama berhasil memanggil server baru; field `prodi` diabaikan aman.

### Praktikum 3

- L3.1 `verify_transfer.py`: **LULUS**. A=800, B=700, total=1500, cache 20 entri. `request_id` kosong dan spasi ditolak `INVALID_ARGUMENT` tanpa mengubah saldo.
- L3.2 `simulate_double_transfer.py`: **LULUS**.
  - ID sama: respons pertama dan retry identik; A=900, B=600; cache 1 entri.
  - ID baru: A=700, B=800 (transfer ganda).
  - Timeout + retry ID sama: A=900, B=600; cache 1 entri; total 0.71 s termasuk retry.
- L3.3 `simulate_race_condition.py`: **LULUS**, 3 ronde masing-masing mode.
  - Dengan lock: A=500, B=1000, total=1500 pada ketiga ronde.
  - Tanpa lock + `threading.Barrier(10)`: A=950, B=550, total=1500 pada ketiga ronde. Lost update terkontrol dan dapat diulang.
  - Barrier adalah hook pengujian, bukan mekanisme produksi.
- L3.4 `benchmark_workers.py`: **LULUS**.
  - 1 worker: 20.45 s, 9.8 req/s, mean 1944.2 ms, P95 2053.6 ms, P99 2058.0 ms.
  - 4 worker: 5.13 s, 39.0 req/s, mean 491.0 ms, P95 540.3 ms, P99 545.4 ms.
  - 10 worker: 2.12 s, 94.5 req/s, mean 203.4 ms, P95 221.1 ms, P99 225.1 ms.
  - Persentil memakai nearest-rank `ceil(p*n)-1`.
- L3.5 `client_failover.py`: **LULUS**.
  - Primary mengeksekusi `tx-shared-001`: A=950/B=550; backup tetap A=1000/B=500.
  - Setelah primary mati, failover ke backup dengan ID sama mengeksekusi lagi: backup A=950/B=550 (mulai dari 1000 lalu menjalankan satu transfer 50; kebetulan sama dengan primary, bukan replikasi state). Ini double execution lintas server.
  - Pengulangan ID sama di backup: respons identik, saldo tetap, cache 1 entri.
  - Restart backup dengan saldo dipulihkan A=950/B=550: cache 0 entri; retry ID sama mengeksekusi lagi menjadi A=900/B=600.
  - Tidak ada klaim exactly-once lintas server/restart.

## Validasi yang tidak dijalankan ulang

- L2.1 client streaming dan L2.2 bidirectional streaming: kode tidak diubah pada perbaikan ini; hasil validasi sebelumnya tetap berlaku.
- Pengujian L1.4 pada dua komputer fisik: belum pernah dilakukan.

## File yang ditambah/diubah pada perbaikan ini

- `praktikum1/benchmark_latency.py` - pemanasan, median/stdev, presisi output, catatan localhost.
- `praktikum2/compare_message_size.py` - payload setara, per-message comparison, penjelasan framing.
- `praktikum2/client_async.py` - latency individual via callback, wall-clock, throughput, concurrency factor.
- `praktikum3/server_transfer.py` - validasi `request_id`, timeout di luar lock, hook barrier untuk pengujian race.
- `praktikum3/verify_transfer.py` - validasi `request_id` kosong/spasi.
- `praktikum3/simulate_double_transfer.py` - respons identik, skenario timeout + retry.
- `praktikum3/simulate_race_condition.py` - 3 ronde lock/no-lock dengan barrier terkontrol.
- `praktikum3/benchmark_workers.py` - percentile nearest-rank, P99, grafik tiga seri.
- `praktikum3/client_failover.py` - skenario state divergence, double execution, dedup per-server, restart.
- `README.md`, `docs/PLAN.md`, `docs/PROGRESS.md`, `docs/reports/praktikum1-validation.md`, `docs/reports/praktikum2-validation.md`, `docs/reports/praktikum3-validation.md`.
- Grafik `praktikum3/l3_4_throughput_latency.png` dan `docs/reports/l3_4_throughput_latency.png` diperbarui.

## Risiko dan catatan teknis

1. **L1.4 lintas komputer belum dilakukan** - hasil yang ada hanya localhost. Jangan menafsirkan rasio 5497x sebagai biaya jaringan.
2. **L3.3 memakai hook pengujian** - barrier sengaja ditambahkan untuk reproduksi terkontrol. Tanpa barrier, penyimpangan tetap mungkin terjadi tetapi besarnya bergantung pada penjadwalan.
3. **Deduplikasi hanya per-server dan in-memory** - L3.5 membuktikan double execution lintas server dan setelah restart. Sistem tidak memberikan exactly-once.
4. **L3.4 bergantung pada mesin uji** - beban adalah I/O-bound buatan (`time.sleep(0.1)`); hasil bukan batas universal.
5. **`benchmark_workers.py` memakai layanan dari `../praktikum2`** - disengaja agar data konsisten, tetapi Praktikum 3 tidak sepenuhnya mandiri.
6. **Timeout simulation** - respons ditunda di luar critical section dan hanya untuk transaksi baru; retry dengan ID sama tidak ikut tertunda.

## Langkah berikutnya

1. Lakukan L1.4 pada dua komputer fisik melalui LAN/Wi-Fi, catat IP, jenis jaringan, dan hasilnya, lalu ubah status L1.4 menjadi selesai penuh.
2. Jika ingin demonstrasi race tanpa hook, jalankan `server_transfer.py --no-lock` dan `client_transfer.py` berulang; catat bahwa hasilnya tidak deterministik.
3. Untuk kebutuhan produksi, terapkan penyimpanan `request_id` persisten dan replikasi state seperti yang direkomendasikan di laporan L3.5.
