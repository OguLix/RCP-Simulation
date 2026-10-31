"""Client demonstrasi unary, streaming, bidirectional, dan gRPC status codes."""

from __future__ import annotations

import argparse

import grpc

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc


def bulk_requests():
    """Generator L2.1 agar nilai dikirim sebagai client stream, bukan list unary."""
    for matkul, nilai in (
        ("Sistem Terdistribusi", 90),
        ("Rekayasa Perangkat Lunak", 86),
        ("Keamanan Informasi", 91),
    ):
        yield pb.NilaiRequest(nim="2023002", matkul=matkul, nilai=nilai)


def diskusi_messages():
    """Generator L2.2: mengirim beberapa pesan diskusi ke server."""
    pesan_list = [
        ("Mahasiswa", "Halo, saya ingin bertanya."),
        ("Mahasiswa", "Bagaimana cara melihat nilai saya?"),
        ("Mahasiswa", "Terima kasih atas informasinya."),
    ]
    for pengirim, isi in pesan_list:
        yield pb.Pesan(pengirim=pengirim, isi=isi)


def run_demo(host: str, port: int) -> None:
    with grpc.insecure_channel(f"{host}:{port}") as channel:
        stub = pb_grpc.LayananNilaiStub(channel)

        # --- Unary: GetMahasiswa (termasuk field prodi) ---
        mahasiswa = stub.GetMahasiswa(pb.MahasiswaRequest(nim="2023001"), timeout=3)
        print(f"{mahasiswa.nama} ({mahasiswa.nim}) - IPK {mahasiswa.ipk:.2f} - Prodi: {mahasiswa.prodi}")

        # --- Unary: TambahNilai ---
        status = stub.TambahNilai(
            pb.NilaiRequest(nim="2023001", matkul="Komputasi Paralel", nilai=88),
            timeout=3,
        )
        print(status.pesan)

        # --- Client streaming L2.1: KirimBanyakNilai ---
        bulk_status = stub.KirimBanyakNilai(bulk_requests(), timeout=3)
        print(f"L2.1: {bulk_status.pesan} (jumlah={bulk_status.jumlah_disimpan})")

        # --- Server streaming: StreamNilai ---
        print("Daftar nilai 2023001:")
        for nilai in stub.StreamNilai(pb.MahasiswaRequest(nim="2023001"), timeout=3):
            print(f"- {nilai.matkul}: {nilai.nilai:g}")

        print("Nilai 2023002 setelah client streaming:")
        for nilai in stub.StreamNilai(pb.MahasiswaRequest(nim="2023002"), timeout=3):
            print(f"- {nilai.matkul}: {nilai.nilai:g}")

        # --- Bidirectional streaming L2.2: Diskusi ---
        print("\n--- L2.2: Bidirectional streaming Diskusi ---")
        responses = stub.Diskusi(diskusi_messages(), timeout=5)
        for response in responses:
            print(f"[{response.pengirim}]: {response.isi}")

        # --- Error handling ---
        for label, request in (
            ("NIM tidak ada", pb.MahasiswaRequest(nim="9999999")),
            ("nilai tidak valid", pb.NilaiRequest(nim="2023001", matkul="Tes", nilai=101)),
        ):
            try:
                if isinstance(request, pb.MahasiswaRequest):
                    stub.GetMahasiswa(request, timeout=3)
                else:
                    stub.TambahNilai(request, timeout=3)
            except grpc.RpcError as error:
                print(f"{label}: {error.code().name} - {error.details()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Menjalankan client gRPC akademik.")
    parser.add_argument("--host", default="127.0.0.1", help="Host server (default: 127.0.0.1).")
    parser.add_argument("--port", default=50051, type=int, help="Port gRPC (default: 50051).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        run_demo(args.host, args.port)
    except grpc.RpcError as error:
        print(f"gRPC gagal: {error.code().name} - {error.details()}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
