# Praktikum RPC - Bagian Individu

Repositori pengerjaan praktikum individu mata kuliah Komputasi Paralel dan Terdistribusi: XML-RPC, gRPC/Protocol Buffers, lalu concurrency, retry, dan failover. Seluruh instruksi menjalankan ada di dokumen ini.

## Ringkasan

| Praktikum | Topik | Butir | Status |
| --- | --- | --- | --- |
| 1 | XML-RPC | L1.1 - L1.5 | Selesai|
| 2 | gRPC dan Protocol Buffers | L2.1 - L2.5 | Selesai dan tervalidasi |
| 3 | Concurrency, timeout, failover | L3.1 - L3.5 | Selesai dan tervalidasi |

## Prasyarat

- Windows 10/11 dengan PowerShell.
- Python 3.10 atau lebih baru (validasi terakhir memakai Python 3.14.7).
- Tidak wajib Git, tetapi disarankan untuk versioning.

## Setup

Dari root repositori:

```powershell
cd "C:\Kuliah\Semester 5\KPT\RPC\Individu"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Jika aktivasi ditolak kebijakan eksekusi PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Perintah di seluruh dokumen memakai `python` dengan asumsi `.venv` sudah aktif. Tanpa aktivasi, ganti dengan `.venv\Scripts\python.exe`.

## Cara menjalankan cepat

Semua perintah dijalankan dari root repositori. Detail tiap butir ada di [Praktikum 1](#praktikum-1---xml-rpc), [Praktikum 2](#praktikum-2---grpc-dan-protocol-buffers), dan [Praktikum 3](#praktikum-3---concurrency-timeout-dan-toleransi-kegagalan).

### Praktikum 1 - XML-RPC

```powershell
# Terminal 1
python praktikum1\server_calculator.py

# Terminal 2
python praktikum1\client_calculator.py

# Opsional: unit test
python -m unittest discover -s praktikum1 -p "test_*.py" -v
```

### Praktikum 2 - gRPC

```powershell
# Sekali saja atau setelah akademik.proto berubah
python -m grpc_tools.protoc -I praktikum2 --python_out=praktikum2 --grpc_python_out=praktikum2 praktikum2\akademik.proto

# Terminal 1
python praktikum2\server_grpc.py

# Terminal 2
python praktikum2\client_grpc.py
```

### Praktikum 3 - Bank

```powershell
# Sekali saja atau setelah bank.proto berubah
python -m grpc_tools.protoc -I praktikum3 --python_out=praktikum3 --grpc_python_out=praktikum3 praktikum3\bank.proto

# Terminal 1
python praktikum3\server_transfer.py --port 50051

# Terminal 2
python praktikum3\client_transfer.py --port 50051

# Skrip mandiri (menyalakan server sendiri)
python praktikum3\verify_transfer.py
```

## Struktur

```text
.
├── praktikum1/                 # XML-RPC
├── praktikum2/                 # gRPC + Protobuf
├── praktikum3/                 # Concurrency, retry, failover
├── docs/
│   ├── PROGRESS.md
│   ├── PLAN.md
│   └── reports/                # hasil ukur, analisis, grafik
├── requirements.txt
└── README.md
```

Kode praktikum tidak diletakkan di root. Semua panduan eksekusi dipusatkan di README ini, sedangkan bukti hasil ada di `docs/reports/`.

## Peta butir dan file utama

| Butir | Deskripsi | File |
| --- | --- | --- |
| L1.1 | `pangkat(a, b)` dan `akar(x)` | `praktikum1/calculator_service.py` |
| L1.2 | `statistik(daftar)` -> min, max, rata2 | `praktikum1/calculator_service.py` |
| L1.3 | `datetime` dan integer `2^31 + 1` via ekstensi `<i8>` | `praktikum1/client_calculator.py --probe-l1-3`, `praktikum1/xmlrpc_i8.py` |
| L1.4 | 100 panggilan RPC vs lokal | `praktikum1/benchmark_latency.py` |
| L1.5 | Perilaku saat server berhenti | `praktikum1/client_calculator.py --expect-offline` |
| L2.1 | Client streaming `KirimBanyakNilai` | `praktikum2/server_grpc.py`, `client_grpc.py` |
| L2.2 | Bidirectional streaming `Diskusi` | `praktikum2/server_grpc.py`, `client_grpc.py` |
| L2.3 | Field `prodi = 4` dan kompatibilitas stub lama | `praktikum2/test_backward_compat.py`, `old_stubs/` |
| L2.4 | Ukuran Protobuf vs XML-RPC | `praktikum2/compare_message_size.py` |
| L2.5 | 10 unary call asinkron | `praktikum2/client_async.py` |
| L3.1 | 20 transfer A ke B, total tetap 1500, validasi `request_id` | `praktikum3/verify_transfer.py` |
| L3.2 | ID tetap vs ID baru saat retry, termasuk skenario timeout | `praktikum3/simulate_double_transfer.py` |
| L3.3 | 50 transfer dari 10 client, lock vs no-lock dengan barrier terkontrol | `praktikum3/simulate_race_condition.py` |
| L3.4 | 200 `GetMahasiswa` dari 20 client, worker 1/4/10 | `praktikum3/benchmark_workers.py` |
| L3.5 | Failover dua server dan dampak restart | `praktikum3/client_failover.py` |

---

# Praktikum 1 - XML-RPC

Server dan client kalkulator berbasis XML-RPC yang memakai standard library Python. Mencakup operasi dasar, fault handling, tipe data, dan pengukuran latensi.

## File

| File | Fungsi |
| --- | --- |
| `praktikum1/calculator_service.py` | Logika kalkulator murni untuk server dan benchmark lokal. |
| `praktikum1/xmlrpc_i8.py` | Ekstensi `<i8>` untuk pengujian integer besar L1.3. |
| `praktikum1/server_calculator.py` | Server XML-RPC dan registrasi method. |
| `praktikum1/client_calculator.py` | Client demo, fault handling, probe, dan uji server offline. |
| `praktikum1/benchmark_latency.py` | Pembanding latensi lokal vs XML-RPC. |
| `praktikum1/test_calculator_service.py` | Unit test tanpa server. |

Tidak ada dependensi eksternal; cukup standard library.

## Menjalankan server dan client

Buka dua terminal PowerShell dari root repositori.

Terminal 1 - server:

```powershell
python praktikum1\server_calculator.py
```

Terminal 2 - client:

```powershell
python praktikum1\client_calculator.py
```

Server default `127.0.0.1:8000` pada path `/RPC2`. Ubah dengan `--host` dan `--port`.

Untuk menguji dari komputer lain di jaringan lokal, jalankan server dengan `--host 0.0.0.0`, lalu arahkan client ke IP komputer server:

```powershell
python praktikum1\client_calculator.py --host 192.168.1.10
```

## L1.1 - `pangkat` dan `akar`

```powershell
python praktikum1\client_calculator.py
```

Hasil yang diharapkan:

- `pangkat(2, 10) = 1024`
- `akar(81) = 9.0`
- `akar(-1)` menghasilkan XML-RPC Fault yang ditangkap client.

## L1.2 - `statistik`

`statistik([2, 4, 6, 8])` mengembalikan `{"min": 2, "max": 8, "rata2": 5.0}`. Daftar kosong dan elemen bukan angka ditolak sebagai fault.

## L1.3 - `datetime` dan integer besar

```powershell
python praktikum1\client_calculator.py --probe-l1-3 --verbose
```

Perilaku yang teramati:

- `datetime` dikirim sebagai `dateTime.iso8601` dan kembali sebagai `datetime.datetime` karena `use_builtin_types=True`.
- XML-RPC standar hanya mendefinisikan `<int>` signed 32-bit (maksimum `2147483647`). Untuk menguji nilai di atas batas itu, `praktikum1/xmlrpc_i8.py` menambahkan dukungan ekstensi `<i8>` pada marshaller client dan server. Nilai `2^31 + 1` (`2147483649`) dikirim sebagai `<i8>2147483649</i8>` dan dikembalikan sebagai `int` dengan nilai yang sama.
- Batas yang didukung ekstensi ini adalah signed 64-bit (`-2^63` sampai `2^63 - 1`).

Hasil validasi:

```text
datetime dikirim/diterima: 2026-10-31T10:30:00 -> 2026-10-31T10:30:00 (datetime)
integer besar dikirim/diterima: 2147483649 -> 2147483649 (int)
[OK] 2147483649 > batas signed 32-bit (2147483647); nilai dan tipe int dipertahankan.
```

## L1.4 - Latensi lokal vs XML-RPC

Dengan server aktif:
python praktikum1/benchmark_latency.py --host 192.168.18.231 --port 8000 --samples 100 --warmup 10

```powershell
python praktikum1/benchmark_latency.py --host 0.0.0.0 --port 8000 --samples 100 --warmup 10
```

Benchmark melakukan pemanasan, lalu mengukur setiap panggilan dengan `time.perf_counter()` dan melaporkan total, rata-rata, median, stdev, minimum, dan maksimum. Hasil validasi terakhir pada satu mesin (Windows 11, Python 3.14.7, `127.0.0.1:8000`, 100 sampel, 10 pemanasan, resolusi timer 100 ns):

| Metode | Total 100 panggilan | Rata-rata | Median | Stdev | Minimum | Maksimum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `tambah(5, 3)` lokal | 0.0311 ms | 0.0003 ms | 0.0003 ms | 0.0001 ms | 0.0002 ms | 0.0010 ms |
| XML-RPC `tambah(5, 3)` | 170.9735 ms | 1.7097 ms | 1.6215 ms | 0.3110 ms | 1.3078 ms | 2.7506 ms |

Selisih rata-rata 1.709 ms per panggilan, dengan rasio sekitar 5497x. Angka ini **bukan klaim biaya jaringan**: panggilan lokal berada dekat resolusi timer dan pengukuran hanya dilakukan di localhost. Uji lintas komputer **belum dilakukan**; untuk melakukannya jalankan server dengan `--host 0.0.0.0`, arahkan client ke IP server, lalu catat IP, jenis jaringan, dan hasil aktualnya.

## L1.5 - Server berhenti

1. Hentikan server dengan `Ctrl+C`.
2. Jalankan:

```powershell
python praktikum1\client_calculator.py --expect-offline
```

Client menangkap kegagalan koneksi (contoh: `WinError 10061`) dan menampilkan host, port, serta detail error. Exit code `0` berarti kegagalan koneksi memang terjadi dan tertangani; jika server masih aktif, exit code `1`.

## Unit test Praktikum 1

```powershell
python -m unittest discover -s praktikum1 -p "test_*.py" -v
```

Tujuh test mencakup operasi dasar, pembagian nol, L1.1, L1.2, serialisasi `datetime`, round-trip `<i8>` untuk integer besar, dan serialisasi Fault.

## Opsi CLI

### Server kalkulator

| Argumen | Default | Keterangan |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Host bind server. |
| `--port` | `8000` | Port server. |

### Client kalkulator

| Argumen | Default | Keterangan |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Host server. |
| `--port` | `8000` | Port server. |
| `--verbose` | nonaktif | Tampilkan XML request/response. |
| `--probe-l1-3` | nonaktif | Uji `datetime` dan integer besar. |
| `--expect-offline` | nonaktif | Sukses hanya bila koneksi gagal. |

### Benchmark

| Argumen | Default | Keterangan |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Host server. |
| `--port` | `8000` | Port server. |
| `--samples` | `100` | Jumlah panggilan tiap metode. |
| `--warmup` | `10` | Jumlah panggilan pemanasan sebelum pengukuran. |

## Ukuran pesan `tambah(5, 3)`

| Item | Ukuran |
| --- | ---: |
| Data murni request (`5`, `3`) | 2 byte |
| Request XML-RPC | 190 byte |
| Data murni response (`8`) | 1 byte |
| Response XML-RPC | 121 byte |
| Request Protobuf setara | 4 byte |

Overhead tag XML mencapai 98.95% pada request dan 99.17% pada response. Detail ada di [laporan validasi Praktikum 1](docs/reports/praktikum1-validation.md).

---

# Praktikum 2 - gRPC dan Protocol Buffers

Layanan akademik berbasis gRPC. Mencakup unary, server streaming, client streaming, bidirectional streaming, backward compatibility, perbandingan ukuran pesan, dan pemanggilan asinkron.

## Setup dan regenerasi stub

```powershell
python -m pip install -r requirements.txt
python -m grpc_tools.protoc -I praktikum2 --python_out=praktikum2 --grpc_python_out=praktikum2 praktikum2\akademik.proto
```

File `akademik_pb2.py` dan `akademik_pb2_grpc.py` adalah hasil generate. Jangan diedit manual; ulangi perintah `protoc` setiap kali `akademik.proto` berubah.

## File

| File | Fungsi |
| --- | --- |
| `praktikum2/akademik.proto` | Kontrak service dan message. |
| `praktikum2/akademik_pb2.py`, `akademik_pb2_grpc.py` | Stub hasil generate. |
| `praktikum2/server_grpc.py` | Implementasi server layanan nilai. |
| `praktikum2/client_grpc.py` | Demo unary, streaming, dan error handling. |
| `praktikum2/client_async.py` | L2.5 - 10 unary call asinkron dengan future. |
| `praktikum2/test_backward_compat.py` | L2.3 - stub lama melawan server baru. |
| `praktikum2/compare_message_size.py` | L2.4 - ukuran Protobuf vs XML-RPC. |
| `praktikum2/old_stubs/` | Salinan stub sebelum field `prodi` ditambahkan. |

## Kontrak RPC dan error

| RPC | Tipe | Keterangan |
| --- | --- | --- |
| `GetMahasiswa` | unary | Mengambil identitas, IPK, dan prodi. |
| `TambahNilai` | unary | Menyimpan satu nilai mata kuliah. |
| `StreamNilai` | server streaming | Mengirim nilai satu per satu. |
| `KirimBanyakNilai` | client streaming | Menerima banyak nilai dalam satu stream (L2.1). |
| `Diskusi` | bidirectional streaming | Pertukaran pesan dua arah (L2.2). |

Error yang diimplementasikan:

- `NOT_FOUND` - NIM tidak ada.
- `INVALID_ARGUMENT` - NIM/matkul kosong atau nilai di luar 0-100.

## Menjalankan server dan client

Buka dua terminal PowerShell dari root repositori.

Terminal 1 - server:

```powershell
python praktikum2\server_grpc.py
```

Terminal 2 - client:

```powershell
python praktikum2\client_grpc.py
```

Server default `127.0.0.1:50051` dengan `--max-workers 10`.

## L2.1 - Client streaming `KirimBanyakNilai`

Sudah terintegrasi di `client_grpc.py`. Client mengirim 3 nilai untuk NIM `2023002` dalam satu stream. Hasil yang diharapkan: `3 nilai tersimpan. (jumlah=3)`, lalu `StreamNilai(2023002)` menampilkan 4 nilai (1 nilai awal + 3 dari stream).

Server menampung seluruh stream, memvalidasi semuanya, baru menyimpan dalam satu critical section agar tidak ada penyimpanan parsial.

## L2.2 - Bidirectional streaming `Diskusi`

Sudah terintegrasi di `client_grpc.py`. Client mengirim 3 pesan dan server membalas setiap pesan secara streaming:

| Pesan client | Balasan server |
| --- | --- |
| "Halo, saya ingin bertanya." | "Halo juga, Mahasiswa! Ada yang bisa dibantu?" |
| "Bagaimana cara melihat nilai saya?" | "Silakan gunakan RPC GetMahasiswa atau StreamNilai untuk mengakses data nilai." |
| "Terima kasih atas informasinya." | "Sama-sama, Mahasiswa! Senang bisa membantu." |

## L2.3 - Backward compatibility field `prodi`

Field `string prodi = 4` ditambahkan pada message `Mahasiswa`. Stub lama tanpa field tersebut disimpan di `old_stubs/`. Dengan server aktif:

```powershell
python praktikum2\test_backward_compat.py --port 50051
```

Hasil yang diharapkan:

- Field stub lama: `['nim', 'nama', 'ipk']`, tanpa `prodi`.
- Client lama tetap berhasil memanggil server baru.
- Field `prodi` dari server diabaikan aman oleh client lama (forward compatibility).
- Client baru yang membaca respons server lama akan menerima string kosong karena default proto3.

## L2.4 - Perbandingan ukuran pesan

Tidak memerlukan server:

```powershell
python praktikum2\compare_message_size.py
```

| Data | Protobuf | XML-RPC | Rasio |
| --- | ---: | ---: | ---: |
| Respons GetMahasiswa (Andi, IPK 3.26, Informatika) | 37 byte | 432 byte | 11.7x |
| Request TambahNilai (Komputasi Paralel, 88) | 37 byte | 396 byte | 10.7x |
| Request `tambah(5, 3)` | 4 byte | 190 byte | 47.5x |
| 4 pesan `Nilai` vs 4 respons XML-RPC terpisah | 93 byte | 1145 byte | 12.3x |

Metode: yang dibandingkan adalah **payload serialisasi aplikasi**, bukan paket jaringan. Header HTTP/1.1 dan framing HTTP/2 + prefix 5 byte per pesan gRPC tidak dihitung untuk kedua sisi. XML-RPC menyertakan envelope `methodCall`/`methodResponse`, sedangkan Protobuf hanya message biner. Data keempat membandingkan 4 pesan Protobuf dengan 4 respons XML-RPC terpisah agar setara; bukan 4 pesan melawan satu array. Untuk `tambah(5, 3)` tidak ada RPC di `akademik.proto`, sehingga sisi Protobuf memakai ilustrasi manual dua varint (4 byte) dan diberi catatan eksplisit. Karena framing tidak dihitung, hasil ini tidak boleh dipakai sebagai klaim ukuran paket di jaringan.

## L2.5 - Client asinkron dengan future

Dengan server aktif:

```powershell
python praktikum2\client_async.py --port 50051
```

10 request `GetMahasiswa` dikirim memakai `stub.GetMahasiswa.future()` tanpa menunggu satu per satu. Waktu selesai dicatat lewat callback pada setiap future, sehingga latency individual terpisah dari total wall-clock.

Hasil validasi terakhir (server `127.0.0.1:50051`, 10 request, 1 request sengaja `NOT_FOUND`):

| Metrik | Nilai |
| --- | ---: |
| Total request | 10 |
| Sukses / gagal | 9 / 1 |
| Wall-clock total | 14.6 ms |
| Fase submit | 5.8 ms |
| Latency individual: min / mean / median / p95 / max | 4.3 / 8.4 / 9.1 / 12.1 / 12.1 ms |
| Throughput | 683.9 request/detik |
| Concurrency factor | 5.71x |

- **Latency individual** = waktu dari submit sampai future selesai, bukan `wall-clock / jumlah request`.
- **Throughput** = jumlah request / wall-clock total.
- **Concurrency factor** = jumlah latency individual / wall-clock total. Nilai 1.0 berarti tidak ada overlap (serial); nilai mendekati 10 berarti pekerjaan saling tumpang tindih. Angka ini adalah indikator overlap, **bukan jumlah thread yang aktif pada satu waktu**.
- Latency request gagal tetap dihitung karena future tetap selesai.

## Opsi CLI

### Server akademik

| Argumen | Default | Keterangan |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Host bind. |
| `--port` | `50051` | Port gRPC. |
| `--max-workers` | `10` | Jumlah thread worker. |

### Client

| Argumen | Default | Keterangan |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Host server. |
| `--port` | `50051` | Port gRPC. |

`test_backward_compat.py` dan `client_async.py` memakai opsi `--host` dan `--port` yang sama.

## Catatan Praktikum 2

- IPK dihitung dari rata-rata nilai dibagi 25, dibulatkan 2 desimal. Setelah nilai baru ditambahkan, IPK ikut berubah.
- Stub harus diregenerasi dan versi `grpcio`/`grpcio-tools` harus cocok agar tidak muncul error `Please upgrade your grpc module`.
- Bukti lengkap ada di [laporan validasi Praktikum 2](docs/reports/praktikum2-validation.md) dan [laporan fondasi](docs/reports/praktikum2-foundation-validation.md).

---

# Praktikum 3 - Concurrency, Timeout, dan Toleransi Kegagalan

Layanan bank gRPC dengan transfer saldo, deduplikasi `request_id`, retry exponential backoff, locking, benchmark worker, dan failover dua server.

## Regenerasi stub

```powershell
python -m grpc_tools.protoc -I praktikum3 --python_out=praktikum3 --grpc_python_out=praktikum3 praktikum3\bank.proto
```

File `bank_pb2.py` dan `bank_pb2_grpc.py` adalah hasil generate dan tidak diedit manual.

## File

| File | Fungsi |
| --- | --- |
| `praktikum3/bank.proto` | Kontrak `Transfer` dan `GetSaldo`. |
| `praktikum3/bank_pb2.py`, `bank_pb2_grpc.py` | Stub hasil generate. |
| `praktikum3/server_transfer.py` | Server bank: saldo, dedup cache, locking, delay/timeout simulation. |
| `praktikum3/client_transfer.py` | Client transfer: retry, backoff, mode saldo, dan `FailoverBankClient`. |
| `praktikum3/verify_transfer.py` | L3.1 - 20 transfer berulang + verifikasi saldo. |
| `praktikum3/simulate_double_transfer.py` | L3.2 - ID tetap vs ID baru saat retry. |
| `praktikum3/simulate_race_condition.py` | L3.3 - 50 transfer konkuren, lock vs tanpa lock. |
| `praktikum3/benchmark_workers.py` | L3.4 - 200 request dari 20 client pada 1/4/10 worker + grafik. |
| `praktikum3/client_failover.py` | L3.5 - failover dua server dan dampak restart. |

## Model data dan alur

- Saldo awal default: `A = 1000`, `B = 500` (total 1500).
- Setiap transfer menyertakan `request_id`. ID yang sudah pernah diproses server yang sama dikembalikan dari `_dedup_cache` dengan respons identik, sehingga retry tidak menggandakan transfer pada server tersebut. Cache tidak dibagi antar-server dan hilang saat restart.
- `threading.Lock` melindungi saldo dan cache. Mode `--no-lock` disediakan untuk mendemonstrasikan race condition.
- Client mengulang hanya pada `UNAVAILABLE` atau `DEADLINE_EXCEEDED`, memakai `request_id` yang sama, dengan backoff `0.5s, 1s, 2s`.
- `FailoverBankClient` berpindah endpoint saat server aktif tidak tersedia. Error bisnis (`FAILED_PRECONDITION`, `INVALID_ARGUMENT`, `NOT_FOUND`) tidak memicu failover.

## Menjalankan server dan client manual

Terminal 1 - server:

```powershell
python praktikum3\server_transfer.py --port 50051 --max-workers 10
```

Terminal 2 - client:

```powershell
python praktikum3\client_transfer.py --host 127.0.0.1 --port 50051
```

Mode lain:

```powershell
python praktikum3\client_transfer.py --action transfer --pengirim A --penerima B --jumlah 50
python praktikum3\client_transfer.py --action saldo --nama A
```

Failover manual membutuhkan dua server. Jalankan server kedua di terminal lain:

```powershell
python praktikum3\server_transfer.py --port 50052 --max-workers 10
python praktikum3\client_transfer.py --action transfer --failover-endpoints "127.0.0.1:50051,127.0.0.1:50052" --jumlah 100
```

## L3.1 - 20 transfer berulang

```powershell
python praktikum3\verify_transfer.py
```

20 transfer @ 10 dari A ke B dengan `request_id` unik. Hasil validasi: A = 800, B = 700, total = 1500, dedup cache 20 entri. Skrip juga mengirim `request_id` kosong dan berisi spasi; keduanya ditolak dengan `INVALID_ARGUMENT` tanpa mengubah saldo.

## L3.2 - ID tetap vs ID baru

```powershell
python praktikum3\simulate_double_transfer.py
```

- Retry dengan ID sama: respons identik dan saldo A hanya berkurang sekali (1000 -> 900).
- Retry dengan ID baru: server menganggap transaksi baru, saldo A berkurang dua kali (900 -> 700).
- Skenario timeout: server menyimpan transaksi lalu menunda respons 3 detik **di luar lock**. Retry dengan ID sama mendapat cache hit tanpa eksekusi kedua; hasil validasi A = 900, B = 600, cache 1 entri, total waktu 0.71 s termasuk retry.

## L3.3 - Concurrency 50 transfer

```powershell
python praktikum3\simulate_race_condition.py
```

10 client x 5 transfer @ 10 secara bersamaan. Mode tanpa lock memakai `threading.Barrier` sebagai hook pengujian: sekelompok thread dipaksa membaca saldo yang sama sebelum ada yang menulis, sehingga lost update dapat direproduksi secara terkontrol. Barrier tidak dipakai pada mode produksi.

| Mode | Saldo A | Saldo B | Total | Hasil |
| --- | ---: | ---: | ---: | --- |
| Dengan lock (3 ronde) | 500 | 1000 | 1500 | Konsisten di setiap ronde |
| Tanpa lock + barrier (3 ronde) | 950 | 550 | 1500 | Lost update, hasil sama di setiap ronde |

Tanpa lock, operasi baca-ubah-tulis saldo disela thread lain sehingga pembaruan tertimpa. Pada konfigurasi barrier ini, hanya satu dari sepuluh pembaruan per batch yang tercatat, sehingga A = 950 dan B = 550. Total kebetulan tetap 1500, tetapi distribusi saldo tidak sesuai dengan 50 transfer yang seharusnya. Tanpa barrier, besar penyimpangan dapat berbeda karena bergantung pada penjadwalan thread.

## L3.4 - Benchmark worker

```powershell
python praktikum3\benchmark_workers.py
```

200 request `GetMahasiswa` dari 20 client (10 request/client), server diberi `time.sleep(0.1)` per request, diuji pada `max_workers` 1, 4, dan 10. Skrip memakai layanan dari `../praktikum2`. Persentil memakai metode **nearest-rank**: data diurutkan lalu diambil indeks `ceil(p * n) - 1`; metode yang sama dipakai untuk P50, P95, dan P99.

Hasil validasi terakhir:

| max_workers | Waktu total (s) | Throughput (req/s) | Mean (ms) | P95 (ms) | P99 (ms) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | 20.45 | 9.8 | 1944.2 | 2053.6 | 2058.0 |
| 4 | 5.13 | 39.0 | 491.0 | 540.3 | 545.4 |
| 10 | 2.12 | 94.5 | 203.4 | 221.1 | 225.1 |

Grafik disimpan ke `praktikum3/l3_4_throughput_latency.png` dan `docs/reports/l3_4_throughput_latency.png`. Speedup throughput relatif terhadap 1 worker: 4.0x pada 4 worker dan 9.6x pada 10 worker. Angka ini berlaku untuk beban I/O-bound dengan delay buatan 100 ms pada mesin uji, bukan batas universal.

## L3.5 - Failover dan restart

```powershell
python praktikum3\client_failover.py
```

Skenario:

1. Primary (`50081`) dan backup (`50082`) aktif dengan saldo awal sama, tetapi state tidak direplikasi.
2. Transfer `tx-shared-001` (50) dieksekusi primary: primary A=950/B=550, backup tetap A=1000/B=500.
3. Primary dimatikan. Client failover ke backup dan mengirim **ID yang sama**; backup mengeksekusi lagi: A=950/B=550. Angka ini kebetulan sama dengan primary karena backup mulai dari A=1000 lalu menjalankan satu transfer 50, bukan karena state direplikasi. Ini membuktikan double execution lintas server.
4. Pengulangan ID yang sama di backup menghasilkan respons cache identik dan saldo tidak berubah (dedup per-server).
5. Backup direstart dengan saldo dipulihkan manual A=950/B=550, tetapi cache kosong. Retry dengan ID yang sama mengeksekusi transfer lagi: A=900/B=600.
6. `request_id` kosong/spasi ditolak dengan `INVALID_ARGUMENT` tanpa mengubah saldo.

Kesimpulan: failover hanya memindahkan request, tidak mereplikasi saldo/cache. Deduplikasi in-memory hanya memberi at-most-once selama proses server yang sama hidup; **tidak ada jaminan exactly-once lintas server atau lintas restart**. Solusi yang disarankan adalah penyimpanan transaksi persisten dengan unique constraint pada `request_id` (PostgreSQL/SQLite), WAL, cache terdistribusi dengan persistence (Redis AOF), atau outbox/event log, disertai replikasi state jika konsistensi lintas server diperlukan.

## Opsi CLI

### Server bank

| Argumen | Default | Keterangan |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Host bind. |
| `--port` | `50051` | Port gRPC. |
| `--max-workers` | `10` | Jumlah thread worker. |
| `--no-lock` | nonaktif | Nonaktifkan locking untuk demo race condition. |
| `--delay` | `0.0` | Delay acak maksimum per transfer (detik). |
| `--simulate-timeout-prob` | `0.0` | Probabilitas respons ditunda 3 detik setelah transfer tersimpan. |

### Client bank

| Argumen | Default | Keterangan |
| --- | --- | --- |
| `--host`, `--port` | `127.0.0.1`, `50051` | Alamat server. |
| `--action` | `demo` | `demo`, `transfer`, atau `saldo`. |
| `--pengirim`, `--penerima` | `A`, `B` | Akun transfer. |
| `--jumlah` | `100.0` | Nominal transfer. |
| `--nama` | `A` | Akun untuk cek saldo. |
| `--failover-endpoints` | kosong | Daftar endpoint dipisah koma. |
| `--new-uuid-on-retry` | nonaktif | Simulasi bug client yang mengganti ID saat retry. |

## Port Praktikum 3

| Komponen | Port |
| --- | ---: |
| Server manual | 50051 |
| L3.1 `verify_transfer.py` | 50071 |
| L3.2 `simulate_double_transfer.py` | 50072 |
| L3.2 skenario timeout | 50078 |
| L3.3 dengan lock / tanpa lock | 50073 / 50074 |
| L3.4 worker 1 / 4 / 10 | 50075 / 50076 / 50077 |
| L3.5 primary / backup | 50081 / 50082 |

## Catatan dan batasan Praktikum 3

- Dedup cache hanya di memori; restart menghapus riwayat `request_id`.
- `--simulate-timeout-prob` menunda respons 3 detik **di luar critical section** dan hanya untuk transaksi baru. Retry dengan ID yang sama mendapat cache hit tanpa ikut tertunda. Fitur ini dipakai pada skenario timeout L3.2.
- Hasil L3.3 tanpa lock pada skrip validasi memakai barrier terkontrol sehingga dapat diulang; tanpa barrier, besar penyimpangan bergantung pada interleaving thread.
- Bukti lengkap ada di [laporan validasi Praktikum 3](docs/reports/praktikum3-validation.md).

---

# Port seluruh praktikum

| Komponen | Port |
| --- | ---: |
| Praktikum 1 server | 8000 |
| Praktikum 2 server | 50051 |
| Praktikum 3 server manual | 50051 |
| L3.1 | 50071 |
| L3.2 | 50072 |
| L3.2 timeout | 50078 |
| L3.3 dengan/tanpa lock | 50073 / 50074 |
| L3.4 worker 1/4/10 | 50075 / 50076 / 50077 |
| L3.5 primary/backup | 50081 / 50082 |

Praktikum 2 dan server manual Praktikum 3 sama-sama memakai port `50051`, jadi jangan dijalankan bersamaan.

# Dokumentasi dan bukti

- [Rencana dan checklist](docs/PLAN.md)
- [Progres pengerjaan](docs/PROGRESS.md)
- [Validasi Praktikum 1](docs/reports/praktikum1-validation.md)
- [Validasi Praktikum 2](docs/reports/praktikum2-validation.md)
- [Validasi fondasi Praktikum 2](docs/reports/praktikum2-foundation-validation.md)
- [Validasi Praktikum 3](docs/reports/praktikum3-validation.md)
- [Grafik L3.4](docs/reports/l3_4_throughput_latency.png)

# Troubleshooting

| Gejala | Penyebab dan solusi |
| --- | --- |
| `Activate.ps1 cannot be loaded` | Jalankan `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, lalu aktivasi ulang. |
| `Address already in use` / port bentrok | Cek pemakai port: `netstat -ano \| findstr :50051`, lalu hentikan proses atau ganti `--port`. Skrip L3.x memakai port tetap, jadi pastikan 50071-50082 bebas. |
| `OverflowError: int exceeds XML-RPC limits` | Batas XML-RPC standar untuk `<int>` 32-bit. L1.3 memakai ekstensi `<i8>` untuk nilai sampai signed 64-bit; error ini muncul jika memakai client XML-RPC standar atau nilai di luar rentang `<i8>`. |
| `Please upgrade your grpc module` | Versi `grpcio` dan stub tidak cocok. Jalankan `pip install -r requirements.txt` lalu regenerasi stub. |
| Karakter Indonesia tampil rusak di console | Jalankan `$env:PYTHONUTF8=1` atau `chcp 65001`. |
| Grafik tidak muncul | `benchmark_workers.py` memakai backend `Agg` dan menyimpan PNG, bukan menampilkan jendela. |
| `ModuleNotFoundError: akademik_pb2` | Jalankan perintah dari root seperti di README, atau regenerasi stub terlebih dahulu. |

# Catatan umum

- File `*_pb2.py` dan `*_pb2_grpc.py` adalah hasil generate dan tidak diedit manual.
- Deduplikasi Praktikum 3 masih in-memory; rekomendasi persistensi ada di bagian L3.5.
- Hasil validasi lengkap beserta lingkungan uji tercatat di `docs/reports/`.
