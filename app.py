"""ALCANTO: generador LOCAL de PDFs, calculados e impresos con Microsoft Excel.
NO modifica el original. Requiere Windows + Excel de escritorio y sesión interactiva.
Lanzar: python -m streamlit run app.py --server.address 127.0.0.1
"""
from __future__ import annotations

import hashlib
import io
import platform
import re
import tempfile
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import streamlit as st
from scripts.estado_documental import libro as rutas_libro, leer_celdas, REQUISITOS, tiene_dato, pts_completo

DOCUMENTOS = (
    "Contrato Imprimible",
    "Anexo Traslado",
    "Anexo extension contrato",
    "INDUCCION PREVENCION",
    "IRL",
    "PTS.",
    "ENTREGA PTS",
    "Registros Entrega EPP",
    "REGLAMENTO INTERNO",
    "DECLARACION JURADA",
)

# Verificadas como casillas sin fórmula en la planilla original.
EDITABLES = {
    "C5": "Empresa", "C6": "RUT empresa", "C7": "Representante legal",
    "C8": "RUT representante", "C9": "Teléfono empresa",
    "C10": "Domicilio empresa", "C11": "Comuna empresa", "C12": "Ciudad empresa",
    "C13": "Correo empresa", "C14": "Rubro",
    "C17": "Nombre trabajador", "C18": "RUT trabajador", "C19": "Nacionalidad",
    "C21": "Estado civil", "C22": "Domicilio trabajador", "C23": "Comuna trabajador",
    "C24": "Ciudad trabajador", "C25": "Correo trabajador", "C26": "Teléfono trabajador",
    "C29": "Cargo / especialidad", "D30": "Obra / faena",
    "C31": "Jornada", "C32": "Sueldo base en pesos (solo números)",
    "C34": "Frecuencia de pago", "C35": "Datos de pago",
    "C38": "AFP", "C39": "Salud", "C43": "Destinos para traslado",
    "C44": "Locomoción",
}


def inspeccionar(contenido: bytes):
    with ZipFile(io.BytesIO(contenido)) as z:
        rutas, cadenas = rutas_libro(z)
        for nombre in ("Datos Contrato", "MATRIZ PTS", "Anexo extension contrato", *DOCUMENTOS):
            if nombre not in rutas:
                raise ValueError("Falta la hoja " + nombre)
        datos = leer_celdas(z, rutas["Datos Contrato"], cadenas)
        matriz = leer_celdas(z, rutas["MATRIZ PTS"], cadenas)
        anexo = leer_celdas(z, rutas["Anexo extension contrato"], cadenas)
        return datos, matriz, anexo


def estados(datos: dict, matriz: dict, anexo: dict, cambios: dict):
    actual = dict(datos)
    actual.update({celda: (valor, False) for celda, valor in cambios.items()})
    cargo = str(actual.get("C29", ("", False))[0] or "")
    pts_valido, estado_pts = pts_completo(matriz, cargo) if cargo else (False, "Cargo sin informar")
    resultado = []
    for hoja in DOCUMENTOS:
        faltan = [celda for celda in REQUISITOS[hoja] if not tiene_dato(actual, celda)]
        if hoja == "Anexo extension contrato" and not tiene_dato(anexo, "M4"):
            faltan.append("Anexo extension contrato!M4")
        if faltan:
            estado, detalle = "FALTAN DATOS", ", ".join(faltan)
        elif hoja == "PTS." and not pts_valido:
            estado, detalle = "PTS PENDIENTE", estado_pts
        else:
            estado, detalle = "GENERABLE / REVISAR", "Revisar contenido, fechas y firmas"
        resultado.append({"Documento": hoja, "Estado": estado, "Detalle": detalle})
    return resultado


def pdf_en_excel(contenido: bytes, seleccion: list[str], cambios: dict) -> bytes:
    """La copia es EFÍMERA. Nunca se escribe la plantilla ni se guardan cambios."""
    if platform.system() != "Windows":
        raise RuntimeError("Se requiere Windows con Microsoft Excel instalado.")
    if any(k not in EDITABLES for k in cambios) or any(h not in DOCUMENTOS for h in seleccion):
        raise ValueError("Se detectó una celda o documento no autorizado.")
    if not seleccion:
        raise ValueError("Selecciona al menos un documento.")
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    excel = None
    wb = None
    try:
        with tempfile.TemporaryDirectory(prefix="alcanto_") as carpeta:
            fuente = Path(carpeta) / "copia_temporal.xlsx"
            fuente.write_bytes(contenido)
            excel = win32com.client.DispatchEx("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False
            excel.ScreenUpdating = False
            excel.AutomationSecurity = 3  # Deshabilitar macros en automatización
            excel.AskToUpdateLinks = False
            wb = excel.Workbooks.Open(str(fuente), UpdateLinks=0, ReadOnly=False, AddToMru=False)
            if wb.ReadOnly:
                raise RuntimeError("No fue posible abrir la copia temporal para los cambios.")
            entrada = wb.Worksheets("Datos Contrato")
            for celda, nuevo in cambios.items():
                rango = entrada.Range(celda)
                if rango.HasFormula is None or bool(rango.HasFormula):
                    raise ValueError("La celda " + celda + " tiene una fórmula y NO será modificada.")
                rango.Value2 = nuevo
            excel.CalculateFullRebuild()
            paquete = io.BytesIO()
            with ZipFile(paquete, "w", ZIP_DEFLATED) as zipf:
                for indice, nombre in enumerate(seleccion, 1):
                    nombre_archivo = re.sub(r"[^A-Za-z0-9._ -]", "_", nombre)
                    destino = Path(carpeta) / f"{indice:02d}_{nombre_archivo}.pdf"
                    wb.Worksheets(nombre).ExportAsFixedFormat(
                        Type=0, Filename=str(destino), Quality=0,
                        IncludeDocProperties=False, IgnorePrintAreas=False,
                        OpenAfterPublish=False,
                    )
                    if not destino.is_file() or destino.stat().st_size < 100:
                        raise RuntimeError("Excel no exportó " + nombre)
                    zipf.write(destino, destino.name)
                zipf.writestr("LEEME.txt", "Documentos para revisión e impresión. Confirmar datos, contenido y firmas.\n")
            wb.Close(SaveChanges=False)
            wb = None
            return paquete.getvalue()
    finally:
        if wb is not None:
            try:
                wb.Close(SaveChanges=False)
            except Exception:
                pass
        if excel is not None:
            try:
                excel.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()


st.set_page_config(page_title="ALCANTO | PDF imprimibles", page_icon="📄", layout="wide")
st.title("PROYECTO ALCANTO")
st.caption("Impresión de contratos y prevención usando el motor y formatos del Excel original")
st.info("El archivo original no se modifica. Se trabaja con una copia temporal que se elimina al terminar.")
if platform.system() != "Windows":
    st.warning("La generación de PDF requiere ejecutar esta aplicación LOCALMENTE en Windows con Excel de escritorio.")
entrada = st.file_uploader("Selecciona tu Excel ALCANTO (.xlsx)", type=["xlsx"])
if entrada is None:
    st.markdown("Carga tu planilla para consultar documentos disponibles y preparar PDF de impresión.")
    st.stop()
contenido = entrada.getvalue()
if len(contenido) > 40 * 1024 * 1024:
    st.error("El archivo supera los 40 MB permitidos.")
    st.stop()
try:
    datos, matriz, anexo = inspeccionar(contenido)
except Exception as exc:
    st.error("No se pudo leer el archivo ALCANTO: " + str(exc))
    st.stop()

st.subheader("1. Datos del trabajador y empresa")
modo = st.radio("Elige cómo trabajar", ["Usar datos que ya están completos en el Excel", "Completar una copia temporal"], index=0)
cambios = {}
if modo == "Completar una copia temporal":
    st.caption("Dejar un campo en blanco mantiene el dato que ya está en el Excel; no se mostrarán los datos personales existentes.")
    grupos = {
        "Empresa y representante": list(EDITABLES.items())[:10],
        "Trabajador": list(EDITABLES.items())[10:19],
        "Contrato, obra y remuneración": list(EDITABLES.items())[19:],
    }
    for grupo, campos in grupos.items():
        with st.expander(grupo, expanded=(grupo == "Empresa y representante")):
            col1, col2 = st.columns(2)
            for i, (ref, etiqueta) in enumerate(campos):
                with (col1 if i % 2 == 0 else col2):
                    valor = st.text_input(etiqueta + " (" + ref + ")", key="campo_" + ref)
                    if valor.strip():
                        if ref == "C32":
                            if not valor.strip().isdigit():
                                st.error("Sueldo C32: usar números sin puntos.")
                                st.stop()
                            cambios[ref] = int(valor.strip())
                        else:
                            cambios[ref] = valor.strip()
    st.warning("Las celdas de fórmula C30, C33, C36, C37 y C40 NO se editan. La fecha HOY() cambia con el día.")

st.subheader("2. Documentos disponibles con los datos actuales")
filas = estados(datos, matriz, anexo, cambios)
st.dataframe(filas, use_container_width=True, hide_index=True)
st.caption("GENERABLE / REVISAR no significa que el documento esté firmado o legalmente validado.")
validos = [e["Documento"] for e in filas if e["Estado"] == "GENERABLE / REVISAR"]

st.subheader("3. Generar PDF para imprimir")
documentos = st.multiselect("Selecciona documentos", DOCUMENTOS, default=validos)
bloqueados = [h for h in documentos if h not in validos]
if bloqueados:
    st.error("Documentos con datos o contenido incompleto: " + ", ".join(bloqueados))
revision = st.checkbox("Revisaré información, fechas, prevención y firmas antes de imprimir.")
clave = hashlib.sha256((hashlib.sha256(contenido).hexdigest() + repr(sorted(cambios.items())) + repr(documentos)).encode()).hexdigest()
if st.session_state.get("firma_zip") != clave:
    st.session_state.pop("zip_impresion", None)
if st.button("Crear PDF imprimibles", type="primary", disabled=not (revision and documentos and not bloqueados)):
    try:
        with st.spinner("Microsoft Excel está preparando los PDF…"):
            archivo_zip = pdf_en_excel(contenido, documentos, cambios)
        st.session_state["zip_impresion"] = archivo_zip
        st.session_state["firma_zip"] = clave
        st.success("PDF generados. El original se mantiene sin cambios.")
    except Exception as exc:
        st.error("No se pudo imprimir: " + str(exc))
if st.session_state.get("zip_impresion"):
    st.download_button("Descargar ZIP de PDF para imprimir", data=st.session_state["zip_impresion"],
                       file_name="ALCANTO_documentos_para_imprimir.zip", mime="application/zip")
st.divider()
st.caption("USO LOCAL exclusivamente. No publicar en una plataforma web: los archivos contienen datos personales.")
