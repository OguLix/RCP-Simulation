"""L2.5: Client asinkron menggunakan gRPC future untuk 10 panggilan konkuren.

Skrip ini mengirim 10 GetMahasiswa request secara asinkron menggunakan
stub.GetMahasiswa.future(), lalu mengumpulkan seluruh hasilnya.
Server harus berjalan sebelum skrip ini dijalankan.
"""

from __future__ import annotations

import argparse
import time
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import grpc

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc


NIMS_TO_QUERY = [
    "2023001", "2023002", "2023001", "2023002", "2023001",
    "2023002", "2023001", "2023002", "9999999", "2023001",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="L2.5: client asinkron dengan future.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=50051, type=int)
    args = parser.parse_args()

    print("=== L2.5: Client Asinkron dengan gRPC Future ===")
    print(f"Mengirim {len(NIMS_TO_QUERY)} GetMahasiswa request secara asinkron.\n")

    with grpc.insecure_channel(f"{args.host}:{args.port}") as channel:
        stub = pb_grpc.LayananNilaiStub(channel)

        # Kirim semua request secara asinkron.
        started_at = time.perf_counter()
        futures = []
        for i, nim in enumerate(NIMS_TO_QUERY):
            future = stub.GetMahasiswa.future(
                pb.MahasiswaRequest(nim=nim),
                timeout=5,
            )
            futures.append((i, nim, future))
            print(f"  [{i}] Request dikirim untuk NIM {nim}")

        elapsed_send = (time.perf_counter() - started_at) * 1000
        print(f"\nSemua {len(futures)} request dikirim dalam {elapsed_send:.1f} ms.")
        print("Mengumpulkan hasil...\n")

        # Kumpulkan hasil dari setiap future.
        sukses = 0
        gagal = 0
        for i, nim, future in futures:
            try:
                result = future.result()
                print(f"  [{i}] NIM {nim}: {result.nama} - IPK {result.ipk:.2f} - Prodi: {result.prodi}")
                sukses += 1
            except grpc.RpcError as error:
                print(f"  [{i}] NIM {nim}: {error.code().name} - {error.details()}")
                gagal += 1

        elapsed_total = (time.perf_counter() - started_at) * 1000
        print(f"\n--- Ringkasan ---")
        print(f"Total request : {len(futures)}")
        print(f"Sukses        : {sukses}")
        print(f"Gagal         : {gagal}")
        print(f"Waktu total   : {elapsed_total:.1f} ms")
        print(f"Rata-rata     : {elapsed_total / len(futures):.1f} ms/request")
        print()
        print("Catatan: Karena request dikirim sebagai future (non-blocking),")
        print("seluruh request terbang ke server hampir bersamaan. Waktu total")
        print("mendekati waktu satu request, bukan 10x lipat seperti sinkron.")


if __name__ == "__main__":
    main()
