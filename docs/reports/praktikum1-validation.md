# Hasil Validasi Praktikum 1

## Lingkungan uji

- Tanggal: 31 Oktober 2026 (Asia/Jakarta).
- Interpreter: Python 3.14 64-bit.
- Host: satu komputer lokal (`127.0.0.1`).
- Server uji: port `8000` (default).
- Jumlah sampel benchmark: 100 panggilan untuk tiap metode.

## Unit test

Perintah:

```powershell
.venv\Scripts\python.exe -m unittest discover -s praktikum1 -p 'test_*.py' -v
```

Hasil: **7 test lulus** dalam 0.001 detik.

- Operasi dasar (`tambah`, `kali`, `bagi`).
- Penolakan pembagian nol.
- L1.1 `pangkat` dan `akar` (termasuk akar negatif).
- L1.2 `statistik` (termasuk daftar kosong dan elemen bukan angka).
- L1.3 fungsi pantul untuk objek `datetime`.
- L1.3 serialisasi `<i8>` untuk integer `2^31 + 1` (request dan response).

## Integrasi server-client

Seluruh RPC yang tersedia: `tambah`, `kali`, `bagi`, `pangkat`, `akar`, `statistik`, `pantulkan`, serta introspection API.

| Skenario | Hasil |
| --- | --- |
| `tambah(5, 3)` | `8` |
| `kali(4, 7)` | `28` |
| `bagi(10, 2)` | `5.0` |
| `pangkat(2, 10)` | `1024` |
| `akar(81)` | `9.0` |
| `statistik([2, 4, 6, 8])` | `min=2`, `max=8`, `rata2=5.0` |
| `bagi(10, 0)` | XML-RPC Fault `ValueError`, tertangani client |
| `akar(-1)` | XML-RPC Fault `ValueError`, tertangani client |
| `statistik([])` | XML-RPC Fault `ValueError`, tertangani client |

## L1.3 - serialisasi

- `datetime(2026, 10, 31, 10, 30, 0)` berhasil dikirim sebagai `dateTime.iso8601` dan diterima kembali sebagai `datetime` saat `use_builtin_types=True` digunakan. Nilai dan tipe tidak berubah.
- XML-RPC standar hanya mendefinisikan `<int>` signed 32-bit dengan maksimum `2147483647`. Marshaller bawaan Python menolak nilai di atas batas itu sebelum request dikirim.
- Agar pengujian integer di atas batas tetap dapat dilakukan sebagai `int`, `praktikum1/xmlrpc_i8.py` menambahkan ekstensi `<i8>` pada marshaller client dan server. `Unmarshaller` bawaan Python sudah mengenali `<i8>`.
- Nilai uji `2^31 + 1` = `2147483649` dikirim melalui XML-RPC dan dikembalikan dengan nilai serta tipe yang sama. Potongan XML aktual:

```xml
<value><i8>2147483649</i8></value>
```

Hasil eksekusi aktual:

```text
datetime dikirim/diterima: 2026-10-31T10:30:00 -> 2026-10-31T10:30:00 (datetime)
integer besar dikirim/diterima: 2147483649 -> 2147483649 (int)
[OK] 2147483649 > batas signed 32-bit (2147483647); nilai dan tipe int dipertahankan.
```

- Unit test `test_l1_3_serialisasi_fault` juga memverifikasi bahwa respons Fault dibungkus dalam `<methodResponse>` dan dapat dibaca kembali sebagai `xmlrpc.client.Fault`.
- Integrasi `bagi(10, 0)`, `akar(-1)`, dan `statistik([])` menghasilkan respons `<methodResponse><fault>...</fault></methodResponse>` standar; client menangkapnya sebagai `xmlrpc.client.Fault` tanpa error parsing.
- Ekstensi `<i8>` mendukung rentang signed 64-bit (`-2^63` sampai `2^63 - 1`); nilai di luar rentang itu tetap ditolak dengan `OverflowError`.

## L1.4 - benchmark lokal

Perintah: `python praktikum1\benchmark_latency.py --samples 100 --warmup 10`.

Lingkungan: Windows 11, Python 3.14.7 64-bit, `127.0.0.1:8000`, resolusi `time.perf_counter()` 100 ns, 100 sampel, 10 panggilan pemanasan.

| Metode | Total 100 panggilan | Rata-rata | Median | Stdev | Minimum | Maksimum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `tambah(5, 3)` lokal | 0.0311 ms | 0.0003 ms | 0.0003 ms | 0.0001 ms | 0.0002 ms | 0.0010 ms |
| XML-RPC `tambah(5, 3)` | 170.9735 ms | 1.7097 ms | 1.6215 ms | 0.3110 ms | 1.3078 ms | 2.7506 ms |

Selisih rata-rata 1.709 ms per panggilan, rasio sekitar 5497x. Angka ini tidak boleh dipakai sebagai klaim lintas komputer karena durasi lokal berada dekat resolusi timer dan pengukuran hanya dilakukan di localhost. Hasil ini membuktikan benchmark bekerja, bukan biaya jaringan. **Uji dua komputer fisik belum dilakukan**; langkahnya: jalankan server dengan `--host 0.0.0.0`, arahkan client ke IP server, lalu catat IP, jenis jaringan, dan hasil aktualnya.

## L1.5 - server mati

Setelah server pengujian dihentikan, client dengan `--expect-offline` menampilkan `WinError 10061` (koneksi ditolak) dan keluar dengan status sukses untuk skenario pengujian ini. Artinya error koneksi tertangani secara eksplisit dan informatif.

## Analisis Ukuran Pesan XML dan Overhead (tambah(5, 3))

### Contoh `methodCall` XML (190 bytes)

```xml
<?xml version='1.0'?>
<methodCall>
<methodName>tambah</methodName>
<params>
<param>
<value><int>5</int></value>
</param>
<param>
<value><int>3</int></value>
</param>
</params>
</methodCall>
```

### Contoh `methodResponse` XML (121 bytes)

```xml
<?xml version='1.0'?>
<methodResponse>
<params>
<param>
<value><int>8</int></value>
</param>
</params>
</methodResponse>
```

### Perhitungan Overhead Format XML vs Data Murni

- **Ukuran Data Murni Request:** Angka `5` dan `3` (hanya **2 byte** ASCII).
- **Ukuran Request XML:** **190 bytes**.
  - **Overhead XML Request:** `(190 - 2) / 190 * 100% = 98.95%` overhead metadata/tagging!
- **Ukuran Data Murni Response:** Angka `8` (**1 byte** ASCII).
- **Ukuran Response XML:** **121 bytes**.
  - **Overhead XML Response:** `(121 - 1) / 121 * 100% = 99.17%` overhead tag XML.
- **Komparasi Protobuf:**
  Sebagai perbandingan, ilustrasi encoding dua varint untuk request setara hanya membutuhkan **4 bytes**. Angka ini bukan pesan dari `akademik.proto` (tidak ada RPC `tambah` di sana), sehingga hanya menggambarkan overhead format, bukan hasil pengukuran RPC Protobuf yang sebenarnya.

## Catatan Pengujian Lanjutan

- Untuk pengujian lintas komputer fisik pada L1.4, jalankan server dengan `--host 0.0.0.0` dan client dengan `--host <IP_SERVER_FISIK>` melalui jaringan lokal (LAN/Wi-Fi).

