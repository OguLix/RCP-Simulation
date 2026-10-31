# Runbook Praktikum 2 - gRPC dan Protocol Buffers

## Prasyarat

- Python 3.10 atau lebih baru.
- Dependensi: `grpcio`, `grpcio-tools` (tercatat di `requirements.txt`).

## Menyiapkan dependensi dan generated stub

Dari root repositori:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m grpc_tools.protoc -I praktikum2 --python_out=praktikum2 --grpc_python_out=praktikum2 praktikum2/akademik.proto
```

Jangan mengubah `akademik_pb2.py` atau `akademik_pb2_grpc.py` secara manual. Ulangi perintah generator setiap kali `akademik.proto` berubah.

## Menjalankan server dan client dasar

Buka dua terminal dari root repositori.

Terminal 1:

```powershell
.venv\Scripts\python.exe praktikum2\server_grpc.py
```

Terminal 2:

```powershell
.venv\Scripts\python.exe praktikum2\client_grpc.py
```

Client mendemonstrasikan:
- `GetMahasiswa` (unary, sekarang dengan field `prodi`).
- `TambahNilai` (unary).
- `KirimBanyakNilai` (L2.1 client streaming).
- `StreamNilai` (server streaming).
- `Diskusi` (L2.2 bidirectional streaming).
- Penanganan error `NOT_FOUND` dan `INVALID_ARGUMENT`.

## L2.2 - Bidirectional streaming Diskusi

Sudah terintegrasi di `client_grpc.py`. Client mengirim 3 pesan diskusi dan server membalas masing-masing secara streaming.

## L2.3 - Backward compatibility

Stub lama (tanpa field `prodi`) tersimpan di `praktikum2/old_stubs/`. Jalankan pengujian dengan server aktif:

```powershell
.venv\Scripts\python.exe praktikum2\test_backward_compat.py --port 50051
```

Skrip ini mengimpor stub lama dan memanggil server baru, membuktikan bahwa field baru tidak merusak client lama.

## L2.4 - Perbandingan ukuran pesan

Skrip ini tidak memerlukan server yang berjalan:

```powershell
.venv\Scripts\python.exe praktikum2\compare_message_size.py
```

Membandingkan ukuran serialisasi Protobuf vs XML-RPC untuk beberapa tipe data (mahasiswa, nilai, tambah(5,3)).

## L2.5 - Client asinkron dengan future

Dengan server aktif:

```powershell
.venv\Scripts\python.exe praktikum2\client_async.py --port 50051
```

Mengirim 10 `GetMahasiswa` secara asinkron menggunakan `stub.GetMahasiswa.future()` dan mengumpulkan hasilnya, termasuk satu NIM invalid untuk menguji error handling.

## Opsi CLI

### Server

| Argumen | Default | Keterangan |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Host bind |
| `--port` | `50051` | Port gRPC |
| `--max-workers` | `10` | Jumlah thread worker |

### Client

| Argumen | Default | Keterangan |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Host server |
| `--port` | `50051` | Port gRPC |
