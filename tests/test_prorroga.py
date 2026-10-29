"""Prórroga: el usuario debe ingresar fecha y no se modifican fórmulas."""
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import os
import re
import unittest

from alcanto_cloud.catalog import estado_documental
from alcanto_cloud.workbook import generar_copia

ARCHIVO = os.getenv("ALCANTO_TEST_WORKBOOK", "")


class RequisitosProrroga(unittest.TestCase):
    def test_fecha_solicitada_en_formulario(self):
        doc = next(x for x in estado_documental({}, set()) if x["hoja"] == "Anexo extension contrato")
        self.assertIn("ANEXO_M4", doc["faltan"])


@unittest.skipUnless(ARCHIVO and os.path.isfile(ARCHIVO), "Modelo privado no facilitado")
class ProrrogaConModeloReal(unittest.TestCase):
    def test_cambio_fecha_en_copia_sin_editar_formulas(self):
        original = Path(ARCHIVO).read_bytes()
        copia = generar_copia(original, {"ANEXO_M4": "2026-12-31", "C17": "TRABAJADOR DE PRUEBA"})
        self.assertEqual(original, Path(ARCHIVO).read_bytes())
        with ZipFile(BytesIO(original)) as a, ZipFile(BytesIO(copia)) as b:
            orig = a.read("xl/worksheets/sheet4.xml")
            nuevo = b.read("xl/worksheets/sheet4.xml")
            celda = rb'<c r="M4"[^>]*>(.*?)</c>'
            self.assertNotEqual(re.search(celda, orig, re.S).group(1),
                                re.search(celda, nuevo, re.S).group(1))
            for hoja in ("sheet1.xml", "sheet4.xml"):
                formulas = lambda z: re.findall(rb'<f(?:\s[^>]*)?>(.*?)</f>',
                    z.read("xl/worksheets/" + hoja), re.S)
                self.assertEqual(formulas(a), formulas(b))


if __name__ == "__main__":
    unittest.main()
