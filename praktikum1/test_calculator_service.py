"""Unit test lokal yang tidak memerlukan server aktif."""

import unittest
from datetime import datetime

from calculator_service import akar, bagi, kali, pangkat, pantulkan, statistik, tambah


class CalculatorServiceTests(unittest.TestCase):
    def test_operasi_dasar(self) -> None:
        self.assertEqual(tambah(5, 3), 8)
        self.assertEqual(kali(4, 7), 28)
        self.assertEqual(bagi(10, 2), 5)

    def test_bagi_nol_ditolak(self) -> None:
        with self.assertRaises(ValueError):
            bagi(10, 0)

    def test_l1_1_pangkat_dan_akar(self) -> None:
        self.assertEqual(pangkat(2, 10), 1024)
        self.assertEqual(akar(81), 9)
        with self.assertRaises(ValueError):
            akar(-1)

    def test_l1_2_statistik(self) -> None:
        self.assertEqual(
            statistik([2, 4, 6, 8]),
            {"min": 2, "max": 8, "rata2": 5.0},
        )
        with self.assertRaises(ValueError):
            statistik([])
        with self.assertRaises(TypeError):
            statistik([1, "dua"])

    def test_l1_3_pantulkan_datetime(self) -> None:
        timestamp = datetime(2026, 10, 31, 10, 30, 0)
        self.assertEqual(pantulkan(timestamp), timestamp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
