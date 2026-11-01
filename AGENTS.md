# Panduan Pengerjaan Praktikum RPC (Individu)

## Tujuan dan batasan

Repositori ini dipakai untuk menyelesaikan **bagian praktikum individu** mata kuliah Komputasi Paralel dan Terdistribusi (KPT), yaitu Praktikum 1 sampai Praktikum 3. Tugas proyek mini kelompok berada di luar ruang lingkup sampai pengguna meminta sebaliknya.

Target akhir:

1. Semua butir L1.x, L2.x, dan L3.x dapat dijalankan dan dibuktikan.
2. Kode mempunyai instruksi eksekusi yang dapat diulang pada Windows.
3. Bukti pengukuran, jawaban analisis, dan progres tersedia di `docs/`.

## Struktur yang dipakai

```text
.
├── praktikum1/             # XML-RPC
├── praktikum2/             # gRPC + Protocol Buffers
├── praktikum3/             # Concurrency, retry, failover
├── docs/
│   ├── PROGRESS.md         # status aktual dan langkah berikutnya
│   ├── PLAN.md             # checklist kebutuhan tugas
│   └── reports/            # hasil ukur, jawaban analisis, tangkapan layar
├── requirements.txt
└── README.md
```

Jangan membuat kode praktikum pada root. Panduan eksekusi seluruh praktikum dipusatkan di `README.md` root.

## Urutan kerja wajib

1. Kerjakan Praktikum 1 sepenuhnya sebelum memulai Praktikum 2.
2. Kerjakan Praktikum 2 sepenuhnya sebelum memulai Praktikum 3.
3. Untuk setiap butir latihan: implementasikan, jalankan, simpan bukti hasil, lalu perbarui `docs/PROGRESS.md`.
4. Jangan menandai butir selesai hanya karena kode sudah ditulis; status selesai membutuhkan eksekusi yang berhasil dan bukti/hasil yang relevan.
5. Setelah satu praktikum selesai, lakukan review ringkas terhadap checklist dan dokumentasikan keterbatasan yang tersisa.

## Konvensi implementasi

- Gunakan Python 3.10+.
- Gunakan virtual environment `.venv`; jangan commit `.venv/`.
- Dependensi Python dicatat di `requirements.txt` dengan versi yang kompatibel.
- Gunakan `localhost` sebagai default; alamat host dan port harus mudah dikonfigurasi melalui argumen CLI atau konstanta yang jelas.
- Hindari state tersembunyi. State layanan, port, timeout, dan jumlah worker perlu tampak jelas di kode.
- Tulis pesan error yang menjelaskan penyebab serta kode status gRPC jika berlaku.
- Gunakan nama file dan API berbahasa Inggris, sementara dokumentasi boleh berbahasa Indonesia.

## Kebutuhan per praktikum

### Praktikum 1 - XML-RPC

- Server kalkulator dengan `tambah`, `kali`, dan `bagi`; pembagian nol menghasilkan fault yang ditangani client.
- Implementasikan L1.1 fungsi `pangkat(a, b)` dan `akar(x)`.
- Implementasikan L1.2 `statistik(daftar)` yang mengembalikan `min`, `max`, dan `rata2`.
- L1.3: uji `datetime` dan integer di atas `2^31`; dokumentasikan perilakunya.
- L1.4: ukur 100 panggilan RPC `tambah` dan 100 panggilan lokal memakai `time.perf_counter()`.
- L1.5: dokumentasikan perilaku saat server berhenti dan tangani error pada client.
- Simpan contoh request/response XML serta analisis ukuran pesan `tambah(5, 3)`.

### Praktikum 2 - gRPC dan Protobuf

- Mulai dari kontrak `akademik.proto` dengan unary `GetMahasiswa`, unary `TambahNilai`, dan server streaming `StreamNilai`.
- Generate stub ke direktori praktikum; file hasil generate tidak diedit manual.
- Implementasikan error `NOT_FOUND` dan `INVALID_ARGUMENT` serta uji dari client.
- L2.1: tambah client streaming `KirimBanyakNilai`.
- L2.2: tambah bidirectional streaming `Diskusi`.
- L2.3: tambah field `prodi = 4`, kemudian buktikan backward compatibility dengan client stub lama.
- L2.4: ukur ukuran serialisasi Protobuf dan bandingkan dengan XML-RPC untuk data setara.
- L2.5: jalankan 10 unary call asinkron dengan future dan kumpulkan hasilnya.

### Praktikum 3 - Concurrency, timeout, dan toleransi kegagalan

- Tambah RPC `Transfer` pada `.proto` dengan `request_id`, pengirim, penerima, dan jumlah.
- Lindungi saldo dan cache deduplikasi dengan locking yang benar; respons untuk `request_id` duplikat harus identik.
- Client retry menggunakan ID yang sama untuk seluruh percobaan dan exponential backoff.
- L3.1: 20 transfer A ke B, saldo total harus tetap 1500 dan A berkurang tepat 200.
- L3.2: tunjukkan efek ID baru di setiap retry dan jelaskan transfer ganda.
- L3.3: uji 50 transfer dari 10 client secara bersamaan, lalu jelaskan race condition jika lock dihilangkan.
- L3.4: ukur 200 `GetMahasiswa` dari 20 client pada `max_workers` 1, 4, dan 10; hasilkan tabel dan grafik.
- L3.5: jalankan dua server pada port 50051 dan 50052; client melakukan failover saat server utama tidak tersedia.
- Jawab dampak restart server terhadap deduplikasi in-memory dan usulkan penyimpanan persisten.

## Verifikasi minimum

- Jalankan formatter/linter bila dikonfigurasi.
- Jalankan server dan client pada terminal terpisah untuk setiap praktikum.
- Uji jalur sukses dan error.
- Untuk perubahan `.proto`, regenerate stub lalu pastikan client dan server memakai stub baru yang sesuai.
- Untuk concurrency, jalankan pengujian berulang agar hasil tidak kebetulan.
- Untuk pengukuran, catat mesin/kondisi uji, parameter, jumlah sampel, satuan, dan hasil mentah atau ringkasannya.

## Protokol pembaruan progres

Setelah pekerjaan bermakna selesai, perbarui `docs/PROGRESS.md` pada bagian berikut:

1. `Status saat ini` dan timestamp.
2. Checklist butir yang berubah.
3. Bukti validasi yang baru dijalankan beserta hasil singkat.
4. File yang ditambah/diubah.
5. Langkah berikutnya yang paling konkret.
6. Risiko, blocker, atau keputusan teknis bila ada.

Dokumen progres harus membedakan jelas antara **selesai dan tervalidasi**, **selesai namun belum divalidasi**, dan **belum dikerjakan**.
