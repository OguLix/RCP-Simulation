# Validasi Fondasi Praktikum 2

## Lingkungan uji

- Tanggal: 31 Oktober 2026 (Asia/Jakarta).
- Interpreter: Python 3.14.7 64-bit dalam `.venv/`.
- Dependensi: `grpcio 1.85.1`, `grpcio-tools 1.85.1`, dan `protobuf 7.36.2`.
- Host: `127.0.0.1`.
- Port pengujian: `50061` (bukan port default, agar tidak berbenturan dengan proses lain).

## Generated stub

Perintah berikut berhasil dijalankan:

```powershell
.venv\Scripts\python.exe -m grpc_tools.protoc -I praktikum2 --python_out=praktikum2 --grpc_python_out=praktikum2 praktikum2\akademik.proto
```

Generator menghasilkan `akademik_pb2.py` dan `akademik_pb2_grpc.py` pada `praktikum2/`.

## Hasil integrasi

| Skenario | Hasil |
| --- | --- |
| `GetMahasiswa(2023001)` | `Andi (2023001) - IPK 3.26` |
| `TambahNilai(2023001, Komputasi Paralel, 88)` | `Nilai tersimpan.` |
| `StreamNilai(2023001)` | Mengalirkan Basis Data 85, Jaringan 78, dan Komputasi Paralel 88. |
| `GetMahasiswa(9999999)` | `NOT_FOUND` dengan pesan NIM tidak ditemukan. |
| `TambahNilai(..., nilai=101)` | `INVALID_ARGUMENT` dengan pesan nilai harus 0-100. |

## L2.1 - client streaming `KirimBanyakNilai`

Kontrak menambahkan `rpc KirimBanyakNilai(stream NilaiRequest) returns (StatusResponse)`. Field `jumlah_disimpan = 3` juga ditambahkan pada `StatusResponse`, sehingga server dapat mengembalikan jumlah pesan yang berhasil disimpan tanpa mengubah field lama.

Client mengirim satu stream berisi tiga nilai untuk NIM `2023002`:

| Mata kuliah | Nilai |
| --- | ---: |
| Sistem Terdistribusi | 90 |
| Rekayasa Perangkat Lunak | 86 |
| Keamanan Informasi | 91 |

Hasil server: `3 nilai tersimpan.` dengan `jumlah_disimpan=3`. Pemanggilan `StreamNilai(2023002)` setelahnya mengembalikan ketiga nilai tersebut, di samping nilai awal Basis Data 92.

Server menampung stream terlebih dahulu, memvalidasi seluruh pesan, lalu menyimpannya dalam satu critical section. Dengan demikian stream kosong atau pesan invalid ditolak tanpa menyisakan penyimpanan parsial.

## Status akhir

Kontrak dasar, generated stub, server, client, unary RPC, server streaming, dua status error, dan L2.1 client streaming sudah tervalidasi. Butir L2.2-L2.5 kemudian divalidasi pada [praktikum2-validation.md](praktikum2-validation.md).
