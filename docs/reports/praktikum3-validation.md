# Hasil Validasi Praktikum 3: Concurrency, Timeout, dan Toleransi Kegagalan

## Lingkungan Pengujian

- Tanggal: 31 Oktober 2026.
- Sistem Operasi: Windows 11 (64-bit).
- Python: 3.14.x melalui virtual environment `.venv`.
- Dependensi: `grpcio`, `protobuf`, `matplotlib`.

---

## Ringkasan Hasil Validasi

| Butir | Deskripsi & File | Status | Keterangan |
| --- | --- | --- | --- |
| Kontrak Proto | `Transfer` & `GetSaldo` pada `bank.proto` | **LULUS** | Protobuf stub digenerate tanpa modifikasi manual. |
| Deduplikasi | Identifikasi `request_id` in-memory | **LULUS** | Request duplikat mengembalikan respons cache identik. |
| Retry & Backoff | Exponential backoff pada client | **LULUS** | Client menggunakan ID tetap saat retry (`UNAVAILABLE`/`DEADLINE_EXCEEDED`). |
| L3.1 | [verify_transfer.py](file:///c:/Kuliah/Semester%205/KPT/RPC/Individu/praktikum3/verify_transfer.py) | **LULUS** | 20 Transfer berulang: total tetap 1500, A berkurang tepat 200 (A=800, B=700). `request_id` kosong/spasi ditolak `INVALID_ARGUMENT`. |
| L3.2 | [simulate_double_transfer.py](file:///c:/Kuliah/Semester%205/KPT/RPC/Individu/praktikum3/simulate_double_transfer.py) | **LULUS** | ID sama: respons identik, transfer 1x. ID baru: transfer ganda (A=700). Timeout + retry ID sama: cache hit, tanpa eksekusi kedua. |
| L3.3 | [simulate_race_condition.py](file:///c:/Kuliah/Semester%205/KPT/RPC/Individu/praktikum3/simulate_race_condition.py) | **LULUS** | 3 ronde dengan lock konsisten (A=500, B=1000). 3 ronde tanpa lock + barrier terkontrol selalu *lost update* (A=950, B=550). |
| L3.4 | [benchmark_workers.py](file:///c:/Kuliah/Semester%205/KPT/RPC/Individu/praktikum3/benchmark_workers.py) | **LULUS** | `sleep(0.1)` per request: 9.8 / 39.0 / 94.5 req/s pada 1/4/10 worker. P95 dan P99 memakai nearest-rank. |
| L3.5 | [client_failover.py](file:///c:/Kuliah/Semester%205/KPT/RPC/Individu/praktikum3/client_failover.py) | **LULUS** | Failover ke backup, double execution lintas server, dedup per-server, dan hilangnya cache setelah restart dibuktikan dengan state nyata. |

---

## Bukti Validasi Detail

### 1. L3.1 - 20 Transfer Berulang (Deduplikasi & Konsistensi Saldo)

- **Skrip:** `praktikum3/verify_transfer.py`
- **Konfigurasi:** Saldo awal A = 1000, B = 500 (Total = 1500). 20 transaksi @ Rp10 dari A ke B.
- **Log Eksekusi:**
  ```text
  === L3.1: 20 Transfer A->B dengan Deduplikasi (verify_transfer) ===
  Server berjalan di port 50071.
  Saldo awal: {'A': 1000.0, 'B': 500.0}
  --- Validasi request_id ---
    [OK] request_id '' ditolak: INVALID_ARGUMENT
    [OK] request_id '   ' ditolak: INVALID_ARGUMENT
  --- 20 transfer dengan request_id unik ---
    [ 1] Transfer 10 dari A ke B berhasil. (A=990, B=510)
    ...
    [20] Transfer 10 dari A ke B berhasil. (A=800, B=700)
  --- Hasil ---
  Saldo A : 800 (diharapkan: 800)
  Saldo B : 700 (diharapkan: 700)
  Total   : 1500 (diharapkan: 1500)
  Dedup cache: 20 entries
  [OK] LULUS: Saldo total tetap 1500, A berkurang tepat 200.
  [OK] request_id kosong/spasi ditolak tanpa mengubah saldo.
  ```

---

### 2. L3.2 - Dampak UUID Baru vs UUID Tetap pada Retry

- **Skrip:** `praktikum3/simulate_double_transfer.py`
- **Analisis:**
  - **Skenario 1 (At-Most-Once / Idempoten):** Client mengirim transfer dengan `request_id = tx-safe-xxx`. Ketika terjadi retry dengan `request_id` yang sama, server mendeteksi `request_id` di `_dedup_cache` dan mengembalikan respons yang sama persis tanpa mengurangi saldo kembali. Saldo A berkurang tepat 100 (1000 -> 900).
  - **Skenario 2 (Double Spending / Non-Idempoten):** Client mengirim percobaan 1 dengan ID `tx-bad-1`, lalu karena timeout client secara keliru men-generate ID baru `tx-bad-2` pada saat retry. Server menganggap keduanya adalah dua transaksi berbeda, sehingga mengeksekusi kedua transaksi tersebut. Saldo A berkurang 200 (900 -> 700).
  - **Skenario 3 (Timeout Setelah Commit):** Server menyimpan transaksi, lalu menunda respons 3 detik **di luar lock**. Client timeout 0.5 s dan retry dengan ID yang sama. Retry mendapat cache hit tanpa eksekusi kedua. Hasil aktual: A=900, B=600, cache 1 entri, total waktu 0.71 s termasuk retry. Ini menunjukkan at-most-once selama cache server masih hidup, bukan exactly-once lintas restart.

---

### 3. L3.3 - Pengujian Concurrency 50 Transfer (Lock vs No-Lock)

- **Skrip:** `praktikum3/simulate_race_condition.py`
- **Konfigurasi:** 10 thread client mengirim masing-masing 5 transaksi @ Rp10 secara bersamaan (total 50 transaksi = Rp500). Saldo awal A=1000, B=500. Pengujian dijalankan 3 ronde untuk lock dan 3 ronde untuk no-lock.
- **Kontrol race:** Mode tanpa lock memakai `threading.Barrier(10)` sebagai hook pengujian. Barrier memaksa sepuluh thread membaca saldo yang sama sebelum ada yang menulis, sehingga lost update tidak bergantung pada keberuntungan penjadwalan. Barrier tidak dipakai pada mode produksi.
- **Hasil Komparasi:**

| Pengujian | Saldo A Akhir | Saldo B Akhir | Total Saldo | Status Integritas Data |
| --- | ---: | ---: | ---: | --- |
| **DENGAN LOCK (3 ronde)** | 500.0 | 1000.0 | 1500.0 | **Sempurna dan konsisten di semua ronde** |
| **TANPA LOCK + BARRIER (3 ronde)** | 950.0 | 550.0 | 1500.0 | **Lost update, hasil sama di semua ronde** |

- **Penyebab Race Condition:**
  Operasi pembaruan saldo melibatkan baca-ubah-tulis yang tidak atomik. Dengan barrier, sepuluh thread membaca nilai awal yang sama; ketika semuanya menulis, hanya pembaruan terakhir yang bertahan. Pada konfigurasi ini hanya satu dari sepuluh pembaruan per batch yang tercatat, sehingga A=950 dan B=550 setelah lima batch. Total kebetulan tetap 1500, tetapi distribusi saldo tidak sesuai dengan 50 transfer yang seharusnya (A=500, B=1000). Penggunaan `threading.Lock()` mencegah interleaving tersebut.

---

### 4. L3.4 - Benchmark Concurrency Server (`GetMahasiswa`)

- **Skrip:** `praktikum3/benchmark_workers.py`
- **Metodologi:** 200 total request dikirim secara konkuren oleh 20 client thread (10 request/thread) terhadap server `GetMahasiswa` dengan `time.sleep(0.1)` ditambahkan di server untuk `max_workers` = 1, 4, dan 10. Persentil memakai nearest-rank: data diurutkan lalu diambil indeks `ceil(p * n) - 1`; metode yang sama dipakai untuk P50, P95, dan P99.
- **Tabel Hasil Pengukuran:**

| max_workers | Waktu total (s) | Throughput (req/s) | Mean (ms) | P95 (ms) | P99 (ms) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | 20.45 | 9.8 | 1944.2 | 2053.6 | 2058.0 |
| **4** | 5.13 | 39.0 | 491.0 | 540.3 | 545.4 |
| **10** | 2.12 | 94.5 | 203.4 | 221.1 | 225.1 |

- **Grafik:** Disimpan di `docs/reports/l3_4_throughput_latency.png` dan `praktikum3/l3_4_throughput_latency.png`.
- **Analisis:**
  - Dengan `time.sleep(0.1)` (100 ms) per request, server dengan `max_workers=1` memproses secara serial sehingga 20 client yang mengirim request bersamaan harus mengantre. Latensi rata-rata mencapai sekitar 1.94 detik dan throughput 9.8 req/s.
  - Pada 4 worker, throughput menjadi **39.0 req/s** (sekitar **4.0x** relatif terhadap 1 worker) dan latensi rata-rata turun menjadi 491.0 ms.
  - Pada 10 worker, throughput menjadi **94.5 req/s** (sekitar **9.6x**) dan latensi rata-rata 203.4 ms. P99 juga turun dari 2058.0 ms menjadi 225.1 ms.
  - Hasil ini konsisten dengan beban I/O-bound buatan (`time.sleep`) pada mesin uji. Angkanya bukan batas universal dan tidak boleh digeneralisasi ke beban CPU-bound atau jaringan nyata.

---

### 5. L3.5 - Failover Otomatis dan Batas Deduplikasi Lintas Server/Restart

- **Skrip:** `praktikum3/client_failover.py`
- **Alur Validasi:**
  1. Primary (port 50081) dan backup (port 50082) dijalankan dengan saldo awal sama, tetapi state tidak direplikasi.
  2. `request_id` kosong dan spasi ditolak `INVALID_ARGUMENT`; saldo tidak berubah.
  3. Transfer `tx-shared-001` (50) ke primary: primary menjadi A=950/B=550, backup tetap A=1000/B=500.
  4. Primary dimatikan (`server.stop(grace=0)`). Client gagal menghubungi primary, lalu failover ke backup dan mengirim **ID yang sama**. Backup mengeksekusi transfer: A=950/B=550. Angka ini kebetulan sama dengan primary karena backup mulai dari A=1000 lalu menjalankan satu transfer 50, bukan karena state direplikasi. Ini adalah double execution lintas server karena cache primary tidak ikut pindah.
  5. Pengulangan ID yang sama di backup mengembalikan respons cache identik; saldo tetap A=950/B=550 dan cache berisi 1 entri. Deduplikasi hanya berlaku per-server.
  6. Backup direstart dengan saldo dipulihkan manual A=950/B=550. Cache kosong (0 entri). Retry dengan ID yang sama mengeksekusi transfer lagi: A=900/B=600 dan cache berisi 1 entri baru.

- **Kesimpulan:**
  - Failover memindahkan request ke server lain, tetapi tidak mereplikasi saldo maupun cache deduplikasi.
  - Deduplikasi in-memory hanya memberi **at-most-once selama proses server yang sama masih hidup**.
  - **Tidak ada jaminan exactly-once lintas server atau lintas restart.** Skrip tidak mengklaim konsistensi lintas server.
  - Restart menghapus cache meskipun saldo dipulihkan; retry dengan ID lama dapat mengeksekusi transfer kembali.

- **Rekomendasi Solusi Penyimpanan Persisten:**
  1. **Relational Database (PostgreSQL / SQLite):**
     Tabel `transaksi` dengan kolom `request_id VARCHAR PRIMARY KEY`, `pengirim`, `penerima`, `jumlah`, dan `status`. Memanfaatkan transaksi ACID (`BEGIN TRANSACTION ... COMMIT`) untuk menjamin atomisitas pemotongan saldo dan pencatatan deduplikasi.
  2. **Distributed Cache dengan Persistence (Redis AOF):**
     Menyimpan `request_id` sebagai key dengan `SET key response NX EX 86400` (kedaluwarsa 24 jam) dengan mode persistensi Append-Only File (AOF) atau Redis Cluster.
  3. **Outbox Pattern / Event Sourcing:**
     Pencatatan mutasi dalam log append-only tidak dapat dihapus, memastikan idempotensi terjamin meskipun server mengalami kegagalan berkali-kali.
  4. **Replikasi state/cache** atau penyimpanan bersama jika konsistensi lintas server diperlukan; failover saja tidak cukup.
