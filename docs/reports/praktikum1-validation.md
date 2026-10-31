# Hasil Validasi Praktikum 1

## Lingkungan uji

- Tanggal: 31 Oktober 2026 (Asia/Jakarta).
- Interpreter: Python 3.14 64-bit.
- Host: satu komputer lokal (`127.0.0.1`).
- Server uji: port `8010` (dipilih agar tidak mengganggu port default `8000`).
- Jumlah sampel benchmark: 100 panggilan untuk tiap metode.

## Unit test

Perintah:

```powershell
.venv\Scripts\python.exe -m unittest discover -s praktikum1 -p 'test_*.py' -v
```

Hasil: **5 test lulus** dalam 0.001 detik.

- Operasi dasar (`tambah`, `kali`, `bagi`).
- Penolakan pembagian nol.
- L1.1 `pangkat` dan `akar` (termasuk akar negatif).
- L1.2 `statistik` (termasuk daftar kosong dan elemen bukan angka).
- L1.3 fungsi pantul untuk objek `datetime`.

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

- `datetime(2026, 10, 31, 10, 30, 0)` berhasil dikirim dan diterima kembali sebagai `datetime` saat `use_builtin_types=True` digunakan.
- Integer `2147483648` (`2^31`) memunculkan `OverflowError: int exceeds XML-RPC limits` pada client sebelum request dikirim. Ini konsisten dengan batas integer signed 32-bit pada XML-RPC standard library.

## L1.4 - benchmark lokal awal

| Metode | Total 100 panggilan | Rata-rata | Minimum | Maksimum |
| --- | ---: | ---: | ---: | ---: |
| `tambah(5, 3)` lokal | 0.018 ms | 0.000 ms | 0.000 ms | 0.001 ms |
| XML-RPC `tambah(5, 3)` | 102.609 ms | 1.026 ms | 0.833 ms | 7.597 ms |

Perbandingan rata-rata yang tercetak adalah sekitar 5669.0x. Angka ini tidak boleh dipakai sebagai klaim lintas komputer karena durasi panggilan lokal berada dekat resolusi timer. Hasil ini hanya membuktikan benchmark bekerja. Untuk memenuhi tugas, ulangi dengan server dan client pada dua komputer berbeda, lalu catat IP, jaringan, dan hasil aktualnya.

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
  Sebagai perbandingan, pada Praktikum 2, request gRPC setara hanya membutuhkan **4 bytes** (Protobuf binary varint), menghemat bandwidth hingga **47.5x lebih ringkas** dibanding XML-RPC.

## Catatan Pengujian Lanjutan

- Untuk pengujian lintas komputer fisik pada L1.4, jalankan server dengan `--host 0.0.0.0` dan client dengan `--host <IP_SERVER_FISIK>` melalui jaringan lokal (LAN/Wi-Fi).

