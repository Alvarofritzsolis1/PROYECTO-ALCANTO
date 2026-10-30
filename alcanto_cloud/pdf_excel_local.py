"""Conversión PDF del XLSX original en servidor Linux sin Excel ni Aspose.

Requiere LibreOffice Calc y python3-uno, más el XLSX maestro privado ya
disponible en el servidor. Nunca cambia ni devuelve el XLSX. Falla en cerrado.
"""
from __future__ import annotations

from functools import lru_cache
from io import BytesIO
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from pypdf import PdfReader

from .catalog import CAMPOS, DOCUMENTOS
from .pdf_service import ResultadoPdf, validar_pdf, verificar_identidad_pdf, ErrorDeConversion
from .workbook import verificar_plantilla, _abrir, _shared_strings, _leer_celdas

HOJAS = frozenset(d.hoja for d in DOCUMENTOS)
MAX_PAGINAS = {
    "Contrato Imprimible": 3,
    "Anexo Traslado": 3,
    "Anexo extension contrato": 3,
    "INDUCCION PREVENCION": 18,
    "IRL": 10,
    "PTS.": 9,
    "ENTREGA PTS": 3,
    "Registros Entrega EPP": 3,
    "REGLAMENTO INTERNO": 3,
    "DECLARACION JURADA": 3,
}


class ErrorExcelLocal(ErrorDeConversion):
    pass


@lru_cache(maxsize=1)
def motor_excel_disponible() -> bool:
    if not shutil.which("soffice") or not Path("/usr/bin/python3").is_file():
        return False
    try:
        r = subprocess.run(
            ["/usr/bin/python3", "-c", "import uno"], timeout=8, capture_output=True,
        )
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


UNIDADES = ("", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve")
ESPECIALES = {
    10: "diez", 11: "once", 12: "doce", 13: "trece", 14: "catorce",
    15: "quince", 16: "dieciséis", 17: "diecisiete", 18: "dieciocho",
    19: "diecinueve", 20: "veinte", 21: "veintiuno", 22: "veintidós",
    23: "veintitrés", 24: "veinticuatro", 25: "veinticinco",
    26: "veintiséis", 27: "veintisiete", 28: "veintiocho", 29: "veintinueve",
}
DECENAS = {
    30: "treinta", 40: "cuarenta", 50: "cincuenta",
    60: "sesenta", 70: "setenta", 80: "ochenta", 90: "noventa",
}
CENTENAS = {
    200: "doscientos", 300: "trescientos", 400: "cuatrocientos",
    500: "quinientos", 600: "seiscientos", 700: "setecientos",
    800: "ochocientos", 900: "novecientos",
}


def _menos_mil(n: int) -> str:
    if n == 0:
        return ""
    if n == 100:
        return "cien"
    if n >= 100:
        prefijo = "ciento" if n < 200 else CENTENAS[n // 100 * 100]
        return prefijo + (" " + _menos_mil(n % 100) if n % 100 else "")
    if n in ESPECIALES:
        return ESPECIALES[n]
    if n < 10:
        return UNIDADES[n]
    d = n // 10 * 10
    return DECENAS[d] + (" y " + UNIDADES[n % 10] if n % 10 else "")


def _apocope(text: str) -> str:
    if text.endswith("veintiuno"):
        return text[:-9] + "veintiún"
    if text.endswith(" y uno"):
        return text[:-6] + " y un"
    if text.endswith("uno"):
        return text[:-3] + "un"
    return text


def _entero(n: int) -> str:
    if n == 0:
        return "cero"
    if n < 1000:
        return _menos_mil(n)
    if n < 1_000_000:
        miles, resto = divmod(n, 1000)
        primero = "mil" if miles == 1 else _apocope(_entero(miles)) + " mil"
    elif n < 1_000_000_000:
        millones, resto = divmod(n, 1_000_000)
        primero = "un millón" if millones == 1 else _apocope(_entero(millones)) + " millones"
    elif n < 1_000_000_000_000:
        miles_m, resto = divmod(n, 1_000_000_000)
        primero = "mil millones" if miles_m == 1 else _apocope(_entero(miles_m)) + " mil millones"
    else:
        raise ValueError("Sueldo fuera del intervalo admitido")
    return primero + (" " + _entero(resto) if resto else "")


def pesos_en_palabras(valor: str) -> str:
    if not re.fullmatch(r"\d{1,12}", valor or ""):
        raise ValueError("Sueldo base inválido: usa pesos enteros")
    n = int(valor)
    if not 1 <= n < 1_000_000_000_000:
        raise ValueError("Sueldo fuera del intervalo admitido")
    if n == 1:
        return "Un peso."
    letras = _apocope(_entero(n))
    if n >= 1_000_000 and n % 1_000_000 == 0:
        letras += " de"
    return letras[0].upper() + letras[1:] + " pesos."


def exportar_pdf_excel(template: bytes, hoja: str, datos: dict[str, str], *,
                       timeout: int = 120) -> ResultadoPdf:
    """Exporta la hoja original elegida y valida que el PDF es legible y seguro."""
    if hoja not in HOJAS:
        raise ErrorExcelLocal("Documento desconocido")
    if not motor_excel_disponible():
        raise ErrorExcelLocal("LibreOffice/UNO no están instalados en Streamlit")
    verificar_plantilla(template)
    if any(k not in CAMPOS and k != "ANEXO_M4" for k in datos):
        raise ErrorExcelLocal("Se intentó modificar un campo no autorizado")
    entradas = {ref: str(datos.get(ref, "")).strip() for ref in CAMPOS}
    if any(len(v) > 800 for v in entradas.values()):
        raise ErrorExcelLocal("Un campo supera el límite de texto")
    renta = entradas["C32"]
    palabras = pesos_en_palabras(renta) if renta else ""
    vencimiento = str(datos.get("ANEXO_M4", "")).strip()
    solicitud = {
        "hoja": hoja, "entradas": entradas,
        "renta_letras": palabras, "ANEXO_M4": vencimiento,
    }
    antiguo = ""
    if hoja in {
        "Contrato Imprimible", "Anexo Traslado", "Anexo extension contrato",
        "IRL", "ENTREGA PTS", "Registros Entrega EPP", "REGLAMENTO INTERNO",
    }:
        with _abrir(template) as z:
            antiguo = _leer_celdas(
                z, "xl/worksheets/sheet1.xml", ["C17"], _shared_strings(z),
            )["C17"]
    worker = Path(__file__).resolve().parents[1] / "scripts" / "uno_sheet_export.py"
    if not worker.is_file():
        raise ErrorExcelLocal("Falta el script de impresión UNO")
    with tempfile.TemporaryDirectory(prefix="alcanto_doc_") as temp:
        d = Path(temp)
        modelo = d / "modelo.xlsx"
        entrada = d / "solicitud.json"
        salida = d / "impresion.pdf"
        modelo.write_bytes(template)
        entrada.write_text(json.dumps(solicitud, ensure_ascii=False), encoding="utf-8")
        try:
            proc = subprocess.run(
                ["/usr/bin/python3", str(worker), str(modelo), str(entrada), str(salida)],
                timeout=timeout, capture_output=True, text=True,
            )
        except subprocess.TimeoutExpired as exc:
            raise ErrorExcelLocal("El recálculo excedió el tiempo permitido") from exc
        if proc.returncode or not salida.is_file():
            raise ErrorExcelLocal("El motor no pudo calcular este documento. Descarga bloqueada.")
        pdf = salida.read_bytes()
    resultado = validar_pdf(pdf, hoja)
    if resultado.paginas > MAX_PAGINAS[hoja]:
        raise ErrorExcelLocal("Se detectó un número anómalo de páginas. PDF bloqueado.")
    texto = " ".join(p.extract_text() or "" for p in PdfReader(BytesIO(pdf)).pages)
    if "1899" in texto or "1900" in texto:
        raise ErrorExcelLocal("Fecha de cálculo incorrecta: PDF bloqueado.")
    if hoja == "Contrato Imprimible" and renta:
        esperado = "$" + f"{int(renta):,}".replace(",", ".")
        if esperado not in texto or palabras.lower().rstrip(".") not in texto.lower():
            raise ErrorExcelLocal("Sueldo y sueldo en letras no coinciden. PDF bloqueado.")
    if antiguo or entradas.get("C17"):
        verificar_identidad_pdf(
            resultado, hoja, entradas["C17"], entradas["C18"], antiguo,
        )
    return resultado
