"""L1.4: membandingkan latensi panggilan lokal dan XML-RPC."""

from __future__ import annotations

import argparse
import statistics
import time

from calculator_service import tambah
from client_calculator import create_proxy


def measure(operation, samples: int) -> list[float]:
    """Mengukur durasi setiap panggilan dalam milidetik."""
    durations_ms: list[float] = []
    for _ in range(samples):
        started_at = time.perf_counter()
        operation()
        durations_ms.append((time.perf_counter() - started_at) * 1000)
    return durations_ms


def describe(label: str, durations_ms: list[float]) -> None:
    total_ms = sum(durations_ms)
    print(f"{label} ({len(durations_ms)} panggilan)")
    print(f"  total    : {total_ms:.3f} ms")
    print(f"  rata-rata: {statistics.mean(durations_ms):.3f} ms")
    print(f"  minimum  : {min(durations_ms):.3f} ms")
    print(f"  maksimum : {max(durations_ms):.3f} ms")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark XML-RPC vs panggilan lokal untuk L1.4.")
    parser.add_argument("--host", default="127.0.0.1", help="Host server (default: 127.0.0.1).")
    parser.add_argument("--port", default=8000, type=int, help="Port server (default: 8000).")
    parser.add_argument("--samples", default=100, type=int, help="Jumlah panggilan tiap metode (default: 100).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.samples < 1:
        raise SystemExit("--samples harus minimal 1.")

    proxy = create_proxy(args.host, args.port)
    local_durations = measure(lambda: tambah(5, 3), args.samples)
    rpc_durations = measure(lambda: proxy.tambah(5, 3), args.samples)

    describe("Panggilan lokal tambah(5, 3)", local_durations)
    describe("XML-RPC tambah(5, 3)", rpc_durations)
    ratio = statistics.mean(rpc_durations) / statistics.mean(local_durations)
    print(f"Overhead rata-rata XML-RPC: {ratio:.1f}x dibanding panggilan lokal.")


if __name__ == "__main__":
    main()
