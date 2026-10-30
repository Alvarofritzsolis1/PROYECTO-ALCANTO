"""Selección documental por datos disponibles, sin obligar a crear trabajador.

Las fórmulas Excel no se editan. Este módulo solo valida campos y combina
datos de la empresa y del trabajador sobre una copia para un documento.
"""
from __future__ import annotations

from .catalog import CAMPOS, DOCUMENTOS, CARGOS_PREDEFINIDOS

HOJAS_EMPRESA = frozenset({
    "INDUCCION PREVENCION", "PTS.", "DECLARACION JURADA",
})
HOJAS_TRABAJADOR = frozenset(d.hoja for d in DOCUMENTOS) - HOJAS_EMPRESA
DOCUMENTOS_POR_HOJA = {d.hoja: d for d in DOCUMENTOS}


def preparar_datos(
    empresa: dict[str, str],
    trabajador: dict[str, str] | None = None,
    *,
    hoja: str,
    cargo_pts: str = "",
) -> dict[str, str]:
    """Combina una sola vez; evita llevar nacionalidad del trabajador a la jurada.

    D30 es la obra principal de empresa, salvo que un trabajador tenga otra
    obra específica. Al crear documento corporativo no se incluyen datos de
    ningún trabajador.
    """
    if hoja not in DOCUMENTOS_POR_HOJA:
        raise ValueError("Hoja de documento desconocida.")
    datos = {k: str(v).strip() for k, v in empresa.items() if k in CAMPOS and isinstance(v, str)}
    if trabajador and hoja in HOJAS_TRABAJADOR:
        datos.update({k: str(v).strip() for k, v in trabajador.items()
                      if (k in CAMPOS or k == "ANEXO_M4") and isinstance(v, str) and str(v).strip()})
    if hoja == "PTS.":
        datos["C29"] = cargo_pts.strip() or (trabajador or {}).get("C29", "").strip()
    if hoja == "DECLARACION JURADA":
        # C19 es una referencia existente del Excel; en este documento
        # se refiere al representante firmante, NUNCA al trabajador.
        datos["C19"] = empresa.get("DECLARANTE_NACIONALIDAD", "").strip()
    return datos


def documento_estado(
    hoja: str, datos: dict[str, str], pts_completos: set[str] | frozenset[str],
    *, tiene_trabajador: bool = False, confirma_jurada: bool = False,
) -> dict[str, object]:
    """Comprobación mínima previa al PDF: no constituye revisión legal."""
    if hoja not in DOCUMENTOS_POR_HOJA:
        raise ValueError("Documento inexistente.")
    doc = DOCUMENTOS_POR_HOJA[hoja]
    faltantes = [r for r in doc.requeridos if not datos.get(r, "").strip()]
    if hoja in HOJAS_TRABAJADOR and not tiene_trabajador:
        estado = "Requiere trabajador"
    elif faltantes:
        estado = "Faltan datos"
    elif hoja in {"Contrato Imprimible", "IRL"} and datos.get("C29", "").upper() not in CARGOS_PREDEFINIDOS:
        estado = "Cargo sin matriz"
    elif hoja == "PTS." and datos.get("C29", "").casefold() not in pts_completos:
        estado = "PTS pendiente"
    elif hoja == "DECLARACION JURADA" and not confirma_jurada:
        estado = "Confirmar declaración"
    else:
        estado = "Datos completos / revisar"
    return {"documento": doc.nombre, "hoja": hoja, "estado": estado,
            "faltan": faltantes, "observacion": doc.observacion,
            "generable": estado == "Datos completos / revisar"}


def estado_por_contexto(
    empresa: dict[str, str], trabajador: dict[str, str] | None,
    pts_completos: set[str] | frozenset[str], *,
    cargo_pts: str = "", confirma_jurada: bool = False,
) -> list[dict[str, object]]:
    """Los 10 documentos son visibles siempre; empresa sola habilita los suyos."""
    salida = []
    for doc in DOCUMENTOS:
        valores = preparar_datos(empresa, trabajador, hoja=doc.hoja, cargo_pts=cargo_pts)
        salida.append(documento_estado(
            doc.hoja, valores, pts_completos,
            tiene_trabajador=bool(trabajador), confirma_jurada=confirma_jurada,
        ))
    return salida
