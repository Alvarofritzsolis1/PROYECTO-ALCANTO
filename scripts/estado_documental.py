#!/usr/bin/env python3
"""Informe local y de solo lectura sobre disponibilidad documental de PROYECTO ALCANTO.

No modifica el Excel ni revela nombres, RUT u otros valores personales.
Uso: python scripts/estado_documental.py "ruta/al/archivo.xlsx" --salida estado.md
"""
from __future__ import annotations

import argparse
from pathlib import PurePosixPath, Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
P = "{http://schemas.openxmlformats.org/package/2006/relationships}"

# Condiciones mínimas de entrada para diagnosticar qué documentos conviene revisar.
# NO constituyen requisitos legales exhaustivos ni prueban que un documento esté firmado.
REQUISITOS = {
    "Contrato Imprimible": ["C5", "C6", "C7", "C8", "C17", "C18", "C29", "D30", "C31", "C32", "C34", "C36", "C37", "C38", "C39", "C40"],
    "Anexo Traslado": ["C5", "C6", "C17", "C18", "C29", "D30", "C43"],
    "Anexo extension contrato": ["C5", "C6", "C7", "C8", "C17", "C18", "C36", "C37"],
    "INDUCCION PREVENCION": ["C5", "C6", "C7", "C8", "C9", "C10", "C13", "C14", "D30"],
    "IRL": ["C5", "C6", "C17", "C18", "C29", "D30"],
    "PTS.": ["C5", "C6", "C7", "C8", "C10", "C29"],
    "ENTREGA PTS": ["C5", "C6", "C12", "C17", "C18", "C29"],
    "Registros Entrega EPP": ["C5", "C6", "C17", "C18", "C29", "D30"],
    "REGLAMENTO INTERNO": ["C5", "C6", "C12", "C17", "C18"],
    "DECLARACION JURADA": ["C5", "C6", "C7", "C8", "C14", "D30"],
}
CAMPOS_PTS = [chr(c) for c in range(ord("D"), ord("T") + 1)]


def leer_celdas(z: ZipFile, ruta: str, cadenas: list[str]) -> dict[str, tuple[str | None, bool]]:
    hoja = ET.fromstring(z.read(ruta))
    resultado = {}
    for celda in hoja.iter(M + "c"):
        direccion = celda.attrib.get("r")
        if not direccion:
            continue
        formula = celda.find(M + "f") is not None
        v = celda.find(M + "v")
        valor = v.text if v is not None else None
        if celda.attrib.get("t") == "s" and valor is not None:
            valor = cadenas[int(valor)]
        elif celda.attrib.get("t") == "inlineStr":
            inline = celda.find(M + "is")
            valor = "".join(t.text or "" for t in inline.iter(M + "t")) if inline is not None else ""
        resultado[direccion] = (valor, formula)
    return resultado


def libro(z: ZipFile):
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    targets = {e.get("Id"): e.get("Target") for e in rels}
    cadenas = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(M + "si"):
            cadenas.append("".join(t.text or "" for t in si.iter(M + "t")))
    rutas = {}
    for hoja in wb.findall(".//" + M + "sheet"):
        target = targets[hoja.attrib[R + "id"]].lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        rutas[hoja.attrib["name"]] = str(PurePosixPath(target))
    return rutas, cadenas


def tiene_dato(celdas: dict, direccion: str) -> bool:
    valor, formula = celdas.get(direccion, (None, False))
    return formula or valor is not None and str(valor).strip() != ""


def pts_completo(matriz: dict, cargo: str) -> tuple[bool, str]:
    encontrado = False
    for fila in range(2, 28):
        clave = matriz.get("A" + str(fila), ("", False))[0] or ""
        if str(clave).strip().casefold() == cargo.strip().casefold():
            encontrado = True
            faltantes = [col for col in CAMPOS_PTS if not tiene_dato(matriz, col + str(fila))]
            if not faltantes:
                return True, "17/17 campos técnicos con contenido"
    if not encontrado:
        return False, "cargo no encontrado en la clave A de MATRIZ PTS"
    return False, "contenido técnico D:T incompleto para el cargo seleccionado"


def informe(ruta: Path) -> str:
    with ZipFile(ruta) as z:
        rutas, cadenas = libro(z)
        necesarias = ["Datos Contrato", "MATRIZ PTS", "Anexo extension contrato"]
        faltan_hojas = [nombre for nombre in necesarias if nombre not in rutas]
        if faltan_hojas:
            raise ValueError("Hojas faltantes: " + ", ".join(faltan_hojas))
        datos = leer_celdas(z, rutas["Datos Contrato"], cadenas)
        matriz = leer_celdas(z, rutas["MATRIZ PTS"], cadenas)
        anexo = leer_celdas(z, rutas["Anexo extension contrato"], cadenas)
    cargo = str(datos.get("C29", ("", False))[0] or "")
    pts_ok, comentario_pts = pts_completo(matriz, cargo) if cargo else (False, "cargo sin informar")
    lineas = [
        "# Estado documental — PROYECTO ALCANTO",
        "",
        "> Evaluación orientativa de datos mínimos; no reemplaza revisión legal, preventiva, de firmas ni de impresión.",
        "> Los valores personales no se incluyen en este reporte.",
        "",
        "| Hoja de salida | Estado | Campos por completar / condición |",
        "|---|---|---|",
    ]
    for nombre, campos in REQUISITOS.items():
        faltantes = [ref for ref in campos if not tiene_dato(datos, ref)]
        if nombre == "Anexo extension contrato" and not tiene_dato(anexo, "M4"):
            faltantes.append("Anexo extension contrato!M4")
        if faltantes:
            estado = "FALTAN DATOS"
            detalle = ", ".join(faltantes)
        elif nombre == "PTS." and not pts_ok:
            estado = "PTS PENDIENTE"
            detalle = comentario_pts
        else:
            estado = "GENERABLE / REVISAR"
            detalle = "Campos mínimos presentes; verificar contenido y firmas"
        lineas.append(f"| {nombre} | {estado} | {detalle} |")
    lineas.extend([
        "", "## Notas", "",
        "- Una plantilla completa no acredita entrega efectiva, capacitación, firma ni cumplimiento.",
        "- Los PTS requieren que MATRIZ PTS tenga contenido técnico por cargo.",
        "- Esta utilidad es de **solo lectura**: no escribe dentro del .xlsx ni crea PDFs.",
        "- Para un PDF o impresión, utilizar el Excel actual y validar visualmente el resultado.",
        "",
    ])
    return "\n".join(lineas)


def main():
    p = argparse.ArgumentParser(description="Estado de documentos de ALCANTO sin modificar el Excel")
    p.add_argument("excel", type=Path, help="Ruta al Excel original o a una copia privada")
    p.add_argument("--salida", type=Path, help="Ruta donde guardar reporte Markdown; si se omite se imprime")
    args = p.parse_args()
    salida = informe(args.excel)
    if args.salida:
        args.salida.write_text(salida, encoding="utf-8")
        print("Informe de solo lectura guardado en " + str(args.salida))
    else:
        print(salida)


if __name__ == "__main__":
    main()
