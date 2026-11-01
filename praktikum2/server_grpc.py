"""Praktikum RPC - Komputasi Paralel dan Terdistribusi

Nama : Muhammad Fadhlan Aminullah
NPM  : 247006111151

Server gRPC akademik: unary, server streaming, client streaming, dan bidirectional."""

from __future__ import annotations

import argparse
import queue
import threading
import time
from concurrent import futures

import grpc

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc


INITIAL_DATA: dict[str, dict[str, object]] = {
    "2023001": {"nama": "Andi", "prodi": "Informatika", "nilai": {"Basis Data": 85.0, "Jaringan": 78.0}},
    "2023002": {"nama": "Sari", "prodi": "Sistem Informasi", "nilai": {"Basis Data": 92.0}},
}


class LayananNilai(pb_grpc.LayananNilaiServicer):
    """Implementasi unary, streaming, dan bidirectional dari kontrak akademik.proto."""

    def __init__(self, initial_data: dict[str, dict[str, object]] | None = None) -> None:
        source = initial_data if initial_data is not None else INITIAL_DATA
        self._data = {
            nim: {
                "nama": record["nama"],
                "prodi": record.get("prodi", ""),
                "nilai": dict(record["nilai"]),
            }
            for nim, record in source.items()
        }
        self._lock = threading.RLock()

    def _get_mahasiswa(self, nim: str, context: grpc.ServicerContext) -> dict[str, object]:
        with self._lock:
            mahasiswa = self._data.get(nim)
            if mahasiswa is None:
                context.abort(grpc.StatusCode.NOT_FOUND, f"NIM {nim} tidak ditemukan.")
            return mahasiswa

    @staticmethod
    def _calculate_ipk(nilai: dict[str, float]) -> float:
        if not nilai:
            return 0.0
        return round(sum(nilai.values()) / len(nilai) / 25, 2)

    @staticmethod
    def _validate_nilai_request(request: pb.NilaiRequest, context: grpc.ServicerContext) -> None:
        if not request.nim.strip() or not request.matkul.strip():
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "NIM dan matkul wajib diisi.")
        if not 0 <= request.nilai <= 100:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Nilai harus berada pada rentang 0-100.")

    def GetMahasiswa(self, request: pb.MahasiswaRequest, context: grpc.ServicerContext) -> pb.Mahasiswa:
        mahasiswa = self._get_mahasiswa(request.nim, context)
        nilai = mahasiswa["nilai"]
        return pb.Mahasiswa(
            nim=request.nim,
            nama=str(mahasiswa["nama"]),
            ipk=self._calculate_ipk(nilai),
            prodi=str(mahasiswa.get("prodi", "")),
        )

    def TambahNilai(self, request: pb.NilaiRequest, context: grpc.ServicerContext) -> pb.StatusResponse:
        self._validate_nilai_request(request, context)

        with self._lock:
            mahasiswa = self._data.setdefault(request.nim, {"nama": "(baru)", "prodi": "", "nilai": {}})
            nilai = mahasiswa["nilai"]
            nilai[request.matkul] = request.nilai
        return pb.StatusResponse(sukses=True, pesan="Nilai tersimpan.", jumlah_disimpan=1)

    def StreamNilai(self, request: pb.MahasiswaRequest, context: grpc.ServicerContext):
        mahasiswa = self._get_mahasiswa(request.nim, context)
        with self._lock:
            nilai_items = list(mahasiswa["nilai"].items())
        for matkul, nilai in nilai_items:
            yield pb.Nilai(matkul=matkul, nilai=nilai)
            time.sleep(0.1)

    def KirimBanyakNilai(self, request_iterator, context: grpc.ServicerContext) -> pb.StatusResponse:
        """L2.1: validasi seluruh stream sebelum menyimpan agar tidak parsial."""
        requests = list(request_iterator)
        if not requests:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Stream nilai tidak boleh kosong.")
        for request in requests:
            self._validate_nilai_request(request, context)

        with self._lock:
            for request in requests:
                mahasiswa = self._data.setdefault(request.nim, {"nama": "(baru)", "prodi": "", "nilai": {}})
                nilai = mahasiswa["nilai"]
                nilai[request.matkul] = request.nilai
        return pb.StatusResponse(
            sukses=True,
            pesan=f"{len(requests)} nilai tersimpan.",
            jumlah_disimpan=len(requests),
        )

    def Diskusi(self, request_iterator, context: grpc.ServicerContext):
        """L2.2: bidirectional streaming - server merespons setiap pesan client."""
        for pesan in request_iterator:
            balasan = self._buat_balasan(pesan)
            yield pb.Pesan(pengirim="Server", isi=balasan)

    @staticmethod
    def _buat_balasan(pesan: pb.Pesan) -> str:
        """Menghasilkan balasan sederhana berdasarkan isi pesan client."""
        isi_lower = pesan.isi.lower()
        if "halo" in isi_lower or "hai" in isi_lower:
            return f"Halo juga, {pesan.pengirim}! Ada yang bisa dibantu?"
        if "nilai" in isi_lower:
            return "Silakan gunakan RPC GetMahasiswa atau StreamNilai untuk mengakses data nilai."
        if "terima kasih" in isi_lower:
            return f"Sama-sama, {pesan.pengirim}! Senang bisa membantu."
        return f"Pesan dari {pesan.pengirim} diterima: '{pesan.isi}'"


def build_server(host: str, port: int, max_workers: int = 10) -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    pb_grpc.add_LayananNilaiServicer_to_server(LayananNilai(), server)
    server.add_insecure_port(f"{host}:{port}")
    return server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Menjalankan server gRPC akademik.")
    parser.add_argument("--host", default="127.0.0.1", help="Host bind (default: 127.0.0.1).")
    parser.add_argument("--port", default=50051, type=int, help="Port gRPC (default: 50051).")
    parser.add_argument("--max-workers", default=10, type=int, help="Jumlah worker server (default: 10).")
    return parser.parse_args()


def tampilkan_header(judul: str, peran: str | None = None) -> None:
    print("=" * 60)
    print(judul)
    print("Mata Kuliah : Komputasi Paralel dan Terdistribusi")
    print("Nama        : Muhammad Fadhlan Aminullah")
    print("NPM         : 247006111151")
    if peran:
        print(f"Peran       : {peran}")
    print("=" * 60)


def main() -> None:
    args = parse_args()
    tampilkan_header("PRAKTIKUM 2 - SERVER gRPC AKADEMIK (L2.1-L2.5)", "Server")
    server = build_server(args.host, args.port, args.max_workers)
    server.start()
    print(f"Server gRPC berjalan di {args.host}:{args.port} (max_workers={args.max_workers}).")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
        server.stop(grace=0)


if __name__ == "__main__":
    main()
