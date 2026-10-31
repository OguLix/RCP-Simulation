# Runbook Praktikum 3: Concurrency, Timeout, dan Toleransi Kegagalan

Dokumen ini memuat panduan lengkap untuk menjalankan server, client, dan seluruh skrip pengujian Praktikum 3 pada Windows PowerShell.

---

## Prasyarat

Pastikan virtual environment telah aktif dan dependensi terpasang:

```powershell
# Aktivasi virtual environment
.\.venv\Scripts\Activate.ps1

# Verifikasi dependensi
python -m pip install -r requirements.txt
```

---

## 1. Kompilasi Protobuf (Opsional jika ingin regenerasi)

Jika file `praktikum3/bank.proto` diubah, lakukan kompilasi ulang stub gRPC:

```powershell
python -m grpc_tools.protoc -Ipraktikum3 --python_out=praktikum3 --grpc_python_out=praktikum3 praktikum3/bank.proto
```

---

## 2. Menjalankan Server Bank Manual

### Server Tunggal Standar (port 50051)
```powershell
python praktikum3\server_transfer.py --port 50051 --max-workers 10
```

### Opsi Parameter Server:
- `--host`: Alamat IP bind (default: `127.0.0.1`).
- `--port`: Port gRPC (default: `50051`).
- `--max-workers`: Jumlah worker thread pool server (default: `10`).
- `--no-lock`: Nonaktifkan locking thread untuk demonstrasi race condition.
- `--delay`: Simulasi delay pemrosesan transaksi dalam detik (default: `0.0`).
- `--simulate-timeout-prob`: Probabilitas balasan terlambat 3 detik untuk memicu timeout pada client (default: `0.0`).

---

## 3. Menjalankan Client Bank Manual

### Mode Demo Standar
```powershell
python praktikum3\client_transfer.py --host 127.0.0.1 --port 50051
```

### Mode Kirim Transfer Tertentu
```powershell
python praktikum3\client_transfer.py --action transfer --pengirim A --penerima B --jumlah 50
```

### Mode Cek Saldo Akun
```powershell
python praktikum3\client_transfer.py --action saldo --nama A
```

### Mode Failover Multi-Server
```powershell
python praktikum3\client_transfer.py --action transfer --failover-endpoints "127.0.0.1:50051,127.0.0.1:50052" --jumlah 100
```

---

## 4. Menjalankan Seluruh Pengujian Terstandarisasi (L3.1 - L3.5)

Setiap skrip pengujian di bawah ini bersifat mandiri (*self-contained*), secara otomatis mengelola siklus hidup server pada port khusus, dan mencakup asersi validasi:

### L3.1: Verifikasi 20 Transfer Berulang A ke B (Integritas Saldo & Deduplikasi)
```powershell
python praktikum3\verify_transfer.py
```
*Ekspektasi:* Saldo A berkurang tepat 200, saldo B bertambah 200, saldo total tetap 1500.

### L3.2: Demonstrasi Request ID Tetap vs Request ID Baru (Double Transfer)
```powershell
python praktikum3\simulate_double_transfer.py
```
*Ekspektasi:* Retry dengan ID sama menjaga idempotensi; retry dengan ID baru memicu transfer ganda.

### L3.3: Uji Concurrency 50 Transfer dari 10 Client (Lock vs No-Lock)
```powershell
python praktikum3\simulate_race_condition.py
```
*Ekspektasi:* Eksekusi dengan lock menghasilkan saldo tepat (A=500, B=1000). Eksekusi tanpa lock membuktikan terjadinya lost update.

### L3.4: Benchmark Concurrency dan Visualisasi Grafik (sleep=0.1s)
```powershell
python praktikum3\benchmark_workers.py
```
*Ekspektasi:* Mengukur throughput dan latensi untuk 1, 4, dan 10 workers dengan `time.sleep(0.1)` di server, menampilkan tabel, dan menghasilkan grafik `docs/reports/l3_4_throughput_latency.png`.

### L3.5: Failover Otomatis Dua Server dan Analisis Restart Deduplikasi
```powershell
python praktikum3\client_failover.py
```
*Ekspektasi:* Saat server primary dimatikan, client otomatis failover ke server backup tanpa error; mendemonstrasikan hilangnya cache in-memory saat server crash/restart.
