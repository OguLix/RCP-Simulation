"""Praktikum RPC - Komputasi Paralel dan Terdistribusi

Nama : Muhammad Fadhlan Aminullah
NPM  : 247006111151

L1.4: membandingkan latensi panggilan lokal dan XML-RPC pada satu mesin."""

from __future__ import annotations

import argparse
import platform
import statistics
import time

from calculator_service import tambah
from client_calculator import create_proxy


def measure(operation, samples: int, warmup: int = 0) -> list[float]:
    """Mengukur durasi setiap panggilan dalam milidetik setelah pemanasan."""
    for _ in range(warmup):
        operation()

    durations_ms: list[float] = []
    for _ in range(samples):
        started_at = time.perf_counter()
        operation()
        durations_ms.append((time.perf_counter() - started_at) * 1000)
    return durations_ms


def describe(label: str, durations_ms: list[float]) -> None:
    total_ms = sum(durations_ms)
    stddev_ms = statistics.stdev(durations_ms) if len(durations_ms) > 1 else 0.0
    print(f"{label} ({len(durations_ms)} panggilan)")
    print(f"  total    : {total_ms:.4f} ms")
    print(f"  rata-rata: {statistics.mean(durations_ms):.4f} ms")
    print(f"  median   : {statistics.median(durations_ms):.4f} ms")
    print(f"  stdev    : {stddev_ms:.4f} ms")
    print(f"  minimum  : {min(durations_ms):.4f} ms")
    print(f"  maksimum : {max(durations_ms):.4f} ms")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark XML-RPC vs panggilan lokal untuk L1.4.")
    parser.add_argument("--host", default="127.0.0.1", help="Host server (default: 127.0.0.1).")
    parser.add_argument("--port", default=8000, type=int, help="Port server (default: 8000).")
    parser.add_argument("--samples", default=100, type=int, help="Jumlah panggilan tiap metode (default: 100).")
    parser.add_argument("--warmup", default=10, type=int, help="Jumlah panggilan pemanasan (default: 10).")
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
    tampilkan_header("PRAKTIKUM 1.4 - PENGUKURAN PERFORMA RPC", "Benchmark")
    if args.samples < 1:
        raise SystemExit("--samples harus minimal 1.")
    if args.warmup < 0:
        raise SystemExit("--warmup tidak boleh negatif.")

    print("=== L1.4: Latensi lokal vs XML-RPC ===\n")
    print(f"Host/port       : {args.host}:{args.port}")
    print(f"Samples/warmup  : {args.samples}/{args.warmup}")
    print(f"Python          : {platform.python_version()} ({platform.architecture()[0]})")
    print(f"Platform        : {platform.platform()}")
    print(f"Resolusi timer  : {time.get_clock_info('perf_counter').resolution * 1e9:.0f} ns")
    print()

    proxy = create_proxy(args.host, args.port)
    local_durations = measure(lambda: tambah(5, 3), args.samples, args.warmup)
    rpc_durations = measure(lambda: proxy.tambah(5, 3), args.samples, args.warmup)

    describe("Panggilan lokal tambah(5, 3)", local_durations)
    describe("XML-RPC tambah(5, 3)", rpc_durations)

    local_mean = statistics.mean(local_durations)
    rpc_mean = statistics.mean(rpc_durations)
    print(f"Selisih rata-rata per panggilan: {rpc_mean - local_mean:.3f} ms")
    if local_mean > 0:
        print(f"Rasio rata-rata RPC/lokal    : {rpc_mean / local_mean:.1f}x")
    else:
        print("Rasio tidak dapat dihitung karena rata-rata lokal nol.")

    print("\nCatatan interpretasi:")
    print("- Hasil ini berasal dari satu mesin (localhost), bukan pengujian antar-komputer.")
    print("- Panggilan lokal mendekati resolusi timer, sehingga rasio sangat sensitif")
    print("  terhadap overhead pengukuran dan tidak boleh ditafsirkan sebagai biaya jaringan.")
    print("- Untuk pengujian antar-komputer, jalankan server dengan --host 0.0.0.0 lalu")
    print("  client dengan --host <IP_SERVER> dan catat IP serta jenis jaringannya.")


if __name__ == "__main__":
    main()
