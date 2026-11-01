"""Unit test lokal yang tidak memerlukan server aktif."""

import unittest
import xmlrpc.client
from datetime import datetime

from calculator_service import akar, bagi, kali, pangkat, pantulkan, statistik, tambah
from xmlrpc_i8 import dumps_i8


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

    def test_l1_3_serialisasi_integer_besar(self) -> None:
        nilai = 2**31 + 1
        request_xml = dumps_i8((nilai,), "pantulkan", allow_none=True)
        request_params, method = xmlrpc.client.loads(
            request_xml, use_builtin_types=True
        )
        self.assertEqual(method, "pantulkan")
        self.assertEqual(request_params, (nilai,))
        self.assertIsInstance(request_params[0], int)

        response_xml = dumps_i8((nilai,), methodresponse=True, allow_none=True)
        response_params, _ = xmlrpc.client.loads(
            response_xml, use_builtin_types=True
        )
        self.assertEqual(response_params, (nilai,))
        self.assertIsInstance(response_params[0], int)

    def test_l1_3_serialisasi_fault(self) -> None:
        fault = xmlrpc.client.Fault(1, "uji fault")
        response_xml = dumps_i8(fault)
        self.assertIn("<methodResponse>", response_xml)
        self.assertIn("<fault>", response_xml)
        with self.assertRaises(xmlrpc.client.Fault) as context:
            xmlrpc.client.loads(response_xml, use_builtin_types=True)
        self.assertEqual(context.exception.faultCode, 1)
        self.assertEqual(context.exception.faultString, "uji fault")


if __name__ == "__main__":
    unittest.main(verbosity=2)
