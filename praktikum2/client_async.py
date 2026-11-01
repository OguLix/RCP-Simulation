"""Praktikum RPC - Komputasi Paralel dan Terdistribusi

Nama : Muhammad Fadhlan Aminullah
NPM  : 247006111151

L2.5: client asinkron menggunakan gRPC future untuk 10 panggilan konkuren.

Skrip ini mengirim 10 GetMahasiswa request secara asinkron menggunakan
stub.GetMahasiswa.future(), lalu mengumpulkan seluruh hasilnya. Untuk setiap
request dicatat waktu submit dan waktu selesai agar latency individual dapat
dipisahkan dari total wall-clock dan throughput.
"""

from __future__ import annotations

import argparse
import math
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

import grpc

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc


NIMS_TO_QUERY = [
    "2023001", "2023002", "2023001", "2023002", "2023001",
    "2023002", "2023001", "2023002", "9999999", "2023001",
]


def percentile_nearest_rank(values: list[float], p: float) -> float:
    """Percentile nearest-rank: indeks ceil(p * n) - 1 pada data terurut."""
    if not values:
        raise ValueError("values tidak boleh kosong.")
    if not 0 < p <= 1:
        raise ValueError("p harus berada pada (0, 1].")
    ordered = sorted(values)
    rank = math.ceil(p * len(ordered))
    return ordered[min(max(rank - 1, 0), len(ordered) - 1)]


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
    parser = argparse.ArgumentParser(description="L2.5: client asinkron dengan future.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=50051, type=int)
    args = parser.parse_args()

    tampilkan_header("PRAKTIKUM 2.5 - IMPLEMENTASI ASYNCHRONOUS RPC", "Client")
    print("=== L2.5: Client Asinkron dengan gRPC Future ===")
    print(f"Mengirim {len(NIMS_TO_QUERY)} GetMahasiswa request secara asinkron.\n")

    with grpc.insecure_channel(f"{args.host}:{args.port}") as channel:
        stub = pb_grpc.LayananNilaiStub(channel)

        records: list[dict[str, object]] = []
        wall_start = time.perf_counter()
        submit_start = wall_start
        for i, nim in enumerate(NIMS_TO_QUERY):
            submit_time = time.perf_counter()
            future = stub.GetMahasiswa.future(
                pb.MahasiswaRequest(nim=nim),
                timeout=5,
            )
            record: dict[str, object] = {
                "index": i,
                "nim": nim,
                "future": future,
                "submit": submit_time,
                "finish": None,
            }
            # Callback memberi waktu selesai saat future benar-benar selesai,
            # bukan saat hasilnya diambil satu per satu.
            future.add_done_callback(
                lambda _future, item=record: item.__setitem__("finish", time.perf_counter())
            )
            records.append(record)
            print(f"  [{i}] Request dikirim untuk NIM {nim}")

        submit_elapsed_ms = (time.perf_counter() - submit_start) * 1000
        print(f"\nSemua {len(records)} request dikirim dalam {submit_elapsed_ms:.1f} ms.")
        print("Mengumpulkan hasil...\n")

        sukses = 0
        gagal = 0
        latencies_ms: list[float] = []
        for record in records:
            i = int(record["index"])
            nim = str(record["nim"])
            future = record["future"]
            try:
                result = future.result()
                print(f"  [{i}] NIM {nim}: {result.nama} - IPK {result.ipk:.2f} - Prodi: {result.prodi}")
                sukses += 1
            except grpc.RpcError as error:
                print(f"  [{i}] NIM {nim}: {error.code().name} - {error.details()}")
                gagal += 1

            finish_time = record["finish"]
            if finish_time is None:
                finish_time = time.perf_counter()
                record["finish"] = finish_time
            latencies_ms.append((float(finish_time) - float(record["submit"])) * 1000)

        wall_elapsed_ms = (time.perf_counter() - wall_start) * 1000
        throughput = len(records) / (wall_elapsed_ms / 1000)
        total_latency_ms = sum(latencies_ms)
        concurrency_factor = total_latency_ms / wall_elapsed_ms if wall_elapsed_ms > 0 else 0.0

        print("\n--- Ringkasan ---")
        print(f"Total request      : {len(records)}")
        print(f"Sukses / gagal     : {sukses} / {gagal}")
        print(f"Wall clock total   : {wall_elapsed_ms:.1f} ms")
        print(f"Fase submit        : {submit_elapsed_ms:.1f} ms")
        print("Latency individual : "
              f"min {min(latencies_ms):.1f} ms | "
              f"mean {statistics.mean(latencies_ms):.1f} ms | "
              f"median {statistics.median(latencies_ms):.1f} ms | "
              f"p95 {percentile_nearest_rank(latencies_ms, 0.95):.1f} ms | "
              f"max {max(latencies_ms):.1f} ms")
        print(f"Throughput         : {throughput:.1f} request/detik")
        print(f"Concurrency factor : {concurrency_factor:.2f}x")
        print(f"Jika serial        : sekitar {total_latency_ms:.1f} ms (jumlah latency individual)")
        print()
        print("Catatan:")
        print("- Latency individual diukur dari submit sampai future selesai, bukan")
        print("  wall-clock total dan bukan waktu pengambilan hasil.")
        print("- Throughput = jumlah request / wall-clock total.")
        print("- Concurrency factor = jumlah latency individual / wall-clock total.")
        print("  Nilai mendekati jumlah request berarti pekerjaan saling tumpang tindih;")
        print("  angka ini bukan jumlah thread yang aktif pada satu waktu.")
        print("- Latency request gagal tetap dihitung karena future tetap selesai.")


if __name__ == "__main__":
    main()
