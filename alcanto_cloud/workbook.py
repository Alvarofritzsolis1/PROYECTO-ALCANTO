"""Operaciones XLSX con ZIP/XML: editar entradas, SIN tocar ninguna fórmula.

No usa openpyxl, LibreOffice ni Excel. Solo modifica el XML de celdas autorizadas
sobre una COPIA EN MEMORIA. Las fórmulas, estilos y demás hojas permanecen iguales.
La evaluación de las fórmulas corresponde al motor remoto contratado.
"""
from __future__ import annotations

from datetime import date
from hashlib import sha256
from io import BytesIO
import re
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED, BadZipFile

from .catalog import CAMPOS, DOCUMENTOS

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
XML_MAX_UNCOMPRESSED = 125 * 1024 * 1024
XLSX_MAX_BYTES = 25 * 1024 * 1024
FORMULA_ERRS = ("#REF!", "#VALUE!", "#NAME?", "#NOMBRE?", "#¡VALOR!", "#¿NOMBRE?", "#DIV/0!", "#N/A")


class PlantillaInvalida(ValueError):
    pass


def _celda(ref: str) -> re.Pattern[str]:
    return re.compile(r'(<c\b(?=[^>]*\br="' + re.escape(ref) + r'")[^>]*>)(.*?)(</c>)', re.DOTALL)


def _abrir(datos: bytes) -> ZipFile:
    if not isinstance(datos, bytes) or len(datos) < 1024 or len(datos) > XLSX_MAX_BYTES:
        raise PlantillaInvalida("Plantilla XLSX ausente o tamaño no permitido (máximo 25 MB).")
    try:
        z = ZipFile(BytesIO(datos))
    except BadZipFile as exc:
        raise PlantillaInvalida("El archivo no es un XLSX válido.") from exc
    nombres = {x.filename for x in z.infolist()}
    faltantes = {"xl/workbook.xml", "xl/worksheets/sheet1.xml", "xl/worksheets/sheet13.xml"} - nombres
    if faltantes:
        z.close()
        raise PlantillaInvalida("Falta estructura esencial del archivo ALCANTO.")
    if sum(x.file_size for x in z.infolist()) > XML_MAX_UNCOMPRESSED:
        z.close()
        raise PlantillaInvalida("El archivo expandido supera el límite de seguridad.")
    if any(x.filename.startswith(("xl/vbaProject", "_rels/.rels/../")) or "../" in x.filename for x in z.infolist()):
        z.close()
        raise PlantillaInvalida("No se aceptan macros ni rutas sospechosas.")
    # El libro tiene 17 hojas. No se aceptan plantillas ajenas.
    wb = z.read("xl/workbook.xml").decode("utf-8")
    if not all('name="' + name + '"' in wb for name in ["Datos Contrato", "MATRIZ PTS", "Contrato Imprimible", "IRL"]):
        z.close()
        raise PlantillaInvalida("El Excel no parece ser la plantilla ALCANTO esperada.")
    return z


def verificar_plantilla(datos: bytes) -> dict[str, object]:
    with _abrir(datos) as z:
        w = ET.fromstring(z.read("xl/workbook.xml"))
        hojas = [n.attrib["name"] for n in w.iter(NS + "sheet")]
        if len(hojas) != 17 or not all(d.hoja in hojas for d in DOCUMENTOS):
            raise PlantillaInvalida("Esta versión no corresponde a las 17 hojas previstas de ALCANTO.")
        orig = z.read("xl/worksheets/sheet1.xml").decode()
        formulas = {ref: bool(re.search(r"<f(?:\s|>)", match.group(2)))
                    for ref in CAMPOS for match in [_celda(ref).search(orig)] if match}
        if len(formulas) != len(CAMPOS):
            raise PlantillaInvalida("Faltan campos de entrada en Datos Contrato.")
        if any(formulas.values()):
            raise PlantillaInvalida("Algún campo de entrada tiene una fórmula: no se editará.")
        return {"hojas": hojas, "formulas_totales": sum(z.read(p).count(b"<f ") + z.read(p).count(b"<f>")
               for p in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", p)),
                "sha256": sha256(datos).hexdigest(), "tamano": len(datos)}


def _shared_strings(z: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    raiz = ET.fromstring(z.read("xl/sharedStrings.xml"))
    return ["".join(t.text or "" for t in si.iter(NS + "t")) for si in raiz.findall(NS + "si")]


def _leer_celdas(z: ZipFile, hoja: str, refs: list[str], strings: list[str]) -> dict[str, str]:
    s = z.read(hoja).decode("utf-8")
    d: dict[str, str] = {}
    for ref in refs:
        m = _celda(ref).search(s)
        if not m:
            d[ref] = ""
            continue
        cell = ET.fromstring(m.group(0))
        v = cell.find("v")
        if cell.get("t") == "s" and v is not None and v.text is not None:
            d[ref] = strings[int(v.text)]
        elif cell.get("t") == "inlineStr":
            d[ref] = "".join(t.text or "" for t in cell.iter("t"))
        else:
            d[ref] = v.text if v is not None and v.text else ""
    return d


def catalogos(datos: bytes) -> dict[str, object]:
    with _abrir(datos) as z:
        strings = _shared_strings(z)
        input_data = _leer_celdas(z, "xl/worksheets/sheet1.xml", ["T16","T17","T18"], strings)
        especialidades = _leer_celdas(z, "xl/worksheets/sheet13.xml",
                                     [a + str(i) for i in range(2, 28) for a in ["A", "B"]], strings)
        matriz = _leer_celdas(z, "xl/worksheets/sheet13.xml",
                             [chr(i) + str(f) for f in range(2, 28) for i in range(68, 85)], strings)
        cargos: list[str] = []
        pts: set[str] = set()
        for fila in range(2, 28):
            cargo = especialidades.get(f"A{fila}", "").strip()
            if cargo and cargo not in cargos:
                cargos.append(cargo)
            if cargo and all(matriz.get(chr(col)+str(fila), "").strip() for col in range(68, 85)):
                pts.add(cargo.casefold())
        obras = list(dict.fromkeys(val for val in input_data.values() if val))
        return {"cargos": cargos, "obras": obras, "pts_completos": pts,
                "registros_pts": sum(bool(especialidades.get(f"A{fila}", "")) for fila in range(2,28))}


def _serial_fecha(s: str) -> int:
    try:
        d = date.fromisoformat(s)
    except ValueError as exc:
        raise ValueError("Fecha de nacimiento debe tener formato AAAA-MM-DD.") from exc
    if not (date(1901,1,1) <= d <= date.today()):
        raise ValueError("Fecha de nacimiento fuera del intervalo permitido.")
    return (d - date(1899,12,30)).days


def _contenido(ref: str, value: str) -> tuple[str, str]:
    if value == "":
        return "inlineStr", '<is><t xml:space="preserve"></t></is>'
    if ref == "C32":
        if not re.fullmatch(r"\d{1,12}", value):
            raise ValueError("El sueldo debe escribirse solo con números enteros.")
        return "n", f"<v>{int(value)}</v>"
    if ref == "C20":
        return "n", f"<v>{_serial_fecha(value)}</v>"
    if len(value) > 800 or any(ord(c) < 32 and c not in '\t\n' for c in value):
        raise ValueError("Texto no permitido o demasiado largo en el campo " + ref)
    return "inlineStr", '<is><t xml:space="preserve">' + escape(value, {'"': '&quot;', "'": '&apos;'}) + '</t></is>'


def generar_copia(datos_originales: bytes, entradas: dict[str, str], *, limpiar_previos: bool = True) -> bytes:
    """No modifica originales. Ignora caches viejos; la nube debe recalcular fórmulas.

    Si limpiar_previos=True, borra todos los campos de entrada ANTES de aplicar
    los nuevos datos, para evitar imprimir información de un trabajador anterior.
    """
    if not isinstance(entradas, dict) or any(c not in CAMPOS and c != "ANEXO_M4" for c in entradas):
        raise ValueError("Intento de editar una celda no autorizada.")
    if any(not isinstance(v,str) for v in entradas.values()):
        raise ValueError("Todos los datos deben ser texto para validarse correctamente.")
    seleccion = {ref: entradas.get(ref, "").strip() for ref in CAMPOS} if limpiar_previos else {k:v for k,v in entradas.items() if k in CAMPOS}
    fecha_prorroga = entradas.get("ANEXO_M4", "").strip()
    # Validar todos los valores ANTES de crear la copia.
    valores = {ref: _contenido(ref, v) for ref,v in seleccion.items()}
    with _abrir(datos_originales) as z:
        origen = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
        copia = origen
        for ref,(tipo,cuerpo) in valores.items():
            regex = _celda(ref)
            m = regex.search(copia)
            if not m:
                raise PlantillaInvalida("No se encontró la celda editable " + ref)
            if re.search(r"<f(?:\s|>)",m.group(2)):
                raise PlantillaInvalida("Se evitó sobrescribir una fórmula en " + ref)
            tag = re.sub(r'\s+t="[^"]*"', "", m.group(1))
            tag = tag[:-1] + (' t="inlineStr">' if tipo == "inlineStr" else '>')
            copia = copia[:m.start()] + tag + cuerpo + "</c>" + copia[m.end():]
        # M4 de anexo es una fecha fija (no una fórmula), solo se cambia en la copia.
        extension = None
        if fecha_prorroga:
            try:
                fecha_obj = date.fromisoformat(fecha_prorroga)
            except ValueError as exc:
                raise ValueError("La nueva fecha de prórroga debe usar AAAA-MM-DD.") from exc
            if not date(1901, 1, 1) <= fecha_obj <= date(2100, 12, 31):
                raise ValueError("La fecha de prórroga está fuera de intervalo permitido.")
            serial = (fecha_obj - date(1899, 12, 30)).days
            extension = z.read("xl/worksheets/sheet4.xml").decode("utf-8")
            ext_match = _celda("M4").search(extension)
            if not ext_match:
                raise PlantillaInvalida("No se encontró la fecha M4 del anexo de prórroga.")
            if re.search(r"<f(?:\s|>)", ext_match.group(2)):
                raise PlantillaInvalida("La fecha M4 tiene fórmula: no se puede editar.")
            tag = re.sub(r'\s+t="[^"]*"', "", ext_match.group(1))
            extension = extension[:ext_match.start()] + tag + f"<v>{serial}</v></c>" + extension[ext_match.end():]
        # Actualizar solamente indicadores de recálculo, sin modificar fórmulas.
        libro = z.read("xl/workbook.xml").decode("utf-8")
        flags = ' fullCalcOnLoad="1" forceFullCalc="1" calcMode="auto"'
        if re.search(r"<calcPr\b",libro):
            libro = re.sub(r"<calcPr\b[^>]*/>", '<calcPr'+flags+'/>',libro,count=1)
        else:
            libro = libro.replace("</workbook>", '<calcPr'+flags+'/></workbook>')
        out = BytesIO()
        with ZipFile(out, 'w') as output:
            for member in z.infolist():
                if member.filename == "xl/worksheets/sheet1.xml":
                    content = copia.encode("utf-8")
                elif member.filename == "xl/workbook.xml":
                    content = libro.encode("utf-8")
                elif member.filename == "xl/worksheets/sheet4.xml" and extension is not None:
                    content = extension.encode("utf-8")
                else:
                    content = z.read(member.filename)
                # Reutilizar metadatos de ZIP y el nivel de compresión de entrada.
                output.writestr(member,content)
        return out.getvalue()
