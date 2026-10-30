#!/usr/bin/python3
"""Exportador aislado de hojas del XLSX original a PDF mediante LibreOffice UNO.

Únicamente transforma valores y algunas fórmulas incompatibles en memoria.
El libro maestro se abre solo para lectura: nunca se guarda como XLSX.
Uso interno: /usr/bin/python3 scripts/uno_sheet_export.py master.xlsx inputs.json output.pdf
"""
from __future__ import annotations

from datetime import date
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

import uno
from com.sun.star.beans import PropertyValue

PRINT_RANGES = {
    "Contrato Imprimible": "A1:C38",
    "Anexo Traslado": "A1:C21",
    "Anexo extension contrato": "A1:M12",
    "INDUCCION PREVENCION": "A1:D483",
    "IRL": "A1:D180",
    "PTS.": "A1:G190",
    "ENTREGA PTS": "A1:I25",
    "Registros Entrega EPP": "A1:E25",
    "REGLAMENTO INTERNO": "A1:G12",
    "DECLARACION JURADA": "A1:G16",
}


def prop(key, value):
    p = PropertyValue()
    p.Name = key
    p.Value = value
    return p


def date_serial(iso: str) -> int:
    d = date.fromisoformat(iso)
    if not date(1901, 1, 1) <= d <= date(2100, 12, 31):
        raise ValueError("Fecha fuera de rango")
    return (d - date(1899, 12, 30)).days


def start_uno():
    from socket import socket, AF_INET, SOCK_STREAM
    with socket(AF_INET, SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    profile = "file:///tmp/alcanto_uno_" + uuid4().hex
    command = [
        "soffice", "-env:UserInstallation=" + profile, "--headless",
        "--accept=socket,host=127.0.0.1,port=" + str(port) + ";urp;StarOffice.ServiceManager",
        "--norestore", "--nodefault", "--nofirststartwizard",
    ]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local
    )
    for _ in range(100):
        try:
            ctx = resolver.resolve(
                "uno:socket,host=127.0.0.1,port=" + str(port) +
                ";urp;StarOffice.ComponentContext"
            )
            return process, ctx
        except Exception:
            if process.poll() is not None:
                break
            time.sleep(0.2)
    process.terminate()
    raise RuntimeError("No se pudo iniciar LibreOffice")


def apply_fields(doc, payload):
    source = doc.Sheets.getByName("Datos Contrato")
    for key, text in payload["entradas"].items():
        cell = source.getCellRangeByName(key)
        if key == "C20" and text:
            cell.setValue(date_serial(text))
        elif key == "C32" and text:
            cell.setValue(int(text))
        elif text:
            cell.setString(str(text))
        else:
            cell.setString("")
    # Excel LET/TEXTSPLIT no funciona igual en LibreOffice. Solo en memoria.
    source.getCellRangeByName("C33").setString(payload.get("renta_letras", ""))
    date_ext = doc.Sheets.getByName("Anexo extension contrato").getCellRangeByName("M4")
    due = payload.get("ANEXO_M4", "")
    date_ext.setValue(date_serial(due)) if due else date_ext.setString("")


def patch_unsupported_formulas(sheet, address):
    region = sheet.getCellRangeByName(address).RangeAddress
    for row in range(region.StartRow, region.EndRow + 1):
        for col in range(region.StartColumn, region.EndColumn + 1):
            cell = sheet.getCellByPosition(col, row)
            original = cell.getFormula()
            formula = original.replace("_xlfn._longtext(", "CONCATENATE(")
            if sheet.Name == "Contrato Imprimible" and row == 12 and col == 0:
                # 640000.000 en la configuración regional original => 640.000 pesos.
                formula = formula.replace(
                    "TEXT($'Datos Contrato'.C32; \"#.##0\")",
                    "SUBSTITUTE(TEXT($'Datos Contrato'.C32; \"#,##0\"); \",\"; \".\")",
                )
            if formula != original:
                cell.setFormula(formula)


def check_formulas(sheet, address):
    region = sheet.getCellRangeByName(address).RangeAddress
    for row in range(region.StartRow, region.EndRow + 1):
        for col in range(region.StartColumn, region.EndColumn + 1):
            if sheet.getCellByPosition(col, row).getError():
                raise ValueError("Fórmula sin calcular, PDF rechazado")


def export_one(master: Path, request: Path, output: Path):
    data = json.loads(request.read_text(encoding="utf-8"))
    name = data["hoja"]
    if name not in PRINT_RANGES:
        raise ValueError("Hoja de exportación inválida")
    process, ctx = start_uno()
    doc = None
    try:
        desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
        doc = desktop.loadComponentFromURL(
            uno.systemPathToFileUrl(str(master.resolve())), "_blank", 0,
            (prop("Hidden", True), prop("ReadOnly", True),
             prop("UpdateDocMode", 3), prop("MacroExecutionMode", 4)),
        )
        if doc is None or len(doc.Sheets.ElementNames) != 17:
            raise ValueError("Modelo Excel ALCANTO incompatible")
        apply_fields(doc, data)
        sheet = doc.Sheets.getByName(name)
        region = sheet.getCellRangeByName(PRINT_RANGES[name])
        patch_unsupported_formulas(sheet, PRINT_RANGES[name])
        doc.calculateAll()
        check_formulas(sheet, PRINT_RANGES[name])
        sheet.setPrintAreas((region.RangeAddress,))
        doc.CurrentController.setActiveSheet(sheet)
        doc.CurrentController.select(region)
        # Selection impide imprimir las 1.048.576 filas de la matriz auxiliar.
        pdf_filter = uno.Any("[]com.sun.star.beans.PropertyValue", (
            prop("Selection", region), prop("ExportBookmarks", False)
        ))
        doc.storeToURL(
            uno.systemPathToFileUrl(str(output.resolve())),
            (prop("FilterName", "calc_pdf_Export"),
             prop("Overwrite", True), prop("FilterData", pdf_filter)),
        )
        if not output.is_file() or output.stat().st_size < 1000:
            raise ValueError("Salida PDF vacía")
    finally:
        if doc:
            try:
                doc.close(True)
            except Exception:
                pass
        process.terminate()
        try:
            process.wait(timeout=6)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(2)
    try:
        export_one(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    except Exception as exc:
        # No registrar jamás contenido, RUT ni datos personales.
        print("ALCANTO_UNO_ERROR:" + type(exc).__name__, file=sys.stderr)
        raise SystemExit(1)
