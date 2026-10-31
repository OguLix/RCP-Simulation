# Rencana Pengerjaan Bagian Individu

Status legend: `[ ]` belum dikerjakan, `[-]` sedang dikerjakan, `[~]` selesai namun belum tervalidasi, `[x]` selesai dan tervalidasi.

## Fondasi proyek

- [x] Buat virtual environment dan `requirements.txt`.
- [x] Buat `README.md` root berisi setup umum.
- [x] Buat struktur folder tiga praktikum (`praktikum1/`, `praktikum2/`, `praktikum3/` lengkap).

## Praktikum 1 - XML-RPC

- [x] Server dan client kalkulator dasar berjalan.
- [x] L1.1 `pangkat` dan `akar`.
- [x] L1.2 `statistik`.
- [x] L1.3 `datetime` dan integer besar.
- [~] L1.4 pengukuran RPC vs panggilan lokal (benchmark localhost tervalidasi; **uji dua komputer fisik belum dilakukan**).
- [x] L1.5 error ketika server mati.
- [x] Bukti XML request/response dan analisis ukuran pesan.
- [x] Dokumentasi di README root serta hasil pengujian Praktikum 1.

## Praktikum 2 - gRPC + Protobuf

- [x] Proto dasar, stub, server, dan client unary/server-streaming.
- [x] L2.1 client streaming.
- [x] L2.2 bidirectional streaming.
- [x] L2.3 backward compatibility.
- [x] L2.4 perbandingan ukuran pesan.
- [x] L2.5 client asinkron.
- [x] Dokumentasi di README root serta hasil pengujian Praktikum 2.

## Praktikum 3 - concurrency dan failure tolerance

- [x] RPC `Transfer`, saldo, dan deduplikasi `request_id`.
- [x] Client timeout/retry dengan exponential backoff.
- [x] L3.1 transfer berulang (20x transfer, saldo total konsisten 1500).
- [x] L3.2 demonstrasi UUID baru dan transfer ganda vs idempotensi.
- [x] L3.3 concurrency 50 transfer serta pembuktian race condition tanpa lock dengan barrier terkontrol.
- [x] L3.4 benchmark 200 req dari 20 client, tabel dan grafik throughput/latensi.
- [x] L3.5 failover dua server serta pembuktian double execution lintas server dan hilangnya cache setelah restart.
- [x] Dokumentasi di README root serta hasil pengujian Praktikum 3.

## Penutupan

- [x] Review seluruh instruksi, kode, dan bukti hasil.
- [x] Seluruh artefak kode, README, dan laporan validasi siap untuk laporan praktikum; satu-satunya butir yang masih menunggu eksekusi manual adalah L1.4 lintas komputer.
