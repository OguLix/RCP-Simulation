"""Praktikum RPC - Komputasi Paralel dan Terdistribusi

Nama : Muhammad Fadhlan Aminullah
NPM  : 247006111151

L2.4: membandingkan ukuran payload Protobuf vs XML-RPC untuk data setara.

Metode pengukuran:
- Yang dibandingkan adalah payload serialisasi aplikasi, bukan paket jaringan.
- Header HTTP/1.1 (XML-RPC) dan framing HTTP/2 + prefix 5 byte per pesan gRPC
  sama-sama tidak dihitung, sehingga perbandingan bersifat payload-level.
- XML-RPC memakai envelope methodCall/methodResponse; Protobuf hanya message biner.
- Untuk daftar nilai, perbandingan dilakukan per pesan (4 pesan vs 4 respons),
  bukan 4 pesan Protobuf melawan satu array XML-RPC.
"""

from __future__ import annotations

import os
import sys
import xmlrpc.client

# Pastikan modul lokal pada direktori ini dapat diimpor.
sys.path.insert(0, os.path.dirname(__file__))
import akademik_pb2 as pb


def report_case(label: str, proto_size: int, xml_size: int, catatan: str = "") -> None:
    ratio = xml_size / proto_size if proto_size else float("inf")
    print(f"--- {label} ---")
    print(f"  Protobuf : {proto_size} byte")
    print(f"  XML-RPC  : {xml_size} byte")
    print(f"  Rasio    : XML-RPC {ratio:.1f}x lebih besar")
    if catatan:
        print(f"  Catatan  : {catatan}")
    print()


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
    tampilkan_header("PRAKTIKUM 2.4 - PERBANDINGAN UKURAN PESAN XML-RPC DAN PROTOBUF", "Test")
    print("=== L2.4: Perbandingan Ukuran Payload Protobuf vs XML-RPC ===\n")
    print("Metode: ukuran payload serialisasi aplikasi; header HTTP dan framing gRPC")
    print("tidak dihitung untuk kedua sisi. XML-RPC menyertakan envelope methodCall/")
    print("methodResponse, Protobuf hanya message biner.\n")

    # Data 1: respons GetMahasiswa (payload setara).
    mhs = pb.Mahasiswa(nim="2023001", nama="Andi", ipk=3.26, prodi="Informatika")
    proto_bytes = mhs.SerializeToString()
    xml_data = {"nim": "2023001", "nama": "Andi", "ipk": 3.26, "prodi": "Informatika"}
    xml_payload = xmlrpc.client.dumps((xml_data,), methodresponse=True)
    report_case(
        "Data 1: respons GetMahasiswa",
        len(proto_bytes),
        len(xml_payload.encode("utf-8")),
        f"protobuf hex: {proto_bytes.hex()}",
    )

    # Data 2: request TambahNilai (payload setara).
    nilai_req = pb.NilaiRequest(nim="2023001", matkul="Komputasi Paralel", nilai=88.0)
    proto_bytes_2 = nilai_req.SerializeToString()
    xml_data_2 = {"nim": "2023001", "matkul": "Komputasi Paralel", "nilai": 88.0}
    xml_payload_2 = xmlrpc.client.dumps((xml_data_2,), "TambahNilai")
    report_case(
        "Data 2: request TambahNilai",
        len(proto_bytes_2),
        len(xml_payload_2.encode("utf-8")),
        f"protobuf hex: {proto_bytes_2.hex()}",
    )

    # Data 3: tambah(5, 3). Tidak ada RPC ini di proto, jadi sisi Protobuf
    # memakai ilustrasi encoding dua varint, bukan pesan dari akademik.proto.
    proto_manual = b"\x08\x05\x10\x03"  # field 1 = 5, field 2 = 3
    xml_req = xmlrpc.client.dumps((5, 3), "tambah")
    xml_res = xmlrpc.client.dumps((8,), methodresponse=True)
    report_case(
        "Data 3: request tambah(5, 3)",
        len(proto_manual),
        len(xml_req.encode("utf-8")),
        "Protobuf diilustrasikan manual (dua varint); tidak ada RPC tambah di proto.",
    )
    print(f"  Respons XML-RPC tambah(5, 3): {len(xml_res.encode('utf-8'))} byte")
    print()

    # Data 4: 4 pesan Nilai vs 4 respons XML-RPC (per pesan, bukan array).
    mata_kuliah = [
        ("Basis Data", 85.0),
        ("Jaringan", 78.0),
        ("Komputasi Paralel", 88.0),
        ("Sistem Operasi", 91.0),
    ]

    total_proto = 0
    total_xml = 0
    for mk, n in mata_kuliah:
        msg = pb.Nilai(matkul=mk, nilai=n)
        total_proto += len(msg.SerializeToString())
        xml_item = xmlrpc.client.dumps(({"matkul": mk, "nilai": n},), methodresponse=True)
        total_xml += len(xml_item.encode("utf-8"))

    report_case(
        "Data 4: 4 pesan Nilai (per pesan)",
        total_proto,
        total_xml,
        "4 pesan Protobuf dibandingkan dengan 4 respons XML-RPC terpisah.",
    )

    print("=== RINGKASAN ===")
    print("Pada payload yang diuji, XML-RPC lebih besar karena membawa tag XML dan")
    print("envelope methodCall/methodResponse. Protobuf memakai encoding biner varint")
    print("dan length-delimited. Perbandingan ini tidak menghitung header HTTP maupun")
    print("framing HTTP/2, sehingga bukan perbandingan ukuran paket di jaringan.")


if __name__ == "__main__":
    main()
