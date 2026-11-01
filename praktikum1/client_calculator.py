"""Client demonstrasi dan penanganan error server XML-RPC kalkulator."""

from __future__ import annotations

import argparse
import socket
import xmlrpc.client
from datetime import datetime

from xmlrpc_i8 import I8ServerProxy


def create_proxy(host: str, port: int, verbose: bool = False) -> I8ServerProxy:
    return I8ServerProxy(
        f"http://{host}:{port}/RPC2",
        allow_none=True,
        verbose=verbose,
        use_builtin_types=True,
    )


def run_demo(proxy: xmlrpc.client.ServerProxy) -> None:
    print("Daftar method:", proxy.system.listMethods())
    print("tambah(5, 3) =", proxy.tambah(5, 3))
    print("kali(4, 7) =", proxy.kali(4, 7))
    print("bagi(10, 2) =", proxy.bagi(10, 2))
    print("pangkat(2, 10) =", proxy.pangkat(2, 10))
    print("akar(81) =", proxy.akar(81))
    print("statistik([2, 4, 6, 8]) =", proxy.statistik([2, 4, 6, 8]))

    for label, operation in (
        ("bagi(10, 0)", lambda: proxy.bagi(10, 0)),
        ("akar(-1)", lambda: proxy.akar(-1)),
        ("statistik([])", lambda: proxy.statistik([])),
    ):
        try:
            operation()
        except xmlrpc.client.Fault as error:
            print(f"Fault {label}: {error.faultString}")


def run_l1_3_probe(proxy: xmlrpc.client.ServerProxy) -> None:
    """Menguji DateTime dan integer di atas batas signed 32-bit XML-RPC."""
    timestamp = datetime(2026, 10, 31, 10, 30, 0)
    hasil_datetime = proxy.pantulkan(timestamp)
    print(
        "datetime dikirim/diterima:",
        timestamp.isoformat(),
        "->",
        hasil_datetime.isoformat(),
        f"({type(hasil_datetime).__name__})",
    )
    assert isinstance(hasil_datetime, datetime), "Hasil datetime berubah tipe."
    assert hasil_datetime == timestamp, "Nilai datetime berubah saat serialisasi."

    nilai_besar = 2**31 + 1
    hasil_besar = proxy.pantulkan(nilai_besar)
    print(
        "integer besar dikirim/diterima:",
        nilai_besar,
        "->",
        hasil_besar,
        f"({type(hasil_besar).__name__})",
    )
    assert isinstance(hasil_besar, int) and not isinstance(hasil_besar, bool), (
        "Hasil integer besar bukan int."
    )
    assert hasil_besar == nilai_besar, (
        f"Nilai integer berubah: dikirim {nilai_besar}, diterima {hasil_besar}."
    )
    print(
        f"[OK] {nilai_besar} > batas signed 32-bit "
        f"({2**31 - 1}); nilai dan tipe int dipertahankan."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Menjalankan client kalkulator XML-RPC.")
    parser.add_argument("--host", default="127.0.0.1", help="Host server (default: 127.0.0.1).")
    parser.add_argument("--port", default=8000, type=int, help="Port server (default: 8000).")
    parser.add_argument("--verbose", action="store_true", help="Tampilkan XML HTTP request/response.")
    parser.add_argument("--probe-l1-3", action="store_true", help="Jalankan pengujian datetime dan integer besar.")
    parser.add_argument(
        "--expect-offline",
        action="store_true",
        help="Sukses hanya bila koneksi ke server gagal dan error tertangani.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    proxy = create_proxy(args.host, args.port, args.verbose)
    try:
        if args.expect_offline:
            proxy.system.listMethods()
            print("Server masih aktif; matikan server terlebih dahulu untuk pengujian server offline.")
            return 1
        if args.probe_l1_3:
            run_l1_3_probe(proxy)
        else:
            run_demo(proxy)
    except (ConnectionRefusedError, socket.gaierror, OSError) as error:
        print(
            "Tidak dapat terhubung ke server XML-RPC. "
            f"Pastikan server aktif di {args.host}:{args.port}. Detail: {error}"
        )
        return 0 if args.expect_offline else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
