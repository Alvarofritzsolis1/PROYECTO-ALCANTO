"""Pruebas sin datos privados del nuevo motor de impresión basado en XLSX."""
from __future__ import annotations
import unittest
from alcanto_cloud.pdf_excel_local import pesos_en_palabras, ErrorExcelLocal, MAX_PAGINAS


class TestConversionDesdeExcelOriginal(unittest.TestCase):
    def test_montos_en_palabras_chileno(self):
        casos = {
            "1": "Un peso.",
            "21": "Veintiún pesos.",
            "100": "Cien pesos.",
            "553553": "Quinientos cincuenta y tres mil quinientos cincuenta y tres pesos.",
            "640000": "Seiscientos cuarenta mil pesos.",
            "1000000": "Un millón de pesos.",
            "1000000000": "Mil millones de pesos.",
        }
        for importe, correcto in casos.items():
            with self.subTest(importe=importe):
                self.assertEqual(pesos_en_palabras(importe), correcto)

    def test_montos_invalidos(self):
        for n in ("0", "-4", "55,000", "abc", "", "1.2", "1000000000000"):
            with self.subTest(importe=n):
                with self.assertRaises(ValueError):
                    pesos_en_palabras(n)

    def test_limitador_de_paginas_cubre_diez_documentos(self):
        self.assertEqual(len(MAX_PAGINAS), 10)
        self.assertEqual(MAX_PAGINAS["Contrato Imprimible"], 3)
        self.assertLessEqual(max(MAX_PAGINAS.values()), 18)


if __name__ == "__main__":
    unittest.main()
