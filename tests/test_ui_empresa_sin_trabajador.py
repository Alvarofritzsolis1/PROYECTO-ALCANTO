"""Prueba de interfaz real de Streamlit: empresa sin registrar trabajador."""
from __future__ import annotations

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


class SmokeEmpresaSinTrabajador(unittest.TestCase):
    def test_empresa_sola_permite_ver_documentos(self):
        at = AppTest.from_file(APP, default_timeout=35).run()
        self.assertFalse(at.exception, str(at.exception))

        at.text_input(key="emp_C5").set_value("ALCANTO EMPRESA FICTICIA SpA")
        at.text_input(key="emp_C6").set_value("76.111.222-3")
        at.text_input(key="emp_C7").set_value("REPRESENTANTE DE PRUEBA")
        at.text_input(key="emp_C8").set_value("12.222.333-4")
        at.text_input(key="emp_C10").set_value("CALLE FICTICIA 1")
        at.text_input(key="emp_C12").set_value("CONCEPCIÓN")
        at.text_input(key="emp_C14").set_value("CONSTRUCCIÓN")
        at.text_input(key="emp_nacionalidad").set_value("CHILENA")
        at.selectbox(key="emp_obra").set_value("Lomas Verdes")
        at.form_submit_button[0].click().run()
        self.assertFalse(at.exception, str(at.exception))

        # Sin ningún trabajador, Streamlit debe mostrar el selector corporativo.
        candidatos = [x for x in at.selectbox if x.label == "Tipo de documentación"]
        self.assertEqual(len(candidatos), 1)
        self.assertEqual(candidatos[0].value, "")
        self.assertTrue(
            any("Solo documentos de empresa" in str(x.format_func("")) for x in candidatos)
        )

        # El formulario corporativo sí permite seleccionar un PTS por cargo.
        cargo = at.selectbox(key="cargo_pts_empresa")
        self.assertIn("PINTOR", list(cargo.options))
        cargo.set_value("PINTOR").run()
        self.assertFalse(at.exception, str(at.exception))

        # La declaración jurada requiere confirmación distinta de los datos laborales.
        checks = [x for x in at.checkbox if x.label.startswith("Confirmo, bajo mi responsabilidad")]
        self.assertEqual(len(checks), 1)
        self.assertFalse(checks[0].value)
        checks[0].check().run()
        self.assertFalse(at.exception, str(at.exception))

        # Después de completar la empresa, 3 hojas corporativas alcanzan datos mínimos.
        disponibles = [m for m in at.metric if m.label == "Documentos con datos mínimos"]
        self.assertEqual(len(disponibles), 1)
        self.assertEqual(str(disponibles[0].value), "3")

    def test_no_muestra_carga_excel_publica(self):
        at = AppTest.from_file(APP, default_timeout=35).run()
        self.assertFalse(at.exception, str(at.exception))
        self.assertEqual(len(at.file_uploader), 0)


if __name__ == "__main__":
    unittest.main()
