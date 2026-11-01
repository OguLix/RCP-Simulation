"""Praktikum RPC - Komputasi Paralel dan Terdistribusi

Nama : Muhammad Fadhlan Aminullah
NPM  : 247006111151

Logika kalkulator yang dipakai server XML-RPC dan benchmark lokal."""

from __future__ import annotations

import math
from collections.abc import Iterable


def tambah(a: int | float, b: int | float) -> int | float:
    """Mengembalikan penjumlahan dua angka."""
    return a + b


def kali(a: int | float, b: int | float) -> int | float:
    """Mengembalikan perkalian dua angka."""
    return a * b


def bagi(a: int | float, b: int | float) -> float:
    """Membagi a dengan b; server akan mengubah ValueError menjadi XML-RPC fault."""
    if b == 0:
        raise ValueError("Pembagian dengan nol tidak diperbolehkan.")
    return a / b


def pangkat(a: int | float, b: int | float) -> int | float:
    """L1.1: mengembalikan a pangkat b."""
    return a**b


def akar(x: int | float) -> float:
    """L1.1: mengembalikan akar kuadrat bilangan non-negatif."""
    if x < 0:
        raise ValueError("Akar kuadrat bilangan negatif tidak didukung.")
    return math.sqrt(x)


def statistik(daftar: Iterable[int | float]) -> dict[str, float | int]:
    """L1.2: mengembalikan min, max, dan rata-rata sebuah daftar angka."""
    angka = list(daftar)
    if not angka:
        raise ValueError("Daftar angka tidak boleh kosong.")
    if not all(isinstance(nilai, (int, float)) and not isinstance(nilai, bool) for nilai in angka):
        raise TypeError("Semua elemen daftar harus berupa angka.")

    return {
        "min": min(angka),
        "max": max(angka),
        "rata2": sum(angka) / len(angka),
    }


def pantulkan(nilai: object) -> object:
    """L1.3: mengembalikan nilai apa adanya untuk mengamati serialisasi XML-RPC."""
    return nilai
