# Runbook Praktikum 1 - XML-RPC

## Prasyarat

- Python 3.10 atau lebih baru.
- Tidak ada paket eksternal: implementasi memakai standard library Python.

## Menjalankan server dan client

Dari root repositori, buka dua terminal PowerShell.

Terminal 1:

```powershell
cd praktikum1
python server_calculator.py
```

Terminal 2:

```powershell
cd praktikum1
python client_calculator.py
```

Tambahkan `--verbose` ke client untuk menampilkan XML request dan response yang dibutuhkan laporan. Untuk menjalankan di dua komputer, jalankan server dengan `--host 0.0.0.0`; pada client gunakan IP komputer server, misalnya `python client_calculator.py --host 192.168.1.10`.

## L1.3 - datetime dan integer besar

Dengan server masih aktif, jalankan:

```powershell
cd praktikum1
python client_calculator.py --probe-l1-3 --verbose
```

Hasil yang diharapkan dari implementasi standard library Python:

- `datetime` diserialisasi sebagai XML-RPC `dateTime.iso8601`; karena `use_builtin_types=True`, nilai hasil kembali sebagai `datetime.datetime`.
- Integer `2^31` (2147483648) melampaui rentang XML-RPC standar signed 32-bit. Client Python akan memunculkan `OverflowError` ketika membuat request, sehingga nilai tidak sampai ke server. Dokumentasikan pesan error aktual dari mesin pengujian.

## Menguji kode

```powershell
cd praktikum1
python -m unittest -v test_calculator_service.py
```

## L1.4 - pengukuran latensi

Dengan server aktif, jalankan benchmark berikut. Simpan seluruh output pada laporan (beserta host, port, jumlah sampel, dan apakah server/client berada pada mesin sama atau berbeda).

```powershell
cd praktikum1
python benchmark_latency.py --samples 100
```

Perbandingan yang dipakai adalah 100 pemanggilan `tambah(5, 3)` secara lokal dan 100 panggilan XML-RPC. Hasil rata-rata RPC lazimnya jauh lebih besar karena serialisasi, HTTP, dan komunikasi jaringan.

## L1.5 - server berhenti

1. Hentikan server dengan `Ctrl+C` pada terminal server.
2. Pada terminal client, jalankan:

```powershell
cd praktikum1
python client_calculator.py --expect-offline
```

Client akan menangkap kegagalan koneksi dan menampilkan pesan yang menjelaskan host, port, serta detail error. Exit code `0` berarti kegagalan koneksi memang terjadi dan telah tertangani; jika server masih aktif, exit code `1`.

## Cakupan saat ini

- Kalkulator dasar: `tambah`, `kali`, `bagi`.
- L1.1: `pangkat`, `akar`.
- L1.2: `statistik` menghasilkan `min`, `max`, dan `rata2`.
- L1.3: endpoint `pantulkan` serta probe client untuk `datetime` dan integer di atas `2^31`.
- L1.4: `benchmark_latency.py` membandingkan 100 panggilan lokal dengan 100 XML-RPC secara default.
- L1.5: `--expect-offline` memverifikasi error koneksi saat server dimatikan.
- Fault ditangani client untuk pembagian nol, akar negatif, dan daftar kosong.

L1.3 hingga L1.5, pengukuran, serta bukti XML akan dikerjakan pada tahap berikutnya.
