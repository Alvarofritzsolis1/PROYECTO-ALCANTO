"""Prueba REAL de clic/descarga en navegador Chromium.

No usa datos personales, requiere servidor Streamlit en ejecución.
Uso: python tests/browser_download_smoke.py --url http://127.0.0.1:8501
"""
from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
import re

from playwright.sync_api import sync_playwright, expect
from pypdf import PdfReader

VERSION = "2026.10.30-pdf-browser-v2"


def inspeccionar(pdf: bytes, empresa: str, obra: str) -> None:
    assert pdf.startswith(b"%PDF-"), "La descarga no es un PDF"
    assert len(pdf) > 1000, "La descarga está vacía"
    lector = PdfReader(BytesIO(pdf))
    assert 1 <= len(lector.pages) <= 10, "Cantidad de páginas anómala"
    texto = " ".join((p.extract_text() or "") for p in lector.pages)
    assert empresa in texto, "La empresa de prueba no aparece en el PDF"
    assert obra in texto, "La obra seleccionada no aparece en el PDF"
    assert "#NAME?" not in texto and "#REF!" not in texto, "Error de fórmula en PDF"


def prueba(url: str, destino: Path) -> None:
    destino.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(accept_downloads=True, viewport={"width": 1450, "height": 1100})
        page = context.new_page()
        page.set_default_timeout(30000)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            expect(page.get_by_text("Versión: " + VERSION)).to_be_visible(timeout=45000)

            # Descarga de diagnóstico: independiza los problemas del formulario.
            page.get_by_text("Diagnóstico de descarga PDF").click()
            expect(page.get_by_text(re.compile("Motor de PDF web:"))).to_be_visible()
            with page.expect_download(timeout=45000) as archivo:
                page.get_by_role("button", name="Descargar PDF ficticio de diagnóstico").click()
            descarga = archivo.value
            archivo_fisico = destino / "01_diagnostico_navegador.pdf"
            descarga.save_as(str(archivo_fisico))
            inspeccionar(archivo_fisico.read_bytes(), "EMPRESA FICTICIA ALCANTO", "Lomas Verdes")
            print("PASS: clic real + descarga PDF ficticio de diagnóstico")

            # Registro corporativo y generación a partir del formulario.
            valores = {
                "Nombre del empleador / empresa · C5": "EMPRESA DE EJEMPLO BROWSER SPA",
                "RUT empleador · C6": "76.111.222-3",
                "Representante legal · C7": "REPRESENTANTE DE EJEMPLO",
                "RUT representante legal · C8": "12.222.333-4",
                "Domicilio empleador · C10": "CALLE FICTICIA 100",
                "Ciudad empresa · C12": "CONCEPCIÓN",
                "Rubro de la empresa · C14": "CONSTRUCCIÓN",
            }
            for etiqueta, valor in valores.items():
                page.get_by_label(etiqueta, exact=True).fill(valor)

            combo_obra = page.get_by_test_id("stSelectbox").filter(
                has_text="Obra / faena principal · D30"
            )
            expect(combo_obra).to_have_count(1)
            print("HTML stSelectbox:", combo_obra.evaluate("(el) => el.outerHTML.slice(0, 2400)"), flush=True)
            obra_input = combo_obra.get_by_role("combobox")
            obra_input.fill("Lomas Verdes")
            print("obra expanded:", obra_input.get_attribute("aria-expanded"), flush=True)
            print("obra screen:", page.locator("body").inner_text()[-1400:], flush=True)
            obra_input.press("ArrowDown")
            obra_input.press("Enter")
            print("obra value:", obra_input.input_value(), flush=True)
            page.get_by_role("button", name="Guardar empresa", exact=True).click()
            expect(page.get_by_text("EMPRESA DE EJEMPLO BROWSER SPA").first).to_be_visible(timeout=30000)
            page.get_by_role("tab", name=re.compile("Documentación e impresión")).click()
            expect(page.get_by_text("Documentos para PDF")).to_be_visible()
            docs = page.get_by_test_id("stMultiSelect").filter(has_text="Documentos para PDF")
            expect(docs).to_have_count(1)
            print("HTML stMultiSelect:", docs.evaluate("(el) => el.outerHTML.slice(0, 2400)"), flush=True)
            botones = docs.get_by_role("button", name="Open")
            if botones.count():
                botones.first.click()
            else:
                docs.get_by_role("combobox").click()
                docs.get_by_role("combobox").fill("Inducción")
            print("Opciones disponibles:", page.get_by_role("option").all_text_contents(), flush=True)
            page.get_by_role("option", name="Inducción de prevención", exact=True).click()
            page.get_by_role("checkbox", name=re.compile("Entiendo que el PDF web es un BORRADOR")).check()
            boton = page.get_by_role("button", name="Generar PDF online para imprimir")
            expect(boton).to_be_enabled()
            boton.click()
            expect(page.get_by_text(re.compile("Se generaron 1 documentos"))).to_be_visible(timeout=45000)

            with page.expect_download(timeout=45000) as archivo_real:
                page.get_by_role("button", name="Descargar PDF listo para imprimir").click()
            pdf = archivo_real.value
            salida = destino / "02_induccion_desde_formulario.pdf"
            pdf.save_as(str(salida))
            inspeccionar(salida.read_bytes(), "EMPRESA DE EJEMPLO BROWSER SPA", "Lomas Verdes")
            print("PASS: formulario Streamlit + generación + descarga PDF real desde navegador")
        except Exception:
            page.screenshot(path=str(destino / "error_browser.png"), full_page=True)
            raise
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    parser.add_argument("--out", default="/tmp/alcanto_browser_smoke")
    args = parser.parse_args()
    prueba(args.url, Path(args.out))
