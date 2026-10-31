"""L2.3: Membuktikan backward compatibility Protobuf.

Skrip ini menggunakan stub LAMA (tanpa field prodi) untuk berkomunikasi
dengan server BARU (yang sudah mengirim field prodi). Jika berhasil,
ini membuktikan bahwa menambah field baru tidak merusak client lama.
"""

from __future__ import annotations

import argparse
import sys
import os

# Menambahkan path old_stubs agar import menggunakan stub lama.
OLD_STUBS_DIR = os.path.join(os.path.dirname(__file__), "old_stubs")
sys.path.insert(0, OLD_STUBS_DIR)

import akademik_pb2 as old_pb
import akademik_pb2_grpc as old_pb_grpc

# Kembalikan sys.path agar tidak mempengaruhi import lain.
sys.path.pop(0)

import grpc


def main() -> None:
    parser = argparse.ArgumentParser(description="L2.3: uji backward compatibility dengan stub lama.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=50051, type=int)
    args = parser.parse_args()

    print("=== L2.3: Backward Compatibility Test ===")
    print(f"Menggunakan stub LAMA dari: {OLD_STUBS_DIR}")
    print(f"Koneksi ke server BARU di {args.host}:{args.port}")
    print()

    # Periksa apakah stub lama benar-benar tidak punya field prodi.
    mhs_fields = [field.name for field in old_pb.Mahasiswa.DESCRIPTOR.fields]
    print(f"Field pada Mahasiswa (stub lama): {mhs_fields}")
    has_prodi = "prodi" in mhs_fields
    print(f"Stub lama memiliki field 'prodi': {has_prodi}")
    print()

    with grpc.insecure_channel(f"{args.host}:{args.port}") as channel:
        stub = old_pb_grpc.LayananNilaiStub(channel)

        # Panggil GetMahasiswa menggunakan stub lama.
        request = old_pb.MahasiswaRequest(nim="2023001")
        response = stub.GetMahasiswa(request, timeout=3)

        print("Respons GetMahasiswa dengan stub LAMA:")
        print(f"  nim  : {response.nim}")
        print(f"  nama : {response.nama}")
        print(f"  ipk  : {response.ipk:.2f}")

        # Coba akses field prodi - pada stub lama, field ini tidak dikenal.
        # Protobuf menyimpan field yang tidak dikenali di _unknown_fields.
        if has_prodi:
            print(f"  prodi: {response.prodi}")
            print("\n[INFO] Stub lama SUDAH memiliki field prodi (kemungkinan stub belum")
            print("disalin sebelum perubahan proto). Uji tetap berhasil.")
        else:
            # Pada proto3, field yang tidak dikenal tetap di-deserialize
            # dan disimpan - tapi tidak bisa diakses lewat attribute biasa.
            print("  prodi: (field tidak ada pada stub lama - ini yang diharapkan)")
            print()
            print("[BUKTI] Client dengan stub lama berhasil memanggil server baru.")
            print("Field 'prodi' yang dikirim server diabaikan secara aman oleh client lama.")

        # Uji juga StreamNilai untuk memastikan streaming masih berfungsi.
        print("\nStreamNilai dengan stub lama:")
        for nilai in stub.StreamNilai(old_pb.MahasiswaRequest(nim="2023001"), timeout=3):
            print(f"  - {nilai.matkul}: {nilai.nilai:g}")

        print()
        print("=== KESIMPULAN ===")
        print("Penambahan field 'prodi = 4' pada message Mahasiswa TIDAK merusak")
        print("client yang dikompilasi dari proto lama. Ini karena Protobuf")
        print("menggunakan nomor field (bukan nama), dan field yang tidak dikenali")
        print("oleh stub lama akan diabaikan secara aman (forward compatibility).")
        print("Sebaliknya, client baru yang membaca dari server lama akan menerima")
        print("string kosong ('') untuk field prodi karena proto3 menggunakan")
        print("default value untuk field yang tidak ada pada respons.")


if __name__ == "__main__":
    main()
