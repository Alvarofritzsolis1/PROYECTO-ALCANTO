"""Regresión: aplicación web sin carga de Excel para el visitante."""
from pathlib import Path
import unittest

APP = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


class FormularioOnline(unittest.TestCase):
    def test_no_pide_cargar_excel(self):
        self.assertNotIn("st.file_uploader(", APP)

    def test_no_pide_password(self):
        self.assertNotIn("ALCANTO_APP_PASSWORD", APP)
        self.assertNotIn("def ingreso()", APP)

    def test_plantilla_es_recurso_interno(self):
        self.assertIn("def almacen_plantilla()", APP)
        self.assertIn("ALCANTO_MODELO.xlsx", APP)

    def test_solo_exporta_si_motor_y_modelo_estan_listos(self):
        self.assertIn("template and seleccion and avisar and cloud_id and cloud_key", APP)

    def test_formularios_siguen_disponibles_sin_modelo(self):
        self.assertIn('catalogo={"cargos":[], "obras":[], "pts_completos":set()}', APP)


if __name__ == "__main__":
    unittest.main()
