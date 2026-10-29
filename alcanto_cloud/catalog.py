"""Catálogo de entradas y documentos, contrastado con el Excel ALCANTO."""
from __future__ import annotations

from dataclasses import dataclass

CAMPOS_EMPRESA = {
    "C5": "Nombre del empleador / empresa",
    "C6": "RUT empleador",
    "C7": "Representante legal",
    "C8": "RUT representante legal",
    "C9": "Teléfono empresa",
    "C10": "Domicilio empleador",
    "C11": "Comuna empresa",
    "C12": "Ciudad empresa",
    "C13": "Correo empresa",
    "C14": "Rubro de la empresa",
}
CAMPOS_TRABAJADOR = {
    "C17": "Nombre completo del trabajador",
    "C18": "RUT trabajador",
    "C19": "Nacionalidad",
    "C20": "Fecha de nacimiento (AAAA-MM-DD)",
    "C21": "Estado civil",
    "C22": "Domicilio trabajador",
    "C23": "Comuna trabajador",
    "C24": "Ciudad trabajador",
    "C25": "Correo trabajador",
    "C26": "Teléfono trabajador",
    "C29": "Cargo del trabajador",
    "D30": "Obra / faena",
    "C31": "Jornada laboral (horas)",
    "C32": "Sueldo base mensual (pesos)",
    "C34": "Frecuencia de pago",
    "C35": "Datos de cuenta / forma de pago",
    "C38": "AFP",
    "C39": "Salud",
    "C43": "Destinos de traslado autorizados",
    "C44": "Asignación de locomoción",
}
CAMPOS = {**CAMPOS_EMPRESA, **CAMPOS_TRABAJADOR}

@dataclass(frozen=True)
class Documento:
    nombre: str
    hoja: str
    requeridos: tuple[str, ...]
    observacion: str = "Revisión y firmas pendientes"

DOCUMENTOS = (
    Documento("Contrato de trabajo", "Contrato Imprimible", ("C5", "C6", "C7", "C8", "C17", "C18", "C19", "C20", "C21", "C22", "C29", "D30", "C31", "C32", "C34", "C38", "C39")),
    Documento("Anexo de traslado", "Anexo Traslado", ("C5", "C6", "C17", "C18", "C29", "D30", "C43")),
    Documento("Anexo de prórroga", "Anexo extension contrato", ("C5", "C6", "C7", "C8", "C17", "C18"), "Fecha de prórroga en la plantilla: comprobar antes de firmar"),
    Documento("Inducción de prevención", "INDUCCION PREVENCION", ("C5", "C6", "C7", "C8", "C14", "D30")),
    Documento("Información de riesgos laborales (IRL)", "IRL", ("C5", "C6", "C17", "C18", "C29", "D30")),
    Documento("Procedimiento de trabajo seguro (PTS)", "PTS.", ("C5", "C6", "C7", "C8", "C29"), "Necesita contenido técnico D:T para el cargo"),
    Documento("Constancia de entrega PTS", "ENTREGA PTS", ("C5", "C6", "C17", "C18", "C29")),
    Documento("Constancia de entrega EPP", "Registros Entrega EPP", ("C5", "C6", "C17", "C18", "C29", "D30")),
    Documento("Recepción de reglamento interno", "REGLAMENTO INTERNO", ("C5", "C6", "C17", "C18")),
    Documento("Declaración jurada", "DECLARACION JURADA", ("C5", "C6", "C7", "C8", "C14", "D30"), "Comprobar que todas las declaraciones sean verdaderas"),
)
HOJAS = {d.hoja: d for d in DOCUMENTOS}


def estado_documental(datos: dict[str, str], pts_listos: set[str]) -> list[dict[str, object]]:
    salida = []
    for doc in DOCUMENTOS:
        faltan = [ref for ref in doc.requeridos if not datos.get(ref, "").strip()]
        if faltan:
            estado = "Faltan datos"
        elif doc.hoja == "PTS." and datos.get("C29", "").casefold().strip() not in pts_listos:
            estado = "PTS pendiente"
        else:
            estado = "Datos completos / revisar"
        salida.append({"documento": doc.nombre, "hoja": doc.hoja, "estado": estado,
                       "faltan": faltan, "observacion": doc.observacion})
    return salida
