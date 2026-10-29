"""PROYECTO ALCANTO — plataforma 100% online para Streamlit Community Cloud.

No necesita Microsoft Excel ni archivos en el computador durante el uso diario.
Las 17 hojas y fórmulas están en una plantilla XLSX privada. Los cambios se
aplican SOLO a una copia en memoria. Para un PDF se requiere Aspose.Cells Cloud.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED

import streamlit as st

from alcanto_cloud.catalog import (
    CAMPOS_EMPRESA, CAMPOS_TRABAJADOR, DOCUMENTOS, estado_documental,
)
from alcanto_cloud.pdf_service import AsposeCellsCloud, ErrorDeConversion, verificar_identidad_pdf
from alcanto_cloud.storage import AlmacenPrivado
from alcanto_cloud.workbook import (
    PlantillaInvalida, catalogos, generar_copia, verificar_plantilla, _abrir, _shared_strings, _leer_celdas,
)

st.set_page_config(page_title="PROYECTO ALCANTO | Gestión documental", page_icon="📄", layout="wide")

# No mostrar valores reales en avisos ni en registros de aplicación.
def secret(nombre: str) -> str:
    try:
        return str(st.secrets.get(nombre, ""))
    except (FileNotFoundError, KeyError):
        return ""


def almacen() -> AlmacenPrivado | None:
    try:
        cfg = st.secrets.get("storage", None)
    except (FileNotFoundError, KeyError):
        cfg = None
    if not cfg:
        return None
    return AlmacenPrivado(dict(cfg))


def guardar(tipo: str, contenido: dict) -> str:
    store = almacen()
    if store:
        return store.guardar(tipo, contenido)
    registro = {**contenido, "id": str(uuid4()),
                "creado": datetime.now(timezone.utc).isoformat()}
    st.session_state.setdefault("demo_" + tipo, []).insert(0, registro)
    return registro["id"]


def listar(tipo: str) -> list[dict]:
    store = almacen()
    if store:
        return store.listar(tipo)
    return st.session_state.setdefault("demo_" + tipo, [])


def inyectar_css() -> None:
    st.markdown("""<style>
    .stApp{background:#f5f8fb}
    [data-testid="stSidebar"]{background:#132b43;color:white}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"]{color:white}
    .alcanto-top{background:#152d46;border-radius:15px;color:white;padding:24px 30px;margin:6px 0 20px}
    .alcanto-top strong{font-size:26px;letter-spacing:1px}
    .alcanto-top p{color:#c5d9e4;margin-bottom:0}
    .alcanto-box{padding:15px;border-radius:10px;background:#e7f3f1;margin:8px 0 12px;color:#17665f}
    .stButton button[kind="primary"]{background:#087c75;border-color:#087c75}
    .stMetric{border:1px solid #dae2ea;border-radius:11px;background:white;padding:12px}
    </style>""", unsafe_allow_html=True)


def ingreso() -> None:
    st.markdown("<div class='alcanto-top'><strong>ALCANTO</strong><p>Contratistas y prevención · Gestión documental 100% online</p></div>", unsafe_allow_html=True)
    configurada = secret("ALCANTO_APP_PASSWORD")
    if not configurada or configurada.startswith("CAMBIAR_") or len(configurada) < 16:
        st.error("La aplicación aún no tiene contraseña segura configurada en los secretos de Streamlit.")
        st.code("ALCANTO_APP_PASSWORD = 'contraseña-generada-de-20-caracteres-o-más'",language="toml")
        st.stop()
    if not st.session_state.get("autenticado", False):
        st.subheader("Acceso autorizado")
        with st.form("acceso"):
            pass_value = st.text_input("Contraseña de acceso", type="password")
            enviar = st.form_submit_button("Ingresar", type="primary")
        if enviar:
            from hmac import compare_digest
            if compare_digest(pass_value.encode("utf-8"), configurada.encode("utf-8")):
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
        st.info("Esta aplicación maneja RUT y datos personales. Restringe además el acceso a sus usuarios desde Streamlit Community Cloud.")
        st.stop()


def plantilla_actual() -> bytes | None:
    if st.session_state.get("plantilla_privada"):
        return st.session_state.plantilla_privada
    store = almacen()
    if store:
        try:
            data = store.obtener_plantilla()
            if data:
                verificar_plantilla(data)
                st.session_state.plantilla_privada = data
                return data
        except Exception:
            st.warning("No se pudo recuperar la plantilla privada de la nube. Revisa la conexión S3.")
    return None


def campo(ref: str, titulo: str, opciones: list[str] | None = None):
    if opciones:
        opciones = [""] + opciones
        return st.selectbox(f"{titulo} · {ref}",options=opciones, key="campo_"+ref)
    if ref == "C20":
        return st.text_input(f"{titulo} · {ref}",placeholder="1995-08-21",key="campo_"+ref)
    return st.text_input(f"{titulo} · {ref}", key="campo_"+ref)


def formulario_empresa() -> list[dict]:
    st.markdown("### 1. Empresas y representantes")
    st.caption("La empresa queda registrada para reutilizarla con varios trabajadores. No necesitas repetir el RUT en cada documento.")
    with st.expander("Registrar una empresa nueva",expanded=not bool(listar("empresas"))):
        with st.form("empresa_nueva",clear_on_submit=True):
            cols = st.columns(2)
            valores = {}
            for i, (ref,titulo) in enumerate(CAMPOS_EMPRESA.items()):
                with cols[i%2]:
                    valores[ref] = st.text_input(f"{titulo} · {ref}",max_chars=800,key="emp_"+ref)
            enviado = st.form_submit_button("Guardar empresa",type="primary")
        if enviado:
            if not valores["C5"].strip() or not valores["C6"].strip():
                st.error("Faltan nombre y RUT del empleador.")
            else:
                try:
                    guardar("empresas",{"valores":{k:v.strip() for k,v in valores.items()}})
                    st.success("Empresa registrada.")
                    st.rerun()
                except Exception:
                    st.error("No se pudo guardar la empresa en el almacenamiento privado.")
    return listar("empresas")


def formulario_trabajador(empresas: list[dict], cat: dict) -> tuple[dict | None, dict | None]:
    st.markdown("### 2. Trabajadores")
    if not empresas:
        st.info("Primero registra una empresa para comenzar.")
        return None,None
    nombres = {emp["id"]:emp.get("valores",{}).get("C5", "Empresa sin nombre") for emp in empresas}
    id_empresa=st.selectbox("Empresa de este trabajador",options=list(nombres),format_func=lambda x:nombres[x])
    elegida=next((e for e in empresas if e["id"]==id_empresa),None)
    trabajadores=[t for t in listar("trabajadores") if t.get("empresa_id")==id_empresa]
    opciones=[""]+[t["id"] for t in trabajadores]
    sel=st.selectbox("Trabajador existente / crear nuevo",options=opciones,
                     format_func=lambda x: "➕ Nuevo trabajador" if not x else next((t["valores"].get("C17","") for t in trabajadores if t["id"]==x),"Trabajador"))
    actual=next((t for t in trabajadores if t["id"]==sel), None)
    if actual:
        st.success("Ficha seleccionada. Ya puedes generar los documentos asociados a este trabajador.")
        st.caption("Para cambiar datos, crea una nueva ficha, conservando el historial de la anterior.")
        return elegida,actual
    with st.form("nuevo_trabajador",clear_on_submit=True):
        valores={}
        cols=st.columns(2)
        for i,(ref,titulo) in enumerate(CAMPOS_TRABAJADOR.items()):
            with cols[i%2]:
                if ref=="C29":
                    valores[ref]=st.selectbox(f"{titulo} · {ref}",options=[""]+cat["cargos"],key="nuevo_"+ref)
                elif ref=="D30":
                    valores[ref]=st.selectbox(f"{titulo} · {ref}",options=[""]+cat["obras"],key="nuevo_"+ref)
                else:
                    valores[ref]=st.text_input(f"{titulo} · {ref}",max_chars=800,key="nuevo_"+ref,
                                             placeholder="AAAA-MM-DD" if ref=="C20" else None)
        creado=st.form_submit_button("Registrar trabajador",type="primary")
    if creado:
        if not all(valores.get(x, "").strip() for x in ("C17","C18","C29","D30")):
            st.error("Completa nombre, RUT, cargo y obra del trabajador.")
        else:
            try:
                guardar("trabajadores",{"empresa_id":id_empresa,"valores":{k:v.strip() for k,v in valores.items()}})
                st.success("Trabajador registrado.")
                st.rerun()
            except Exception:
                st.error("No se pudo registrar al trabajador. Revisa la conexión de almacenamiento.")
    return elegida,None


def descargar_documentos(template: bytes, empresa:dict, trabajador:dict, cat:dict) -> None:
    st.markdown("### 3. Documentos disponibles y PDF")
    datos={**empresa.get("valores",{}),**trabajador.get("valores",{})}
    estados=estado_documental(datos, cat["pts_completos"])
    hechos=sum(1 for e in estados if e["estado"]=="Datos completos / revisar")
    c1,c2,c3=st.columns(3)
    c1.metric("Documentos con datos mínimos",hechos)
    c2.metric("Por completar",len(estados)-hechos)
    c3.metric("Total de documentos",len(estados))
    for item in estados:
        nombre=item["documento"]
        estado=item["estado"]
        texto=", ".join(item["faltan"])
        with st.expander(("✅ " if estado.startswith("Datos completos") else "⚠️ ")+nombre+" — "+estado):
            if texto: st.write("Campos necesarios: "+texto)
            else: st.write("Datos de identificación completos; sigue pendiente revisar legalidad, firmas y contenido.")
            st.caption(item["observacion"])
    disponibles=[e for e in estados if e["estado"]=="Datos completos / revisar"]
    nombres={e["hoja"]: e["documento"] for e in disponibles}
    seleccion=st.multiselect("Selecciona los documentos que deseas convertir a PDF",
        list(nombres),format_func=lambda k:nombres[k])
    avisar=st.checkbox("Confirmo que los datos son correctos, que conozco que el archivo se enviará por HTTPS a Aspose.Cells Cloud y revisaré los PDF antes de su uso.")
    cloud_id=secret("ASPOSE_CLIENT_ID")
    cloud_key=secret("ASPOSE_CLIENT_SECRET")
    if not cloud_id or not cloud_key:
        st.warning("Falta conectar Aspose.Cells Cloud en los secretos de Streamlit. Los PDFs online no se pueden generar todavía.")
    if st.button("Generar PDF online para imprimir", type="primary",disabled=not (seleccion and avisar and cloud_id and cloud_key)):
        try:
            with st.spinner("Preparando copia temporal del Excel sin modificar ninguna fórmula…"):
                copia=generar_copia(template,datos)
                motor=AsposeCellsCloud(cloud_id,cloud_key)
                with _abrir(template) as z:
                    nombre_anterior = _leer_celdas(z, "xl/worksheets/sheet1.xml", ["C17"], _shared_strings(z))["C17"]
            zipdata=BytesIO()
            total_paginas=0
            with ZipFile(zipdata, "w", ZIP_DEFLATED) as paquete:
                progreso=st.progress(0.0)
                for i,hoja in enumerate(seleccion,1):
                    resultado=motor.convertir_hoja(copia,hoja)
                    verificar_identidad_pdf(resultado,hoja,datos.get("C17",""),
                                             datos.get("C18",""),nombre_anterior)
                    safe=hoja.replace(" ","_").replace(".","")
                    paquete.writestr(f"{i:02d}_{safe}.pdf",resultado.contenido)
                    total_paginas+=resultado.paginas
                    progreso.progress(i/len(seleccion))
                paquete.writestr("IMPORTANTE.txt",
                    "ALCANTO: PDFs pendientes de revisión de datos, firmas y cumplimiento legal.\n"
                    "El documento original XLSX y sus fórmulas no fueron modificados.\n")
            st.session_state["pdf_generados"] = zipdata.getvalue()
            st.session_state["pdf_firma"] = sha256((trabajador["id"]+"|"+"|".join(seleccion)).encode()).hexdigest()
            st.success(f"Conversión finalizada: {len(seleccion)} documentos, {total_paginas} páginas. Confirma el resultado antes de imprimir.")
        except (ErrorDeConversion, PlantillaInvalida, ValueError) as error:
            st.session_state.pop("pdf_generados",None)
            st.error(str(error))
        except Exception:
            st.session_state.pop("pdf_generados",None)
            st.error("La conversión no pudo completarse. Revisa las credenciales, cuotas y funcionamiento del proveedor.")
    firma=sha256((trabajador["id"]+"|"+"|".join(seleccion)).encode()).hexdigest()
    if st.session_state.get("pdf_firma")==firma and st.session_state.get("pdf_generados"):
        st.download_button("⬇ Descargar documentos PDF para imprimir",data=st.session_state["pdf_generados"],
            file_name="ALCANTO_documentos_imprimibles.zip",mime="application/zip",type="primary")


def main() -> None:
    inyectar_css()
    ingreso()
    st.markdown("<div class='alcanto-top'><strong>PROYECTO ALCANTO</strong><p>Empresas, trabajadores, subcontratos y prevención | Automático y online</p></div>",unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("## 📄 ALCANTO")
        st.caption("Gestiona el sistema sin instalar Excel")
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.rerun()
        st.divider()
        st.markdown("**Almacenamiento**")
        st.write("🔐 Privado en la nube" if almacen() else "⚠️ Temporal en esta sesión")
        st.markdown("**Motor de impresión**")
        st.write("✅ Credenciales configuradas" if secret("ASPOSE_CLIENT_ID") and secret("ASPOSE_CLIENT_SECRET") else "⚠️ Aspose no configurado")
        st.caption("No guardar archivos con RUT en GitHub público.")
    template=plantilla_actual()
    if not template:
        st.subheader("Configuración inicial de tu plantilla")
        st.info("Carga UNA VEZ el XLSX del proyecto. En la nube se guarda como plantilla privada si conectas un bucket S3. El usuario no necesita Microsoft Excel para operar.")
        nuevo=st.file_uploader("Archivo ALCANTO original (.xlsx, máximo 25 MB)",type=["xlsx"])
        confirmado=st.checkbox("Confirmo que estoy autorizado a tratar los datos personales del libro y, cuando genere PDFs, a enviarlos al procesador cloud configurado.")
        if nuevo and confirmado and st.button("Validar y cargar plantilla",type="primary"):
            try:
                data=nuevo.getvalue()
                resumen=verificar_plantilla(data)
                if almacen():
                    almacen().guardar_plantilla(data)
                st.session_state.plantilla_privada=data
                st.success(f"Plantilla validada: {len(resumen['hojas'])} hojas. No se cambió el archivo.")
                st.rerun()
            except PlantillaInvalida as error:
                st.error(str(error))
            except Exception:
                st.error("No se pudo guardar la plantilla. Revisa los permisos del almacenamiento privado.")
        st.stop()
    try:
        catalogo = catalogos(template)
    except Exception:
        st.error("La matriz o los catálogos del Excel no se pueden leer. No se modificará el archivo.")
        st.stop()
    if not almacen():
        st.warning("Modo sesión: los registros desaparecerán cuando el servidor se reinicie. Configura un bucket S3 privado en Streamlit Secrets para conservarlos online.")
    st.markdown("<div class='alcanto-box'>La fórmula y la presentación del Excel original se respetan. Los documentos se obtienen desde una copia temporal sin sobrescribir la plantilla.</div>",unsafe_allow_html=True)
    tab1,tab2 = st.tabs(["📋 Registrar empresas y trabajadores", "🖨️ Documentación e impresión"])
    with tab1:
        empresas=formulario_empresa()
        empresa,trabajador=formulario_trabajador(empresas,catalogo)
    with tab2:
        empresas=listar("empresas")
        todos=listar("trabajadores")
        if not empresas or not todos:
            st.info("Guarda una empresa y un trabajador en la primera pestaña.")
        else:
            mapa={t["id"]:t for t in todos}
            elegido=st.selectbox("Trabajador",options=list(mapa),format_func=lambda k:mapa[k].get("valores",{}).get("C17","Trabajador"))
            worker=mapa[elegido]
            company=next((e for e in empresas if e["id"]==worker.get("empresa_id")),None)
            if company:
                st.caption("Empresa: "+company.get("valores",{}).get("C5",""))
                descargar_documentos(template,company,worker,catalogo)
            else:
                st.error("No se encontró la empresa vinculada a este trabajador.")
    st.caption("Alcanto online · Contratos, IRL, PTS y registros. Es obligatorio revisar los PDF antes de imprimir, firmar o entregar.")


if __name__ == "__main__":
    main()
