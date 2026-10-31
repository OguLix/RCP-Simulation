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
| L3.1 | [verify_transfer.py](file:///c:/Kuliah/Semester%205/KPT/RPC/Individu/praktikum3/verify_transfer.py) | **LULUS** | 20 Transfer berulang: saldo total tetap 1500, A berkurang tepat 200 (A=800, B=700). |
| L3.2 | [simulate_double_transfer.py](file:///c:/Kuliah/Semester%205/KPT/RPC/Individu/praktikum3/simulate_double_transfer.py) | **LULUS** | ID baru menyebabkan *double transfer* (A=700 alih-alih 800), ID tetap menjaga idempotensi. |
| L3.3 | [simulate_race_condition.py](file:///c:/Kuliah/Semester%205/KPT/RPC/Individu/praktikum3/simulate_race_condition.py) | **LULUS** | Dengan lock konsisten (A=500, B=1000). Tanpa lock terjadi *lost update* (A=880, B=620). |
| L3.4 | [benchmark_workers.py](file:///c:/Kuliah/Semester%205/KPT/RPC/Individu/praktikum3/benchmark_workers.py) | **LULUS** | Sesuai modul (`sleep(0.1)`): Throughput 9.8 req/s (1 worker), 39.5 req/s (4 worker), 97.5 req/s (10 worker). |
| L3.5 | [client_failover.py](file:///c:/Kuliah/Semester%205/KPT/RPC/Individu/praktikum3/client_failover.py) | **LULUS** | Failover otomatis ke port cadangan saat primary mati. Dampak hilangnya cache saat restart dibuktikan. |

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
    [ 1] Transfer 10 dari A ke B berhasil. (A=990, B=510)
    ...
    [20] Transfer 10 dari A ke B berhasil. (A=800, B=700)
  --- Hasil ---
  Saldo A : 800 (diharapkan: 800)
  Saldo B : 700 (diharapkan: 700)
  Total   : 1500 (diharapkan: 1500)
  Dedup cache: 20 entries
  [OK] LULUS: Saldo total tetap 1500, A berkurang tepat 200.
  ```

---

### 2. L3.2 - Dampak UUID Baru vs UUID Tetap pada Retry

- **Skrip:** `praktikum3/simulate_double_transfer.py`
- **Analisis:**
  - **Skenario 1 (At-Most-Once / Idempoten):** Client mengirim transfer dengan `request_id = tx-safe-xxx`. Ketika terjadi retry dengan `request_id` yang sama, server mendeteksi `request_id` di `_dedup_cache` dan mengembalikan respons yang sama persis tanpa mengurangi saldo kembali. Saldo A berkurang tepat 100 (1000 -> 900).
  - **Skenario 2 (Double Spending / Non-Idempoten):** Client mengirim percobaan 1 dengan ID `tx-bad-1`, lalu karena timeout client secara keliru men-generate ID baru `tx-bad-2` pada saat retry. Server menganggap keduanya adalah dua transaksi berbeda, sehingga mengeksekusi kedua transaksi tersebut. Saldo A berkurang 200 (900 -> 700).

---

### 3. L3.3 - Pengujian Concurrency 50 Transfer (Lock vs No-Lock)

- **Skrip:** `praktikum3/simulate_race_condition.py`
- **Konfigurasi:** 10 thread client mengirim masing-masing 5 transaksi @ Rp10 secara bersamaan (total 50 transaksi = Rp500). Saldo awal A=1000, B=500.
- **Hasil Komparasi:**

| Pengujian | Saldo A Akhir | Saldo B Akhir | Total Saldo | Status Integritas Data |
| --- | ---: | ---: | ---: | --- |
| **DENGAN LOCK** | 500.0 | 1000.0 | 1500.0 | **Sempurna (Thread-safe)** |
| **TANPA LOCK** | 880.0 | 620.0 | 1500.0 | **Rusak (Lost Update: A kelebihan 380, B kekurangan 380)** |

- **Penyebab Race Condition:**
  Operasi pembaruan saldo di Python tidak atomik (melibatkan *LOAD_FAST*, *BINARY_SUBTRACT*, *STORE_FAST*). Ketika thread A membaca saldo sebelum thread B selesai menulis, pembaruan saldo tertimpa (*lost update*). Penggunaan `threading.Lock()` mencegah interleaving antar thread.

---

### 4. L3.4 - Benchmark Concurrency Server (`GetMahasiswa`)

- **Skrip:** `praktikum3/benchmark_workers.py`
- **Metodologi (Sesuai Modul Dosen Hal. 11):** 200 total request dikirim secara konkuren oleh 20 client thread (10 request/thread) terhadap server `GetMahasiswa` dengan `time.sleep(0.1)` ditambahkan di server untuk `max_workers` = 1, 4, dan 10.
- **Tabel Hasil Pengukuran:**

| max_workers | Waktu total (s) | Throughput (req/s) | Latensi rata-rata (ms) | P95 (ms) |
| :---: | :---: | :---: | :---: | :---: |
| **1** | 20.32 | 9.8 | 1932.6 | 2038.3 |
| **4** | 5.07 | 39.5 | 485.7 | 510.4 |
| **10** | 2.05 | 97.5 | 198.9 | 208.3 |

- **Grafik:** Disimpan di `docs/reports/l3_4_throughput_latency.png`.
- **Analisis:**
  - Dengan `time.sleep(0.1)` (100 ms) per request, server dengan `max_workers=1` memproses secara serial sehingga 20 client yang mengirim request bersamaan harus mengantre hingga latensi rata-rata mencapai ~1.93 detik dan throughput hanya 9.8 req/s.
  - Saat worker ditingkatkan ke 4, throughput melonjak **4.0x** (39.5 req/s) dan latensi rata-rata terpangkas menjadi 485.7 ms.
  - Pada 10 worker, throughput mencapai **97.5 req/s** (**9.9x speedup**) dan latensi terpangkas hingga 198.9 ms. Hal ini membuktikan efektivitas ThreadPoolExecutor untuk tugas I/O bound.

---

### 5. L3.5 - Failover Otomatis dan Ketahanan Restart

- **Skrip:** `praktikum3/client_failover.py`
- **Alur Validasi Failover:**
  1. Server Primary (port 50081) dan Backup (port 50082) dijalankan.
  2. Client mengirim transaksi 1 ke Primary -> sukses dilayani oleh Primary.
  3. Server Primary dimatikan mendadak (`server.stop(grace=0)`).
  4. Client mengirim transaksi 2 -> mengalami `UNAVAILABLE` pada Primary, otomatis beralih (*failover*) ke port 50082 (Backup). Transaksi berhasil diproses tanpa aplikasi client crash.

- **Analisis Dampak Restart terhadap In-Memory Deduplication:**
  - Cache deduplikasi `_dedup_cache` disimpan di memori RAM proses server.
  - Ketika server crash atau di-restart, seluruh riwayat `request_id` yang sudah diproses ikut terhapus.
  - Pembuktian: Saat client mengirim ulang `tx-restart-999` ke server yang baru direstart, server menganggap transaksi tersebut adalah baru dan memotong saldo untuk kedua kalinya.

- **Rekomendasi Solusi Penyimpanan Persisten:**
  1. **Relational Database (PostgreSQL / SQLite):**
     Tabel `transaksi` dengan kolom `request_id VARCHAR PRIMARY KEY`, `pengirim`, `penerima`, `jumlah`, dan `status`. Memanfaatkan transaksi ACID (`BEGIN TRANSACTION ... COMMIT`) untuk menjamin atomisitas pemotongan saldo dan pencatatan deduplikasi.
  2. **Distributed Cache dengan Persistence (Redis AOF):**
     Menyimpan `request_id` sebagai key dengan `SET key response NX EX 86400` (kedaluwarsa 24 jam) dengan mode persistensi Append-Only File (AOF) atau Redis Cluster.
  3. **Outbox Pattern / Event Sourcing:**
     Pencatatan mutasi dalam log append-only tidak dapat dihapus, memastikan idempotensi terjamin meskipun server mengalami kegagalan berkali-kali.
