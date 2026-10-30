"""Prueba de punta a punta: formulario Streamlit -> PDF en ZIP sin Excel/Aspose."""
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import unittest

from pypdf import PdfReader
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


class PlataformaImpresionSinClaves(unittest.TestCase):
    def test_empresa_imprime_induccion_sin_plantilla(self):
        app = AppTest.from_file(APP, default_timeout=45).run()
        self.assertFalse(app.exception, str(app.exception))
        app.text_input(key="emp_C5").set_value("EMPRESA DE DEMOSTRACIÓN SpA")
        app.text_input(key="emp_C6").set_value("76.111.222-3")
        app.text_input(key="emp_C7").set_value("REPRESENTANTE DEMO")
        app.text_input(key="emp_C8").set_value("12.222.333-4")
        app.text_input(key="emp_C10").set_value("CALLE FICTICIA 10")
        app.text_input(key="emp_C12").set_value("CONCEPCIÓN")
        app.text_input(key="emp_C14").set_value("OBRAS CIVILES")
        app.selectbox(key="emp_obra").set_value("Lomas Verdes")
        app.form_submit_button[0].click().run()
        self.assertFalse(app.exception, str(app.exception))
        opciones = [w for w in app.checkbox if w.label == "Inducción de prevención"]
        self.assertEqual(len(opciones), 1)
        opciones[0].check().run()
        app.checkbox(key="confirmacion_aspose").check().run()
        botones = [w for w in app.button if w.label == "Generar PDF online para imprimir"]
        self.assertEqual(len(botones), 1)
        self.assertFalse(botones[0].disabled)
        botones[0].click().run()
        self.assertFalse(app.exception, str(app.exception))
        data=app.session_state["pdf_generados"]
        with ZipFile(BytesIO(data)) as z:
            pdfnames=[n for n in z.namelist() if n.lower().endswith(".pdf")]
            self.assertEqual(len(pdfnames), 1)
            blob=z.read(pdfnames[0])
            self.assertTrue(blob.startswith(b"%PDF-"))
            reader=PdfReader(BytesIO(blob))
            self.assertGreater(len(reader.pages), 0)
            text=" ".join(p.extract_text() or "" for p in reader.pages)
            self.assertIn("EMPRESA DE DEMOSTRACIÓN", text)
            self.assertIn("Lomas Verdes", text)
            self.assertIn("Av. Jorge Alessandri", text)
            self.assertNotIn("TRABAJADOR SINTÉTICO", text)


if __name__ == "__main__":
    unittest.main()
