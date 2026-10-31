# Validasi Praktikum 2 - Lengkap

## Lingkungan uji

- Tanggal: 31 Oktober 2026 (Asia/Jakarta).
- Interpreter: Python 3.14.7 64-bit dalam `.venv/`.
- Dependensi: `grpcio 1.85.1`, `grpcio-tools 1.85.1`, dan `protobuf 7.36.2`.
- Host: `127.0.0.1`.
- Port pengujian: `50051`.

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
  ipk  : 3.26
  prodi: (field tidak ada pada stub lama - ini yang diharapkan)

[BUKTI] Client dengan stub lama berhasil memanggil server baru.
Field 'prodi' yang dikirim server diabaikan secara aman oleh client lama.
```

**Kesimpulan**: Protobuf memakai nomor field, bukan nama. Field yang tidak dikenali stub lama diabaikan secara aman (forward compatibility). Client baru yang membaca dari server lama akan menerima string kosong (`""`) karena proto3 menggunakan default value.

## L2.4 - Perbandingan ukuran pesan Protobuf vs XML-RPC

| Data | Protobuf | XML-RPC | Rasio |
| --- | ---: | ---: | ---: |
| GetMahasiswa response (Andi, IPK 3.26, Informatika) | 37 byte | 432 byte | 11.7x |
| TambahNilai request (Komputasi Paralel, 88) | 37 byte | 396 byte | 10.7x |
| tambah(5, 3) request | 4 byte | 190 byte | 47.5x |
| 4 pesan `Nilai` vs 4 respons XML-RPC terpisah | 93 byte | 1145 byte | 12.3x |

Metode pengukuran:

- Yang dibandingkan adalah payload serialisasi aplikasi, bukan paket jaringan.
- Header HTTP/1.1 dan framing HTTP/2 + prefix 5 byte per pesan gRPC tidak dihitung untuk kedua sisi.
- XML-RPC menyertakan envelope `methodCall`/`methodResponse`; Protobuf hanya message biner.
- Data keempat membandingkan 4 pesan Protobuf dengan 4 respons XML-RPC terpisah, bukan 4 pesan melawan satu array XML-RPC.
- Untuk `tambah(5, 3)` tidak ada RPC di `akademik.proto`; sisi Protobuf memakai ilustrasi manual dua varint dan diberi catatan eksplisit.

Protobuf menggunakan encoding biner (varint, length-delimited) sehingga payload yang diuji lebih kecil. Overhead XML mencakup tag, deklarasi tipe, dan envelope. Karena framing tidak dihitung, hasil ini tidak boleh dipakai sebagai klaim ukuran paket di jaringan.

## L2.5 - Client asinkron dengan future

10 request `GetMahasiswa` dikirim secara asinkron menggunakan `stub.GetMahasiswa.future()`. Waktu selesai setiap request dicatat melalui callback, sehingga latency individual tidak dicampur dengan wall-clock total.

Hasil aktual (server `127.0.0.1:50051`, 10 request, 1 request sengaja `NOT_FOUND`):

```
Total request      : 10
Sukses / gagal     : 9 / 1
Wall clock total   : 14.6 ms
Fase submit        : 5.8 ms
Latency individual : min 4.3 ms | mean 8.4 ms | median 9.1 ms | p95 12.1 ms | max 12.1 ms
Throughput         : 683.9 request/detik
Concurrency factor : 5.71x
Jika serial        : sekitar 83.5 ms (jumlah latency individual)
```

- **Latency individual** = submit sampai future selesai; bukan `wall-clock / jumlah request`.
- **Throughput** = jumlah request / wall-clock total.
- **Concurrency factor** = jumlah latency individual / wall-clock total. Nilai 1.0 berarti serial, nilai mendekati 10 berarti pekerjaan saling tumpang tindih. Angka ini adalah indikator overlap, bukan jumlah thread aktif.
- Latency request gagal tetap dihitung karena future tetap selesai.
- Persentil memakai nearest-rank, konsisten dengan benchmark L3.4.

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
