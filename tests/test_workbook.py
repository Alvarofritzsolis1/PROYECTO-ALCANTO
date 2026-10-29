"""Pruebas sin datos personales; el archivo real se pasa por variable de entorno."""
import os
import unittest
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from alcanto_cloud.catalog import estado_documental
from alcanto_cloud.workbook import catalogos, generar_copia, verificar_plantilla, PlantillaInvalida
from alcanto_cloud.pdf_service import validar_pdf, ErrorDeConversion

ARCHIVO = os.getenv("ALCANTO_TEST_WORKBOOK", "")

@unittest.skipUnless(ARCHIVO and os.path.isfile(ARCHIVO), "ALCANTO_TEST_WORKBOOK no suministrado")
class PruebasLibroReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(ARCHIVO,"rb") as handle:
            cls.original = handle.read()

    def test_17_hojas_y_catalogos(self):
        info = verificar_plantilla(self.original)
        self.assertEqual(len(info["hojas"]),17)
        m = catalogos(self.original)
        self.assertEqual(m["registros_pts"],26)
        self.assertEqual(len(m["pts_completos"]),3)
        self.assertGreaterEqual(len(m["obras"]),3)

    def test_integridad_total_formulas_en_copia(self):
        antes=sha256(self.original).hexdigest()
        datos={"C5":"EMPRESA DE PRUEBA LTDA", "C6":"00.000.000-0",
               "C17":"TRABAJADOR DE PRUEBA", "C18":"11.111.111-1",
               "C29":"PINTOR", "D30":"Brisas de Junquillar", "C32":"750000",
               "C20":"1996-06-10"}
        copia=generar_copia(self.original,datos)
        self.assertEqual(sha256(self.original).hexdigest(), antes)
        with ZipFile(BytesIO(self.original)) as a, ZipFile(BytesIO(copia)) as b:
            self.assertEqual(a.namelist(), b.namelist())
            for path in a.namelist():
                if path not in {"xl/worksheets/sheet1.xml","xl/workbook.xml"}:
                    self.assertEqual(a.read(path),b.read(path), path)
            import re
            formulas=lambda x:re.findall(rb'<f(?:\s[^>]*)?>(.*?)</f>',x,re.S)
            self.assertEqual(formulas(a.read('xl/worksheets/sheet1.xml')),
                             formulas(b.read('xl/worksheets/sheet1.xml')))
            self.assertIn(b'TRABAJADOR DE PRUEBA',b.read('xl/worksheets/sheet1.xml'))
            self.assertNotIn(b'C5" s="94" t="s"',b.read('xl/worksheets/sheet1.xml'))

    def test_prohibido_editar_formulas(self):
        with self.assertRaises(ValueError):
            generar_copia(self.original,{"C33":"CAMBIADO"})

    def test_se_borran_datos_previos(self):
        copia=generar_copia(self.original,{"C17":"TRABAJADOR DE PRUEBA"})
        from alcanto_cloud.workbook import _abrir,_shared_strings,_leer_celdas
        with _abrir(copia) as z:
            d=_leer_celdas(z,'xl/worksheets/sheet1.xml',["C5","C17","C18","C32"],_shared_strings(z))
        self.assertEqual(d["C5"], "")
        self.assertEqual(d["C18"], "")
        self.assertEqual(d["C17"], "TRABAJADOR DE PRUEBA")

class PruebasValidacion(unittest.TestCase):
    def test_requisitos_para_documentos(self):
        estado=estado_documental({"C5":"EMPRESA DEMO","C17":"TRABAJADOR DEMO"},set())
        self.assertEqual(len(estado),10)
        self.assertEqual(estado[0]["estado"],"Faltan datos")

    def test_pdf_invalido(self):
        with self.assertRaises(ErrorDeConversion):validar_pdf(b"not a pdf","IRL")

if __name__=="__main__": unittest.main()
