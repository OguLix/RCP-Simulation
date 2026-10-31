# Validasi Praktikum 2 - Lengkap

## Lingkungan uji

- Tanggal: 31 Oktober 2026 (Asia/Jakarta).
- Interpreter: Python 3.14.7 64-bit dalam `.venv/`.
- Dependensi: `grpcio 1.85.1`, `grpcio-tools 1.85.1`, dan `protobuf 7.36.2`.
- Host: `127.0.0.1`.
- Port pengujian: `50063`.

## Fondasi (tervalidasi sebelumnya)

| Skenario | Hasil |
| --- | --- |
| `GetMahasiswa(2023001)` | `Andi (2023001) - IPK 3.26 - Prodi: Informatika` |
| `TambahNilai(2023001, Komputasi Paralel, 88)` | `Nilai tersimpan.` |
| `StreamNilai(2023001)` | 3 nilai: Basis Data 85, Jaringan 78, Komputasi Paralel 88. |
| `GetMahasiswa(9999999)` | `NOT_FOUND` - NIM tidak ditemukan. |
| `TambahNilai(..., nilai=101)` | `INVALID_ARGUMENT` - Nilai harus 0-100. |

## L2.1 - Client streaming `KirimBanyakNilai`

Client mengirim 3 nilai untuk NIM `2023002` melalui satu stream. Server menerima dan menyimpan ketiganya.

Hasil: `3 nilai tersimpan. (jumlah=3)`. StreamNilai setelahnya mengembalikan 4 nilai (1 awal + 3 dari stream).

## L2.2 - Bidirectional streaming `Diskusi`

Proto menambahkan `rpc Diskusi(stream Pesan) returns (stream Pesan)` dan message `Pesan` dengan field `pengirim` dan `isi`.

Client mengirim 3 pesan diskusi:

| Pesan client | Balasan server |
| --- | --- |
| "Halo, saya ingin bertanya." | "Halo juga, Mahasiswa! Ada yang bisa dibantu?" |
| "Bagaimana cara melihat nilai saya?" | "Silakan gunakan RPC GetMahasiswa atau StreamNilai untuk mengakses data nilai." |
| "Terima kasih atas informasinya." | "Sama-sama, Mahasiswa! Senang bisa membantu." |

Server memproses setiap pesan client dan menghasilkan balasan kontekstual secara streaming. Kedua arah berjalan bersamaan dalam satu koneksi gRPC.

## L2.3 - Backward compatibility dengan field `prodi`

Field `string prodi = 4` ditambahkan pada message `Mahasiswa`. Stub lama (tanpa prodi) disalin ke `old_stubs/` sebelum perubahan proto.

Pengujian:

```
Field pada Mahasiswa (stub lama): ['nim', 'nama', 'ipk']
Stub lama memiliki field 'prodi': False

Respons GetMahasiswa dengan stub LAMA:
  nim  : 2023001
  nama : Andi
  ipk  : 3.35
  prodi: (field tidak ada pada stub lama - ini yang diharapkan)

[BUKTI] Client dengan stub lama berhasil memanggil server baru.
Field 'prodi' yang dikirim server diabaikan secara aman oleh client lama.
```

**Kesimpulan**: Protobuf memakai nomor field, bukan nama. Field yang tidak dikenali stub lama diabaikan secara aman (forward compatibility). Client baru yang membaca dari server lama akan menerima string kosong (`""`) karena proto3 menggunakan default value.

## L2.4 - Perbandingan ukuran pesan Protobuf vs XML-RPC

| Data | Protobuf | XML-RPC | Rasio |
| --- | ---: | ---: | ---: |
| GetMahasiswa response (Andi, IPK 3.26, Informatika) | 37 bytes | 432 bytes | 11.7x |
| TambahNilai request (Komputasi Paralel, 88) | 37 bytes | 396 bytes | 10.7x |
| tambah(5, 3) request | 4 bytes | 190 bytes | 47.5x |
| 4 nilai mata kuliah | 93 bytes | 911 bytes | 9.8x |

Protobuf menggunakan encoding biner (varint, length-delimited) sehingga ukurannya jauh lebih kecil. Overhead XML mencakup tag pembuka/penutup, deklarasi tipe, dan whitespace. Pada volume data besar atau frekuensi tinggi, perbedaan ini sangat berpengaruh terhadap bandwidth.

## L2.5 - Client asinkron dengan future

10 request `GetMahasiswa` dikirim secara asinkron menggunakan `stub.GetMahasiswa.future()`:

```
Semua 10 request dikirim dalam 15.2 ms.
Sukses: 9, Gagal: 1 (NIM 9999999: NOT_FOUND)
Waktu total: 28.9 ms
Rata-rata: 2.9 ms/request
```

Karena request non-blocking, seluruh request dikirim hampir bersamaan. Waktu total mendekati waktu satu request, bukan 10x lipat seperti panggilan sinkron berurutan.

## File yang ditambahkan/diubah

- `praktikum2/akademik.proto` (ditambah `Diskusi` RPC, `Pesan` message, field `prodi`)
- `praktikum2/akademik_pb2.py` (regenerated)
- `praktikum2/akademik_pb2_grpc.py` (regenerated)
- `praktikum2/server_grpc.py` (ditambah `Diskusi`, `prodi`, perbaikan data)
- `praktikum2/client_grpc.py` (ditambah demo L2.2 dan tampilan prodi)
- `praktikum2/test_backward_compat.py` (L2.3)
- `praktikum2/compare_message_size.py` (L2.4)
- `praktikum2/client_async.py` (L2.5)
- `praktikum2/old_stubs/` (salinan stub lama untuk L2.3)
