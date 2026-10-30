"""150 casos documentales: 15 pruebas independientes por cada una de 10 hojas.

NO afirma haber exportado 150 PDF reales: comprueba reglas de disponibilidad,
combinación de datos, protección contra cruces y errores básicos de PDF.
La conversión real de Aspose requiere credenciales y pruebas de impresión aparte.
"""
from __future__ import annotations

import unittest

from alcanto_cloud.catalog import DOCUMENTOS, CARGOS_PREDEFINIDOS
from alcanto_cloud.documentos import (
    HOJAS_EMPRESA, HOJAS_TRABAJADOR, documento_estado,
    preparar_datos, estado_por_contexto,
)
from alcanto_cloud.pdf_service import validar_pdf, ErrorDeConversion

EMPRESA = {
    "C5": "CONSTRUCTORA DEMOSTRACIÓN SpA",
    "C6": "76.111.222-3", "C7": "REPRESENTANTE DE PRUEBA",
    "C8": "12.222.333-4", "C9": "+56 41 222 0000",
    "C10": "CALLE DE PRUEBA 123", "C11": "SAN PEDRO DE LA PAZ",
    "C12": "CONCEPCIÓN", "C13": "correo@ejemplo.invalid",
    "C14": "CONSTRUCCIÓN", "D30": "Lomas Verdes",
    "DECLARANTE_NACIONALIDAD": "CHILENA",
}
TRABAJADOR = {
    "C17": "TRABAJADOR FICTICIO UNO", "C18": "11.111.111-1",
    "C19": "PERUANA", "C20": "1995-08-21", "C21": "SOLTERO",
    "C22": "CALLE FICTICIA 10", "C23": "CONCEPCIÓN",
    "C24": "CONCEPCIÓN", "C25": "trabajador@ejemplo.invalid",
    "C26": "999000111", "C29": "PINTOR", "D30": "Brisas de Junquillar",
    "C31": "42", "C32": "640000", "C34": "MENSUALMENTE",
    "C35": "CUENTA FICTICIA", "C38": "HABITAT", "C39": "FONASA",
    "C43": "Faenas Lomas Verdes", "C44": "SIN ASIGNACIÓN",
    "ANEXO_M4": "2027-01-31",
}
PTS_LISTOS = {"pintor", "albañil", "gasfiter"}
HOJAS = tuple(doc.hoja for doc in DOCUMENTOS)
CASOS = (
    "01_datos_completos",
    "02_sin_datos",
    "03_solo_empresa",
    "04_falta_primer_campo",
    "05_falta_ultimo_campo",
    "06_solo_espacios",
    "07_caracteres_acentuados",
    "08_datos_largos",
    "09_obra_brisa",
    "10_obra_concepcion",
    "11_sin_trabajador",
    "12_cargo_fuera_de_matriz",
    "13_declaracion_no_confirmada",
    "14_datos_no_se_mezclan",
    "15_pdf_corrupto_bloqueado",
)


def entradas(hoja, *, empresa=None, trabajador=None, cargo="PINTOR"):
    e = EMPRESA if empresa is None else empresa
    w = TRABAJADOR if trabajador is None else trabajador
    return preparar_datos(e, w, hoja=hoja, cargo_pts=cargo)


class CasosDocumentales(unittest.TestCase):
    maxDiff = None

    def comprobar(self, hoja: str, numero: int):
        self.assertIn(hoja, HOJAS)
        self.assertEqual(len(HOJAS), 10)
        corporativo = hoja in HOJAS_EMPRESA
        datos = entradas(hoja)
        base = documento_estado(hoja, datos, PTS_LISTOS,
                                tiene_trabajador=True, confirma_jurada=True)
        self.assertTrue(base["generable"], (hoja, base))

        if numero == 1:
            self.assertEqual(base["estado"], "Datos completos / revisar")
        elif numero == 2:
            res = documento_estado(hoja, {}, PTS_LISTOS,
                                   tiene_trabajador=False)
            self.assertFalse(res["generable"])
            self.assertTrue(res["faltan"])
        elif numero == 3:
            d = preparar_datos(EMPRESA, None, hoja=hoja,
                               cargo_pts="PINTOR")
            res = documento_estado(hoja, d, PTS_LISTOS,
                                   tiene_trabajador=False, confirma_jurada=True)
            self.assertEqual(res["generable"], corporativo)
            if not corporativo:
                self.assertEqual(res["estado"], "Requiere trabajador")
        elif numero == 4:
            primera = next(doc for doc in DOCUMENTOS if doc.hoja == hoja).requeridos[0]
            datos[primera] = ""
            res = documento_estado(hoja, datos, PTS_LISTOS,
                                   tiene_trabajador=True, confirma_jurada=True)
            self.assertFalse(res["generable"])
            self.assertIn(primera, res["faltan"])
        elif numero == 5:
            ultima = next(doc for doc in DOCUMENTOS if doc.hoja == hoja).requeridos[-1]
            datos[ultima] = ""
            res = documento_estado(hoja, datos, PTS_LISTOS,
                                   tiene_trabajador=True, confirma_jurada=True)
            self.assertFalse(res["generable"])
            self.assertIn(ultima, res["faltan"])
        elif numero == 6:
            primera = next(doc for doc in DOCUMENTOS if doc.hoja == hoja).requeridos[0]
            datos[primera] = "  \t "
            res = documento_estado(hoja, datos, PTS_LISTOS,
                                   tiene_trabajador=True, confirma_jurada=True)
            self.assertFalse(res["generable"])
        elif numero == 7:
            datos["C5"] = "CONSTRUCCIÓN ÑANDÚ ÁRBOLES"
            res = documento_estado(hoja, datos, PTS_LISTOS,
                                   tiene_trabajador=True, confirma_jurada=True)
            self.assertTrue(res["generable"])
            self.assertIn("ÑANDÚ", datos["C5"])
        elif numero == 8:
            datos["C10"] = "CALLE MUY LARGA " + "SUR " * 50
            res = documento_estado(hoja, datos, PTS_LISTOS,
                                   tiene_trabajador=True, confirma_jurada=True)
            self.assertTrue(res["generable"])
            self.assertLess(len(datos["C10"]), 800)
        elif numero in (9, 10):
            obra = "Brisas de Junquillar" if numero == 9 else "Concepción"
            datos["D30"] = obra
            res = documento_estado(hoja, datos, PTS_LISTOS,
                                   tiene_trabajador=True, confirma_jurada=True)
            self.assertTrue(res["generable"])
            self.assertEqual(datos["D30"], obra)
        elif numero == 11:
            res = documento_estado(hoja, datos, PTS_LISTOS,
                                   tiene_trabajador=False, confirma_jurada=True)
            self.assertEqual(res["generable"], corporativo)
            if not corporativo:
                self.assertEqual(res["estado"], "Requiere trabajador")
        elif numero == 12:
            datos["C29"] = "CARGO NO EXISTENTE"
            res = documento_estado(hoja, datos, PTS_LISTOS,
                                   tiene_trabajador=True, confirma_jurada=True)
            self.assertFalse(res["generable"] if hoja in
                {"PTS.", "IRL", "Contrato Imprimible"} else False)
            if hoja in {"PTS.", "IRL", "Contrato Imprimible"}:
                self.assertIn(res["estado"], {"PTS pendiente", "Cargo sin matriz"})
            else:
                self.assertTrue(res["generable"])
        elif numero == 13:
            res = documento_estado(hoja, datos, PTS_LISTOS,
                                   tiene_trabajador=True, confirma_jurada=False)
            if hoja == "DECLARACION JURADA":
                self.assertEqual(res["estado"], "Confirmar declaración")
                self.assertFalse(res["generable"])
            else:
                self.assertTrue(res["generable"])
        elif numero == 14:
            otro = dict(TRABAJADOR, C17="TRABAJADOR FICTICIO DOS",
                        C18="22.222.222-2", C19="ARGENTINA")
            uno = preparar_datos(EMPRESA, TRABAJADOR, hoja=hoja, cargo_pts="PINTOR")
            dos = preparar_datos(EMPRESA, otro, hoja=hoja, cargo_pts="PINTOR")
            if corporativo:
                self.assertNotIn("C17", uno)
                self.assertNotIn("C18", dos)
                if hoja == "DECLARACION JURADA":
                    self.assertEqual(uno["C19"], "CHILENA")
                    self.assertEqual(dos["C19"], "CHILENA")
            else:
                self.assertNotEqual(uno["C17"], dos["C17"])
                self.assertNotEqual(uno["C18"], dos["C18"])
                self.assertEqual(uno["C5"], dos["C5"])
        elif numero == 15:
            with self.assertRaises(ErrorDeConversion):
                validar_pdf(b"NO_ES_PDF", hoja)
        else:
            self.fail("Caso de prueba inexistente")


def crear_test(hoja, numero):
    def test(self):
        return self.comprobar(hoja, numero)
    test.__doc__ = "Validar " + hoja + ": " + CASOS[numero - 1]
    return test


for indice, hoja in enumerate(HOJAS, start=1):
    for numero in range(1, 16):
        nombre = "test_%02d_documento_%02d_%s" % (
            indice, numero, CASOS[numero - 1]
        )
        setattr(CasosDocumentales, nombre, crear_test(hoja, numero))


class PruebasDeSuite(unittest.TestCase):
    def test_cobertura_quince_por_cada_documento(self):
        pruebas = [m for m in dir(CasosDocumentales) if m.startswith("test_")]
        self.assertEqual(len(pruebas), 150)
        self.assertEqual(len(HOJAS), 10)
        for indice in range(1, 11):
            self.assertEqual(sum(p.startswith("test_%02d_documento_" % indice)
                                 for p in pruebas), 15)

    def test_con_empresa_se_muestran_diez_estados(self):
        items = estado_por_contexto(EMPRESA, None, PTS_LISTOS,
                                    cargo_pts="PINTOR", confirma_jurada=True)
        self.assertEqual(len(items), 10)
        self.assertEqual(sum(i["generable"] for i in items), 3)


if __name__ == "__main__":
    unittest.main()
