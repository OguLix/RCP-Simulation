"""L2.4: Membandingkan ukuran serialisasi Protobuf vs XML-RPC untuk data setara.

Skrip ini tidak memerlukan server yang berjalan; ia hanya membuat
objek Protobuf dan XML-RPC secara lokal, lalu mencetak ukuran byte.
"""

from __future__ import annotations

import sys
import os
import xmlrpc.client

# Pastikan modul lokal pada direktori ini dapat diimpor.
sys.path.insert(0, os.path.dirname(__file__))
import akademik_pb2 as pb


def main() -> None:
    print("=== L2.4: Perbandingan Ukuran Pesan Protobuf vs XML-RPC ===\n")

    # --- Data 1: GetMahasiswa response ---
    print("--- Data 1: Respons GetMahasiswa ---")

    mhs = pb.Mahasiswa(nim="2023001", nama="Andi", ipk=3.26, prodi="Informatika")
    proto_bytes = mhs.SerializeToString()
    proto_size = len(proto_bytes)

    # Representasi setara dalam XML-RPC (sebagai struct).
    xml_data = {"nim": "2023001", "nama": "Andi", "ipk": 3.26, "prodi": "Informatika"}
    xml_payload = xmlrpc.client.dumps((xml_data,), methodresponse=True)
    xml_size = len(xml_payload.encode("utf-8"))

    print(f"  Protobuf : {proto_size} bytes")
    print(f"    hex    : {proto_bytes.hex()}")
    print(f"  XML-RPC  : {xml_size} bytes")
    print(f"  Rasio    : XML-RPC {xml_size / proto_size:.1f}x lebih besar dari Protobuf")
    print()

    # --- Data 2: TambahNilai request ---
    print("--- Data 2: Request TambahNilai ---")

    nilai_req = pb.NilaiRequest(nim="2023001", matkul="Komputasi Paralel", nilai=88.0)
    proto_bytes_2 = nilai_req.SerializeToString()
    proto_size_2 = len(proto_bytes_2)

    xml_data_2 = {"nim": "2023001", "matkul": "Komputasi Paralel", "nilai": 88.0}
    xml_payload_2 = xmlrpc.client.dumps((xml_data_2,), "TambahNilai")
    xml_size_2 = len(xml_payload_2.encode("utf-8"))

    print(f"  Protobuf : {proto_size_2} bytes")
    print(f"    hex    : {proto_bytes_2.hex()}")
    print(f"  XML-RPC  : {xml_size_2} bytes")
    print(f"  Rasio    : XML-RPC {xml_size_2 / proto_size_2:.1f}x lebih besar dari Protobuf")
    print()

    # --- Data 3: tambah(5, 3) untuk perbandingan langsung dengan XML-RPC ---
    print("--- Data 3: Panggilan tambah(5, 3) - Perbandingan dengan XML-RPC ---")

    # Protobuf: tidak ada definisi 'tambah' di proto, jadi kita simulasikan
    # dengan dua int32 dalam sebuah message sederhana. Ukuran minimum protobuf
    # untuk dua integer kecil: field_tag(1B) + varint(1B) x2 = ~4 bytes.
    # Kita pakai NilaiRequest sebagai proxy terdekat, atau hitung manual.
    # Manual: field 1 varint 5 = [0x08, 0x05], field 2 varint 3 = [0x10, 0x03] = 4 bytes.
    proto_manual = b"\x08\x05\x10\x03"  # field 1=5, field 2=3 dalam protobuf encoding
    proto_manual_size = len(proto_manual)

    xml_req = xmlrpc.client.dumps((5, 3), "tambah")
    xml_req_size = len(xml_req.encode("utf-8"))
    xml_res = xmlrpc.client.dumps((8,), methodresponse=True)
    xml_res_size = len(xml_res.encode("utf-8"))

    print(f"  Protobuf request  : {proto_manual_size} bytes (dua varint: 5 dan 3)")
    print(f"  XML-RPC request   : {xml_req_size} bytes")
    print(f"  XML-RPC response  : {xml_res_size} bytes")
    print(f"  Rasio request     : XML-RPC {xml_req_size / proto_manual_size:.1f}x lebih besar")
    print()

    # --- Data 4: Daftar nilai (lebih banyak data) ---
    print("--- Data 4: Beberapa nilai mata kuliah ---")

    mata_kuliah = [
        ("Basis Data", 85.0),
        ("Jaringan", 78.0),
        ("Komputasi Paralel", 88.0),
        ("Sistem Operasi", 91.0),
    ]

    total_proto = 0
    for mk, n in mata_kuliah:
        msg = pb.Nilai(matkul=mk, nilai=n)
        total_proto += len(msg.SerializeToString())

    xml_list = [{"matkul": mk, "nilai": n} for mk, n in mata_kuliah]
    xml_payload_4 = xmlrpc.client.dumps((xml_list,), methodresponse=True)
    xml_size_4 = len(xml_payload_4.encode("utf-8"))

    print(f"  Protobuf (4 pesan Nilai) : {total_proto} bytes total")
    print(f"  XML-RPC (1 struct array) : {xml_size_4} bytes")
    print(f"  Rasio                    : XML-RPC {xml_size_4 / total_proto:.1f}x lebih besar")
    print()

    # --- Ringkasan ---
    print("=== RINGKASAN ===")
    print("Protobuf menggunakan encoding biner (varint, length-delimited) sehingga")
    print("ukuran pesan jauh lebih kecil dibandingkan XML-RPC yang berbasis teks XML.")
    print("Overhead XML mencakup tag pembuka/penutup, deklarasi tipe, dan header HTTP.")
    print(f"Untuk data mahasiswa sederhana, XML-RPC {xml_size / proto_size:.1f}x lebih besar.")
    print("Pada volume data besar atau frekuensi panggilan tinggi, perbedaan ini")
    print("sangat berpengaruh terhadap bandwidth dan latensi jaringan.")


if __name__ == "__main__":
    main()
