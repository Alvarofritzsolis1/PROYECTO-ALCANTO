"""Aspose.Cells Cloud API v4.0: motor real en la nube, sin instalar Excel.

Se requiere cuenta comercial/credenciales de Aspose. Solo se envían los bytes de
la COPIA por HTTPS para una hoja, sin almacenar archivos en el repo.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import re
from urllib.parse import quote

import requests
from pypdf import PdfReader

PDF_ERR = re.compile(r"#(?:NAME\?|NOMBRE\?|¿NOMBRE\?|REF!|VALUE!|¡VALOR!|DIV/0!|NUM!|N/A|CALC!)", re.I)
ASPOSE_HOST = "https://api.aspose.cloud"


class ErrorDeConversion(RuntimeError):
    pass


@dataclass(frozen=True)
class ResultadoPdf:
    contenido: bytes
    paginas: int
    texto_extraible: bool


class AsposeCellsCloud:
    def __init__(self, client_id: str, client_secret: str):
        if not client_id or not client_secret:
            raise ErrorDeConversion("Faltan credenciales de Aspose.Cells Cloud en los secretos de Streamlit.")
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None
        self.session = requests.Session()

    def _autenticar(self) -> str:
        if self._token:
            return self._token
        try:
            response = self.session.post(
                ASPOSE_HOST + "/connect/token",
                data={"grant_type": "client_credentials", "client_id": self.client_id,
                      "client_secret": self.client_secret},
                headers={"Accept": "application/json"}, timeout=(10, 25),
            )
            response.raise_for_status()
            self._token = response.json()["access_token"]
        except (requests.RequestException, ValueError, KeyError) as exc:
            raise ErrorDeConversion("La cuenta de Aspose no pudo autenticarse. Revisar las credenciales y el servicio.") from exc
        return self._token

    def convertir_hoja(self, workbook: bytes, hoja: str) -> ResultadoPdf:
        if not hoja or len(hoja) > 100 or '/' in hoja or '\\' in hoja:
            raise ErrorDeConversion("Nombre de hoja inválido.")
        token = self._autenticar()
        try:
            respuesta = self.session.put(
                ASPOSE_HOST + "/v4.0/cells/convert/worksheet/pdf",
                params={"worksheet": hoja, "region": "es-CL",
                        "AutoRowsFit": "false", "AutoColumnsFit": "false"},
                data={}, files={"Spreadsheet": (
                    "ALCANTO_copia_temporal.xlsx", workbook,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                headers={"Authorization": "Bearer " + token,
                         "Accept": "application/octet-stream"},
                timeout=(20, 160),
            )
            if respuesta.status_code != 200:
                # No incluir respuesta completa porque un proveedor podría repetir datos personales.
                raise ErrorDeConversion(
                    "La conversión de Aspose falló (HTTP " + str(respuesta.status_code)
                    + "). Comprobar plan, cuota, tamaño y compatibilidad de fórmulas.")
            return validar_pdf(respuesta.content, hoja)
        except requests.Timeout as exc:
            raise ErrorDeConversion("El motor cloud agotó el tiempo de conversión. Reintentar con un documento.") from exc
        except requests.RequestException as exc:
            raise ErrorDeConversion("Falló la conexión HTTPS con Aspose.Cells Cloud.") from exc


def validar_pdf(contenido: bytes, hoja: str) -> ResultadoPdf:
    if not contenido.startswith(b"%PDF-"):
        raise ErrorDeConversion("El servicio no entregó un archivo PDF válido.")
    if len(contenido) > 40 * 1024 * 1024:
        raise ErrorDeConversion("El PDF es demasiado grande para una descarga segura.")
    try:
        reader = PdfReader(BytesIO(contenido), strict=False)
        total = len(reader.pages)
        if not (1 <= total <= 75):
            raise ErrorDeConversion("El PDF tiene un número de páginas inesperado: " + str(total))
        extraible = False
        for i, page in enumerate(reader.pages):
            texto = page.extract_text() or ""
            extraible |= bool(texto.strip())
            match = PDF_ERR.search(texto)
            if match:
                raise ErrorDeConversion(
                    f"PDF bloqueado: se encontró error de fórmula {match.group(0)} "
                    f"en {hoja}, página {i+1}. El motor remoto no reprodujo el Excel correctamente.")
        return ResultadoPdf(contenido, total, extraible)
    except ErrorDeConversion:
        raise
    except Exception as exc:
        raise ErrorDeConversion("No se pudo comprobar la integridad del PDF recibido.") from exc
