"""Pruebas: opciones predefinidas deben coincidir con el archivo ALCANTO real.

El libro original no se sube a GitHub; validar contra él si se proporciona
ALCANTO_TEST_WORKBOOK como ruta privada en el entorno de pruebas.
"""
import os
import unittest
from alcanto_cloud.catalog import (
    OBRAS_PREDEFINIDAS, CARGOS_PREDEFINIDOS, DIRECCIONES_OBRA,
    RENTA_BASE_REFERENCIA, JORNADA_REFERENCIA, PAGO_REFERENCIA,
    PTS_EXISTENTES, catalogo_predefinido,
)
from alcanto_cloud.workbook import catalogos, _abrir, _shared_strings, _leer_celdas


class TestOpcionesSinPlantilla(unittest.TestCase):
    def test_tres_obras_exactas(self):
        self.assertEqual(OBRAS_PREDEFINIDAS, (
            "Lomas Verdes", "Brisas de Junquillar", "Concepción"))
        self.assertEqual(set(DIRECCIONES_OBRA), set(OBRAS_PREDEFINIDAS))
        self.assertTrue(all(DIRECCIONES_OBRA.values()))

    def test_renta_jornada_y_pago_editables(self):
        self.assertEqual(RENTA_BASE_REFERENCIA, 553553)
        self.assertEqual(JORNADA_REFERENCIA, 42)
        self.assertEqual(PAGO_REFERENCIA, "MENSUALMENTE")

    def test_cargos_y_pts(self):
        self.assertEqual(len(CARGOS_PREDEFINIDOS), 25)
        self.assertEqual(len(set(CARGOS_PREDEFINIDOS)), 25)
        self.assertEqual(PTS_EXISTENTES, {"pintor", "albañil", "gasfiter"})
        cat=catalogo_predefinido()
        self.assertEqual(cat["obras"], list(OBRAS_PREDEFINIDAS))
        self.assertEqual(cat["cargos"], list(CARGOS_PREDEFINIDOS))


class TestArchivoOriginalOpcional(unittest.TestCase):
    @unittest.skipUnless(
        os.environ.get("ALCANTO_TEST_WORKBOOK") and
        os.path.isfile(os.environ.get("ALCANTO_TEST_WORKBOOK", "")),
        "No hay archivo de prueba privado en el entorno"
    )
    def test_comparacion_con_original(self):
        data=open(os.environ["ALCANTO_TEST_WORKBOOK"], "rb").read()
        actual=catalogos(data)
        self.assertEqual(actual["obras"],list(OBRAS_PREDEFINIDAS))
        self.assertEqual(actual["cargos"],list(CARGOS_PREDEFINIDOS))
        self.assertEqual(actual["pts_completos"],set(PTS_EXISTENTES))
        with _abrir(data) as z:
            s=_shared_strings(z)
            d=_leer_celdas(z, "xl/worksheets/sheet1.xml",
                        ["C31","C32","C34","T16","T17","T18","U16","U17","U18"],s)
        self.assertEqual(d["C31"],str(JORNADA_REFERENCIA))
        self.assertEqual(d["C32"],str(RENTA_BASE_REFERENCIA))
        self.assertEqual(d["C34"],PAGO_REFERENCIA)
        for idx,obra in enumerate(OBRAS_PREDEFINIDAS,16):
            self.assertEqual(d["T"+str(idx)],obra)
            self.assertEqual(d["U"+str(idx)],DIRECCIONES_OBRA[obra])

if __name__=="__main__":
    unittest.main()
