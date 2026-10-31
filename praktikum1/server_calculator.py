"""Server XML-RPC kalkulator untuk Praktikum 1."""

from __future__ import annotations

import argparse
from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer

from calculator_service import akar, bagi, kali, pangkat, statistik, tambah, pantulkan


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/RPC2",)


def build_server(host: str, port: int) -> SimpleXMLRPCServer:
    """Membuat server dan mendaftarkan seluruh RPC yang dibutuhkan L1.1-L1.2."""
    server = SimpleXMLRPCServer(
        (host, port),
        requestHandler=RequestHandler,
        allow_none=True,
        logRequests=True,
        use_builtin_types=True,
    )
    server.register_introspection_functions()
    for function in (tambah, kali, bagi, pangkat, akar, statistik, pantulkan):
        server.register_function(function, function.__name__)
    return server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Menjalankan server kalkulator XML-RPC.")
    parser.add_argument("--host", default="127.0.0.1", help="Host bind server (default: 127.0.0.1).")
    parser.add_argument("--port", default=8000, type=int, help="Port server (default: 8000).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = build_server(args.host, args.port)
    print(f"Server XML-RPC berjalan di http://{args.host}:{args.port}/RPC2")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
