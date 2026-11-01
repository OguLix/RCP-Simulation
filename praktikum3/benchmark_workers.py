"""Praktikum RPC - Komputasi Paralel dan Terdistribusi

Nama : Muhammad Fadhlan Aminullah
NPM  : 247006111151

Benchmark throughput dan latensi: 200 GetMahasiswa dari 20 client (L3.4).

Konfigurasi pengukuran:
- Total pemanggilan: 200 requests.
- Beban konkuren: 20 client threads (masing-masing 10 request).
- Delay server: time.sleep(0.1) ditambahkan di server (simulasi I/O / DB 100 ms).
- Variasi max_workers: 1, 4, dan 10 workers.

Percentile memakai metode nearest-rank: data diurutkan, lalu diambil indeks
ceil(p * n) - 1. Metode ini dipakai konsisten untuk P50, P95, dan P99.

Menghasilkan:
1. Tabel throughput dan statistik latensi (min, mean, P50, P95, P99, max).
2. Grafik visualisasi performa disimpan ke docs/reports/l3_4_throughput_latency.png dan praktikum3/.
"""

from __future__ import annotations

import concurrent.futures
import math
import os
import statistics
import sys
import time

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PRAKTIKUM2_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "praktikum2"))
REPORTS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "docs", "reports"))
sys.path.insert(0, PRAKTIKUM2_DIR)
sys.path.insert(0, CURRENT_DIR)

import grpc
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

import akademik_pb2 as pb
import akademik_pb2_grpc as pb_grpc
from server_grpc import LayananNilai

TOTAL_REQUESTS = 200
NUM_CLIENTS = 20
REQUESTS_PER_CLIENT = TOTAL_REQUESTS // NUM_CLIENTS  # 10
WORKER_CONFIGS = [1, 4, 10]
SIMULATED_DELAY = 0.1


def percentile_nearest_rank(values: list[float], p: float) -> float:
    """Percentile nearest-rank: indeks ceil(p * n) - 1 pada data terurut."""
    if not values:
        raise ValueError("values tidak boleh kosong.")
    if not 0 < p <= 1:
        raise ValueError("p harus berada pada (0, 1].")
    ordered = sorted(values)
    rank = math.ceil(p * len(ordered))
    return ordered[min(max(rank - 1, 0), len(ordered) - 1)]


class BenchmarkLayananNilai(LayananNilai):
    """LayananNilai dengan delay time.sleep(0.1) per request (L3.4)."""

    def __init__(self, delay_sec: float = SIMULATED_DELAY) -> None:
        super().__init__()
        self._delay_sec = delay_sec

    def GetMahasiswa(self, request: pb.MahasiswaRequest, context: grpc.ServicerContext) -> pb.Mahasiswa:
        if self._delay_sec > 0:
            time.sleep(self._delay_sec)
        return super().GetMahasiswa(request, context)


def run_benchmark_for_workers(max_workers: int, port: int) -> dict[str, float]:
    """Menjalankan server dengan max_workers tertentu dan mengukur 200 request dari 20 client."""
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=max_workers))
    pb_grpc.add_LayananNilaiServicer_to_server(BenchmarkLayananNilai(), server)
    server.add_insecure_port(f"127.0.0.1:{port}")
    server.start()

    latencies_ms: list[float] = []

    def client_task(client_id: int) -> list[float]:
        thread_latencies = []
        with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
            stub = pb_grpc.LayananNilaiStub(channel)
            nim_target = "2023001" if client_id % 2 == 0 else "2023002"
            for _ in range(REQUESTS_PER_CLIENT):
                t0 = time.perf_counter()
                res = stub.GetMahasiswa(pb.MahasiswaRequest(nim=nim_target), timeout=35.0)
                t1 = time.perf_counter()
                assert res.nim == nim_target
                thread_latencies.append((t1 - t0) * 1000.0)
        return thread_latencies

    try:
        t_start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_CLIENTS) as pool:
            futures_list = [pool.submit(client_task, i) for i in range(NUM_CLIENTS)]
            for fut in futures_list:
                latencies_ms.extend(fut.result())
        t_total = time.perf_counter() - t_start

        if len(latencies_ms) != TOTAL_REQUESTS:
            raise AssertionError(
                f"Jumlah sampel salah: {len(latencies_ms)} != {TOTAL_REQUESTS}"
            )

        throughput = len(latencies_ms) / t_total
        return {
            "workers": max_workers,
            "total_time_s": t_total,
            "throughput": throughput,
            "min_ms": min(latencies_ms),
            "mean_ms": statistics.mean(latencies_ms),
            "p50_ms": percentile_nearest_rank(latencies_ms, 0.50),
            "p95_ms": percentile_nearest_rank(latencies_ms, 0.95),
            "p99_ms": percentile_nearest_rank(latencies_ms, 0.99),
            "max_ms": max(latencies_ms),
        }
    finally:
        server.stop(grace=0)


def generate_plot(results: list[dict[str, float]], save_paths: list[str]) -> None:
    """Membuat visualisasi grafik throughput dan latensi."""
    workers = [str(r["workers"]) for r in results]
    throughputs = [r["throughput"] for r in results]
    means = [r["mean_ms"] for r in results]
    p95s = [r["p95_ms"] for r in results]
    p99s = [r["p99_ms"] for r in results]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.0))

    # Plot Throughput
    bars1 = ax1.bar(workers, throughputs, color="#2b5c8f", width=0.45)
    ax1.set_title("Throughput vs Server Workers\n(200 req / 20 client, sleep=0.1s)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("max_workers", fontsize=10)
    ax1.set_ylabel("Throughput (req / detik)", fontsize=10)
    ax1.grid(axis="y", linestyle="--", alpha=0.6)
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2.0, yval + 1.5, f"{yval:.1f}",
                 ha="center", va="bottom", fontsize=9, fontweight="bold")

    # Plot Latency (Mean, P95, P99)
    import numpy as np
    x = np.arange(len(workers))
    width = 0.25
    bars_mean = ax2.bar(x - width, means, width, label="Mean", color="#e67e22")
    bars_p95 = ax2.bar(x, p95s, width, label="P95", color="#c0392b")
    bars_p99 = ax2.bar(x + width, p99s, width, label="P99", color="#7d3c98")
    ax2.set_title("Latensi vs Server Workers\n(Mean, P95, P99 nearest-rank)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("max_workers", fontsize=10)
    ax2.set_ylabel("Latensi (ms)", fontsize=10)
    ax2.set_xticks(x)
    ax2.set_xticklabels(workers)
    ax2.legend()
    ax2.grid(axis="y", linestyle="--", alpha=0.6)
    for bars in (bars_mean, bars_p95, bars_p99):
        for bar in bars:
            yval = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2.0, yval + 15, f"{yval:.0f}",
                     ha="center", va="bottom", fontsize=7)

    plt.tight_layout()
    for path in save_paths:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        plt.savefig(path, dpi=200)
    plt.close()


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
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    tampilkan_header("PRAKTIKUM 3.4 - PENGUKURAN THROUGHPUT BERDASARKAN JUMLAH WORKER", "Benchmark")
    print("=== L3.4: Benchmark Concurrency GetMahasiswa (benchmark_workers) ===\n")
    print(f"Total Requests  : {TOTAL_REQUESTS}")
    print(f"Client Threads  : {NUM_CLIENTS}")
    print(f"Worker Configs  : {WORKER_CONFIGS}")
    print(f"Server Delay    : {SIMULATED_DELAY * 1000:.0f} ms / request (time.sleep(0.1))")
    print("Percentile      : nearest-rank, indeks ceil(p*n)-1\n")

    results = []
    base_port = 50075

    for idx, workers in enumerate(WORKER_CONFIGS):
        port = base_port + idx
        print(f"Mengukur max_workers={workers} (port {port})...")
        res = run_benchmark_for_workers(workers, port)
        results.append(res)
        print(f"  -> Total waktu: {res['total_time_s']:.2f} s | Throughput: {res['throughput']:.1f} req/s | "
              f"Mean: {res['mean_ms']:.1f} ms | P95: {res['p95_ms']:.1f} ms | P99: {res['p99_ms']:.1f} ms")

    # Tampilkan tabel hasil
    print("\n" + "=" * 100)
    print("TABEL HASIL PENGUKURAN L3.4 (percentile nearest-rank)")
    print("=" * 100)
    print(f"{'max_workers':<12} | {'Waktu (s)':<10} | {'Throughput':<12} | "
          f"{'Mean (ms)':<10} | {'P95 (ms)':<10} | {'P99 (ms)':<10}")
    print("-" * 100)
    for r in results:
        print(f"{r['workers']:<12} | {r['total_time_s']:<10.2f} | {r['throughput']:<12.1f} | "
              f"{r['mean_ms']:<10.1f} | {r['p95_ms']:<10.1f} | {r['p99_ms']:<10.1f}")
    print("=" * 100 + "\n")

    # Generate grafik
    plot_paths = [
        os.path.join(CURRENT_DIR, "l3_4_throughput_latency.png"),
        os.path.join(REPORTS_DIR, "l3_4_throughput_latency.png"),
    ]
    generate_plot(results, plot_paths)
    print("[OK] Grafik berhasil dibuat dan disimpan ke:")
    for p in plot_paths:
        print(f"     - {p}")

    print("\n[OK] L3.4 TERVALIDASI: Analisis throughput dan latensi selesai.")


if __name__ == "__main__":
    main()
