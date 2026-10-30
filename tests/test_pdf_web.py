"""Pruebas de 10 PDFs reales, sin Aspose, Microsoft Excel o archivos privados.

Para cada documento se comprueba integridad binaria, texto extraíble,
ausencia de nombres ajenos y presencia de información de prueba.
"""
from datetime import date
from io import BytesIO
import unittest

from pypdf import PdfReader

from alcanto_cloud.catalog import DOCUMENTOS, DIRECCIONES_OBRA
from alcanto_cloud.documentos import preparar_datos
from alcanto_cloud.pdf_service import validar_pdf, verificar_identidad_pdf
from alcanto_cloud.pdf_web import generar_pdf_web, ErrorPDFWeb

EMPRESA = {
    "C5": "CONSTRUCTORA DEMOSTRACIÓN SpA",
    "C6": "76.111.222-3", "C7": "REPRESENTANTE FICTICIO",
    "C8": "12.222.333-4", "C9": "411234567",
    "C10": "AVENIDA DE PRUEBA 101", "C11": "CONCEPCIÓN",
    "C12": "CONCEPCIÓN", "C13": "no-real@ejemplo.invalid",
    "C14": "CONSTRUCCIÓN", "D30": "Brisas de Junquillar",
    "DECLARANTE_NACIONALIDAD": "CHILENA",
}
TRABAJADOR = {
    "C17": "TRABAJADOR SINTÉTICO A", "C18": "11.111.111-1",
    "C19": "CHILENA", "C20": "1994-02-02", "C21": "SOLTERO",
    "C22": "CASA DE EJEMPLO 1", "C23": "CONCEPCIÓN",
    "C24": "CONCEPCIÓN", "C25": "no-real2@ejemplo.invalid",
    "C26": "912345678", "C29": "PINTOR", "D30": "Lomas Verdes",
    "C31": "42", "C32": "640000", "C34": "MENSUALMENTE",
    "C35": "CUENTA FICTICIA", "C38": "HABITAT", "C39": "FONASA",
    "C43": "Faenas Brisas de Junquillar", "C44": "SIN LOCOMOCIÓN",
    "ANEXO_M4": "2027-04-30",
}
FECHA = date(2026, 11, 1)
CORP = {"INDUCCION PREVENCION", "PTS.", "DECLARACION JURADA"}


class PdfPorDocumento(unittest.TestCase):
    def verificar_pdf(self, doc):
        datos = preparar_datos(EMPRESA, TRABAJADOR, hoja=doc.hoja, cargo_pts="PINTOR")
        pdf = generar_pdf_web(doc.hoja, datos, fecha=FECHA, confirma_jurada=True)
        self.assertTrue(pdf.startswith(b"%PDF-"))
        info = validar_pdf(pdf, doc.hoja)
        self.assertGreater(len(pdf), 1600)
        self.assertGreaterEqual(info.paginas, 1)
        self.assertLessEqual(info.paginas, 8)
        texto = "\n".join(p.extract_text() or "" for p in PdfReader(BytesIO(pdf)).pages)
        self.assertIn("CONSTRUCTORA DEMOSTRACIÓN", texto)
        self.assertIn("76.111.222-3", texto)
        if doc.hoja not in CORP:
            self.assertIn("TRABAJADOR SINTÉTICO A", texto)
            self.assertIn("11.111.111-1", texto)
            verificar_identidad_pdf(info, doc.hoja, "TRABAJADOR SINTÉTICO A",
                                     "11.111.111-1", "TRABAJADOR ANTIGUO")
        else:
            self.assertNotIn("TRABAJADOR SINTÉTICO A", texto)
            self.assertNotIn("11.111.111-1", texto)
        self.assertNotIn("CLAUDIO NAVARRO", texto)
        self.assertNotIn("#NAME?", texto)
        return texto

    def test_las_diez_hojas_tienen_pdf(self):
        self.assertEqual(len(DOCUMENTOS), 10)
        for doc in DOCUMENTOS:
            with self.subTest(hoja=doc.hoja):
                self.verificar_pdf(doc)

    def test_contrato_sueldo_obra_y_fechas(self):
        texto = self.verificar_pdf(DOCUMENTOS[0])
        self.assertIn("$640.000", texto)
        self.assertIn("Lomas Verdes", texto)
        self.assertIn(DIRECCIONES_OBRA["Lomas Verdes"], texto)
        self.assertIn("30 de noviembre de 2026", texto)

    def test_empresa_sola_genera_tres_documentos(self):
        for hoja in CORP:
            with self.subTest(hoja=hoja):
                datos = preparar_datos(EMPRESA, None, hoja=hoja, cargo_pts="PINTOR")
                pdf = generar_pdf_web(hoja, datos, fecha=FECHA,
                                     confirma_jurada=True)
                self.assertTrue(pdf.startswith(b"%PDF-"))

    def test_declaracion_sin_confirmacion_bloqueada(self):
        datos = preparar_datos(EMPRESA, None, hoja="DECLARACION JURADA")
        with self.assertRaises(ErrorPDFWeb):
            generar_pdf_web("DECLARACION JURADA", datos, fecha=FECHA)

    def test_pts_incompleto_bloqueado(self):
        datos = preparar_datos(EMPRESA, None, hoja="PTS.", cargo_pts="CARPINTERO")
        with self.assertRaises(ErrorPDFWeb):
            generar_pdf_web("PTS.", datos, fecha=FECHA)

    def test_renta_invalida_bloqueada(self):
        datos = preparar_datos(EMPRESA, TRABAJADOR, hoja="Contrato Imprimible")
        datos["C32"] = "NO NUMÉRICO"
        with self.assertRaises(ErrorPDFWeb):
            generar_pdf_web("Contrato Imprimible", datos, fecha=FECHA)

    def test_datos_faltantes_bloqueados(self):
        datos = preparar_datos(EMPRESA, TRABAJADOR, hoja="Contrato Imprimible")
        datos["C18"] = ""
        with self.assertRaises(ErrorPDFWeb):
            generar_pdf_web("Contrato Imprimible", datos, fecha=FECHA)

    def test_pdf_obra_corporativa_sin_trabajador(self):
        datos = preparar_datos(EMPRESA, None, hoja="INDUCCION PREVENCION")
        pdf = generar_pdf_web("INDUCCION PREVENCION", datos, fecha=FECHA)
        texto = " ".join((p.extract_text() or "") for p in PdfReader(BytesIO(pdf)).pages)
        self.assertIn(DIRECCIONES_OBRA["Brisas de Junquillar"], texto)
        self.assertNotIn("TRABAJADOR", texto.upper().split("CONTRATISTA")[0])


if __name__ == "__main__":
    unittest.main()
