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
    catalogo_predefinido, RENTA_BASE_REFERENCIA, JORNADA_REFERENCIA,
    PAGO_REFERENCIA,
)
from alcanto_cloud.documentos import estado_por_contexto, preparar_datos
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


def almacen() -> None:
    """Los datos personales son exclusivos de la sesión: NO compartir S3."""
    return None


def almacen_plantilla() -> AlmacenPrivado | None:
    """Acceso de servidor y únicamente lectura al modelo XLSX maestro."""
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



def plantilla_actual() -> bytes | None:
    """El Excel es un recurso interno del servidor, no una carga del usuario.

    Se busca exclusivamente en S3 privado preconfigurado o en una ruta
    preinstalada para despliegues controlados. Ningún usuario puede subir
    ni descargar la plantilla maestra desde esta aplicación.
    """
    if st.session_state.get("plantilla_privada"):
        return st.session_state.plantilla_privada
    modelo = None
    privado = almacen_plantilla()
    if privado is not None:
        try:
            modelo = privado.obtener_plantilla()
        except Exception:
            st.error("No se pudo abrir el Excel interno desde el almacenamiento privado.")
            return None
    else:
        ruta = Path(__file__).resolve().parent / "plantillas" / "ALCANTO_MODELO.xlsx"
        if ruta.is_file():
            try:
                modelo = ruta.read_bytes()
            except OSError:
                st.error("No se puede leer el modelo interno.")
                return None
    if modelo is None:
        return None
    try:
        verificar_plantilla(modelo)
        st.session_state.plantilla_privada = modelo
        return modelo
    except PlantillaInvalida:
        st.error("La plantilla interna no coincide con las 17 hojas de ALCANTO.")
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
    st.caption("La empresa queda registrada durante esta sesión para reutilizarla con varios trabajadores. No necesitas repetir el RUT en cada documento.")
    with st.expander("Registrar una empresa nueva",expanded=not bool(listar("empresas"))):
        with st.form("empresa_nueva",clear_on_submit=True):
            cols = st.columns(2)
            valores = {}
            for i, (ref,titulo) in enumerate(CAMPOS_EMPRESA.items()):
                with cols[i%2]:
                    valores[ref] = st.text_input(f"{titulo} · {ref}",max_chars=800,key="emp_"+ref)
            st.markdown("#### Opciones de documentación de empresa")
            valores["D30"] = st.selectbox(
                "Obra / faena principal · D30",
                options=[""] + catalogo_predefinido()["obras"],
                key="emp_obra",
                help="Se conserva la selección para la fórmula de dirección C30 del Excel.",
            )
            valores["DECLARANTE_NACIONALIDAD"] = st.text_input(
                "Nacionalidad del representante firmante (solo declaración jurada)",
                max_chars=80, key="emp_nacionalidad",
                help="Es distinta de la nacionalidad del trabajador: el Excel usa C19 en la declaración jurada.",
            )
            enviado = st.form_submit_button("Guardar empresa",type="primary")
        if enviado:
            if not valores["C5"].strip() or not valores["C6"].strip():
                st.error("Faltan nombre y RUT del empleador.")
            else:
                try:
                    guardar("empresas",{"valores":{k:v.strip() for k,v in valores.items()}})
                    st.success("Empresa registrada temporalmente en esta sesión.")
                    st.rerun()
                except Exception:
                    st.error("No se pudo guardar la empresa en el almacenamiento privado.")
    return listar("empresas")


def formulario_trabajador(empresas: list[dict], cat: dict) -> tuple[dict | None, dict | None]:
    st.markdown("### 2. Trabajadores")
    st.caption("3 obras predefinidas y 25 cargos del Excel. Renta de referencia $553.553 y jornada 42, ambas editables.")
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
                if ref == "C29":
                    cargo_seleccionado = st.selectbox(
                        f"{titulo} · {ref}",
                        options=[""] + list(cat["cargos"]) + ["OTRO (ESPECIFICAR)"],
                        key="nuevo_"+ref,
                        help="Los 25 cargos son claves exactas de MATRIZ PTS. Un cargo nuevo no tendrá PTS hasta incorporarlo a la matriz.",
                    )
                    valores[ref] = (
                        st.text_input("Especifica el cargo no incluido en la matriz",
                                      key="nuevo_cargo_libre", max_chars=200).strip()
                        if cargo_seleccionado == "OTRO (ESPECIFICAR)"
                        else cargo_seleccionado
                    )
                elif ref == "D30":
                    valores[ref] = st.selectbox(
                        f"{titulo} · {ref}", options=[""] + list(cat["obras"]),
                        key="nuevo_"+ref,
                        help="Las 3 obras corresponden a la lista D30 del Excel.",
                    )
                    obra_actual = valores[ref]
                    if obra_actual and cat.get("direcciones", {}).get(obra_actual):
                        st.caption("Dirección vinculada automáticamente: " + cat["direcciones"][obra_actual])
                elif ref == "C31":
                    valores[ref] = str(st.number_input(
                        f"{titulo} · {ref}", min_value=1, max_value=60,
                        value=JORNADA_REFERENCIA, step=1, key="nuevo_"+ref,
                        help="Jornada de referencia del Excel: 42 horas; puedes cambiarla.",
                    ))
                elif ref == "C32":
                    valores[ref] = str(st.number_input(
                        f"{titulo} · {ref}", min_value=1, max_value=999_999_999,
                        value=RENTA_BASE_REFERENCIA, step=10_000, key="nuevo_"+ref,
                        help="Sueldo predefinido en el Excel: $553.553; puedes cambiarlo por trabajador.",
                    ))
                elif ref == "C34":
                    valores[ref] = st.text_input(
                        f"{titulo} · {ref}", value=PAGO_REFERENCIA, max_chars=100,
                        key="nuevo_"+ref, help="El Excel trae MENSUALMENTE; editable.",
                    )
                elif ref == "C43":
                    destinos = st.multiselect(
                        f"{titulo} · {ref}", options=list(cat["obras"]),
                        key="nuevo_"+ref,
                        help="Selecciona únicamente las obras de traslado efectivamente autorizadas.",
                    )
                    otro_destino = st.text_input(
                        "Otras faenas o condiciones autorizadas (opcional)",
                        key="nuevo_destino_libre", max_chars=500,
                        help="El Excel original permite texto libre en C43; no se pierde esa posibilidad.",
                    ).strip()
                    todos = [*destinos, *([otro_destino] if otro_destino else [])]
                    valores[ref] = "Faenas " + ", ".join(todos) if todos else ""
                else:
                    valores[ref] = st.text_input(
                        f"{titulo} · {ref}", max_chars=800,key="nuevo_"+ref,
                        placeholder="AAAA-MM-DD" if ref=="C20" else None,
                    )
        valores["ANEXO_M4"] = st.text_input(
            "Nueva fecha de término para prórroga (AAAA-MM-DD) · Anexo M4",
            key="nuevo_anexo_m4", placeholder="2026-12-31",
        )
        creado=st.form_submit_button("Registrar trabajador",type="primary")
    if creado:
        if not all(valores.get(x, "").strip() for x in ("C17","C18","C29")) or not (
            valores.get("D30", "").strip() or elegida.get("valores", {}).get("D30", "").strip()
        ):
            st.error("Completa nombre, RUT, cargo y una obra (del trabajador o de la empresa).")
        else:
            try:
                guardar("trabajadores",{"empresa_id":id_empresa,"valores":{k:v.strip() for k,v in valores.items()}})
                st.success("Trabajador registrado.")
                st.rerun()
            except Exception:
                st.error("No se pudo registrar al trabajador. Revisa la conexión de almacenamiento.")
    return elegida,None


def descargar_documentos(
    template: bytes | None, empresa: dict, trabajador: dict | None, cat: dict,
    *, cargo_pts: str = "", confirma_jurada: bool = False,
) -> None:
    """Elige documentos con empresa sola; trabajador solo cuando corresponda."""
    st.markdown("### Documentación que puedes generar")
    empresa_datos = empresa.get("valores", {})
    trabajador_datos = trabajador.get("valores", {}) if trabajador else None
    estados = estado_por_contexto(
        empresa_datos, trabajador_datos, cat["pts_completos"],
        cargo_pts=cargo_pts, confirma_jurada=confirma_jurada,
    )
    disponibles = [e for e in estados if e["generable"]]
    c1, c2, c3 = st.columns(3)
    c1.metric("Documentos con datos mínimos", len(disponibles))
    c2.metric("Pendientes / requieren revisión", len(estados) - len(disponibles))
    c3.metric("Documentos del sistema", len(estados))
    for e in estados:
        icono = "✅ " if e["generable"] else "⚠️ "
        with st.expander(icono + e["documento"] + " — " + e["estado"]):
            if e["faltan"]:
                st.write("Faltan campos: " + ", ".join(e["faltan"]))
            if e["estado"] == "Requiere trabajador":
                st.write("Este documento identifica a un trabajador. Selecciona uno para generarlo.")
            if e["estado"] == "PTS pendiente":
                st.write("El cargo todavía no tiene sus 17 campos técnicos PTS completos.")
            if e["estado"] == "Confirmar declaración":
                st.write("Confirma que la declaración de inexistencia de dependientes es verdadera.")
            st.caption(e["observacion"])
    nombres = {e["hoja"]: e["documento"] for e in disponibles}
    seleccion = st.multiselect(
        "Documentos para PDF", options=list(nombres),
        format_func=lambda h: nombres[h], key="docs_seleccionados",
    )
    avisar = st.checkbox(
        "Confirmo que revisaré los datos y que autorizo el envío de la copia temporal por HTTPS "
        "a Aspose.Cells Cloud para su conversión.",
        key="confirmacion_aspose",
    )
    cloud_id, cloud_key = secret("ASPOSE_CLIENT_ID"), secret("ASPOSE_CLIENT_SECRET")
    if not template:
        st.warning("Falta instalar el modelo privado del Excel en el servidor. Los formularios funcionan, pero todavía no se pueden imprimir PDFs.")
    if not cloud_id or not cloud_key:
        st.warning("Falta configurar Aspose.Cells Cloud en Streamlit Secrets. Hasta entonces los PDF siguen deshabilitados.")
    apto = bool(template and cloud_id and cloud_key and seleccion and avisar)
    contexto = empresa["id"] + "|" + (trabajador["id"] if trabajador else "empresa") + "|" + cargo_pts
    firma = sha256((contexto + "|" + "|".join(seleccion)).encode()).hexdigest()
    if st.button("Generar PDF online para imprimir", type="primary", disabled=not apto):
        try:
            motor = AsposeCellsCloud(cloud_id, cloud_key)
            bolsa = BytesIO()
            total_paginas = 0
            with _abrir(template) as z:
                nombre_previo = _leer_celdas(
                    z, "xl/worksheets/sheet1.xml", ["C17"], _shared_strings(z)
                )["C17"]
            with ZipFile(bolsa, "w", ZIP_DEFLATED) as paquete:
                progreso = st.progress(0.0)
                for indice, hoja in enumerate(seleccion, 1):
                    datos = preparar_datos(
                        empresa_datos, trabajador_datos,
                        hoja=hoja, cargo_pts=cargo_pts,
                    )
                    # Comprobación de servidor; nunca confiar únicamente en el desplegable.
                    vigente = next(
                        e for e in estado_por_contexto(
                            empresa_datos, trabajador_datos, cat["pts_completos"],
                            cargo_pts=cargo_pts, confirma_jurada=confirma_jurada
                        ) if e["hoja"] == hoja
                    )
                    if not vigente["generable"]:
                        raise ValueError("La información de " + hoja + " está incompleta o pendiente.")
                    copia = generar_copia(template, datos)
                    resultado = motor.convertir_hoja(copia, hoja)
                    verificar_identidad_pdf(
                        resultado, hoja,
                        (trabajador_datos or {}).get("C17", ""),
                        (trabajador_datos or {}).get("C18", ""),
                        nombre_previo,
                    )
                    archivo_pdf = hoja.replace(" ", "_").replace(".", "")
                    paquete.writestr(f"{indice:02d}_{archivo_pdf}.pdf", resultado.contenido)
                    total_paginas += resultado.paginas
                    progreso.progress(indice / len(seleccion))
                paquete.writestr(
                    "IMPORTANTE.txt",
                    "ALCANTO: documentos pendientes de revisión de contenido legal, preventivo y firmas.\n"
                    "El XLSX maestro y sus fórmulas originales no se modificaron.\n",
                )
            st.session_state["pdf_generados"] = bolsa.getvalue()
            st.session_state["pdf_firma"] = firma
            st.success(f"Se generaron {len(seleccion)} documentos ({total_paginas} páginas). Revisa antes de imprimir.")
        except (ErrorDeConversion, PlantillaInvalida, ValueError) as error:
            st.session_state.pop("pdf_generados", None)
            st.error(str(error))
        except Exception:
            st.session_state.pop("pdf_generados", None)
            st.error("El proveedor de conversión no pudo generar todos los documentos; revisa sus credenciales y cuota.")
    if st.session_state.get("pdf_firma") == firma and st.session_state.get("pdf_generados"):
        st.download_button(
            "⬇ Descargar documentos PDF para imprimir",
            data=st.session_state["pdf_generados"],
            file_name="ALCANTO_documentos_imprimibles.zip",
            mime="application/zip", type="primary",
        )


def main() -> None:
    inyectar_css()
    st.markdown("<div class='alcanto-top'><strong>PROYECTO ALCANTO</strong><p>Empresas, trabajadores, subcontratos y prevención | Automático y online</p></div>",unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("## 📄 ALCANTO")
        st.caption("Gestiona el sistema sin instalar Excel")
        if st.checkbox("Confirmo que deseo borrar los datos de esta sesión"):
            if st.button("Borrar datos temporales"):
                st.session_state.clear()
                st.rerun()
        st.divider()
        st.markdown("**Almacenamiento**")
        st.write("🕒 Temporal y separado por visitante")
        st.markdown("**Motor de impresión**")
        st.write("✅ Credenciales configuradas" if secret("ASPOSE_CLIENT_ID") and secret("ASPOSE_CLIENT_SECRET") else "⚠️ Aspose no configurado")
        st.caption("No guardar archivos con RUT en GitHub público.")
    template=plantilla_actual()
    if not template:
        st.warning("El Excel interno todavía no está instalado en el servidor. Puedes registrar empresas y trabajadores; para generar PDF el administrador debe instalarlo una sola vez. No necesitas subir archivos desde esta página.")
        catalogo = catalogo_predefinido()
    else:
        try:
            catalogo = catalogos(template)
        except Exception:
            st.error("El motor no pudo leer los catálogos internos. La pantalla conserva las opciones originales, pero se bloqueará la impresión hasta corregir la plantilla.")
            catalogo = catalogo_predefinido()
        else:
            catalogo["direcciones"] = catalogo_predefinido()["direcciones"]
    st.info("Modo sin contraseña: cada visitante usa su propia sesión temporal. Los registros no se comparten y se pierden al cerrar o reiniciar la sesión. No existe almacenamiento histórico persistente.")
    st.markdown("<div class='alcanto-box'>La fórmula y la presentación del Excel original se respetan. Los documentos se obtienen desde una copia temporal sin sobrescribir la plantilla.</div>",unsafe_allow_html=True)
    tab1,tab2 = st.tabs(["📋 Registrar empresas y trabajadores", "🖨️ Documentación e impresión"])
    with tab1:
        empresas=formulario_empresa()
        empresa,trabajador=formulario_trabajador(empresas,catalogo)
    with tab2:
        empresas = listar("empresas")
        if not empresas:
            st.info("Registra una empresa para ver su documentación. No necesitas registrar trabajadores para los documentos de empresa.")
        else:
            empresa_id = st.selectbox(
                "Empresa para documentos",
                options=[e["id"] for e in empresas],
                format_func=lambda key: next(
                    e["valores"].get("C5", "Empresa") for e in empresas if e["id"] == key
                ),
            )
            company = next(e for e in empresas if e["id"] == empresa_id)
            personas = [
                t for t in listar("trabajadores") if t.get("empresa_id") == empresa_id
            ]
            persona_id = st.selectbox(
                "Tipo de documentación",
                options=[""] + [t["id"] for t in personas],
                format_func=lambda key: "Solo documentos de empresa" if not key else next(
                    t.get("valores", {}).get("C17", "Trabajador")
                    for t in personas if t["id"] == key
                ),
            )
            worker = next((t for t in personas if t["id"] == persona_id), None)
            if worker:
                st.caption("Se reutilizan automáticamente los antecedentes de esta empresa.")
                cargo_pts = worker.get("valores", {}).get("C29", "")
            else:
                st.info("Puedes generar documentación de empresa sin trabajador. Selecciona un cargo únicamente si necesitas un PTS corporativo.")
                cargo_pts = st.selectbox(
                    "Cargo para PTS de empresa",
                    options=[""] + catalogo["cargos"],
                    key="cargo_pts_empresa",
                )
            if not company.get("valores", {}).get("D30"):
                st.warning("La empresa no tiene obra registrada. Los documentos que la necesiten seguirán pendientes.")
            confirma_jurada = st.checkbox(
                "Confirmo, bajo mi responsabilidad, que en el período y obra declarados "
                "la empresa NO tuvo trabajadores dependientes; esta declaración es verdadera.",
                value=False,
                key="confirma_jurada_empresa",
            )
            descargar_documentos(
                template, company, worker, catalogo,
                cargo_pts=cargo_pts, confirma_jurada=confirma_jurada,
            )
    st.caption("Alcanto online · Contratos, IRL, PTS y registros. Es obligatorio revisar los PDF antes de imprimir, firmar o entregar.")


if __name__ == "__main__":
    main()
