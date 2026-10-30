"""Motor de PDF web de ALCANTO: funciona en Streamlit sin Excel ni Aspose.

Genera documentos nuevos a partir de los datos introducidos. NO modifica el XLSX
original ni afirma reproducir exactamente su maqueta de Microsoft Excel.
Los documentos se deben revisar antes de firmar o presentar.
"""
from __future__ import annotations

from datetime import date, timedelta
from html import escape
from io import BytesIO
from zoneinfo import ZoneInfo
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
    HRFlowable, PageBreak,
)

from .catalog import DIRECCIONES_OBRA, HOJAS, RENTA_BASE_REFERENCIA


class ErrorPDFWeb(ValueError):
    """No se puede generar un documento seguro con los datos disponibles."""


AZUL = colors.HexColor("#172e46")
VERDE = colors.HexColor("#187766")
GRIS = colors.HexColor("#586879")
CLARO = colors.HexColor("#edf5f3")
BORDE = colors.HexColor("#d6dfe6")


def hoy_chile() -> date:
    return datetime.now(ZoneInfo("America/Santiago")).date()


def _limpio(datos: dict, celda: str, defecto: str = "") -> str:
    return str(datos.get(celda) or defecto).strip()


def _num_pesos(valor: str) -> str:
    try:
        return "$" + f"{int(valor):,}".replace(",", ".")
    except (ValueError, TypeError):
        raise ErrorPDFWeb("El sueldo debe ser un número entero de pesos.") from None


def _fecha(valor: str, defecto: date) -> date:
    if not valor:
        return defecto
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise ErrorPDFWeb("Las fechas deben tener formato AAAA-MM-DD.") from None


def _fecha_es(fecha: date) -> str:
    meses = ("enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
    return f"{fecha.day} de {meses[fecha.month-1]} de {fecha.year}"


def _plantilla(hoja: str, datos: dict, fecha: date) -> tuple[str, list[tuple[str, str]]]:
    empresa = _limpio(datos, "C5")
    rut_emp = _limpio(datos, "C6")
    representante = _limpio(datos, "C7")
    rut_rep = _limpio(datos, "C8")
    trabajador = _limpio(datos, "C17")
    rut_trab = _limpio(datos, "C18")
    cargo = _limpio(datos, "C29")
    obra = _limpio(datos, "D30")
    direccion_obra = DIRECCIONES_OBRA.get(obra, "Dirección de faena por confirmar")
    domicilio = _limpio(datos, "C10")
    ciudad = _limpio(datos, "C12", "Concepción")
    fecha_es = _fecha_es(fecha)

    if hoja == "Contrato Imprimible":
        sueldo = _num_pesos(_limpio(datos, "C32"))
        jornada = _limpio(datos, "C31")
        frecuencia = _limpio(datos, "C34", "MENSUALMENTE")
        termino = _fecha_es(fecha + timedelta(days=29))
        return "CONTRATO DE TRABAJO A PLAZO FIJO", [
            ("Comparecientes", f"En {ciudad}, a {fecha_es}, entre {empresa}, RUT {rut_emp}, "
             f"representada por {representante}, RUT {rut_rep}, domiciliada en {domicilio}, "
             f"y don(a) {trabajador}, RUT {rut_trab}, nacionalidad {_limpio(datos,'C19')}, "
             f"estado civil {_limpio(datos,'C21')}, domicilio {_limpio(datos,'C22')}, "
             "se celebra el presente contrato."),
            ("PRIMERO · Funciones y lugar de trabajo",
             f"El trabajador prestará servicios como {cargo} en la obra {obra}, "
             f"ubicada en {direccion_obra}. Sus labores y riesgos se detallarán "
             "en la descripción de cargo e IRL correspondiente."),
            ("SEGUNDO · Jornada", f"La jornada ordinaria pactada será de {jornada} "
             "horas semanales, conforme al calendario y distribución acordados, "
             "sin perjuicio de los descansos legalmente procedentes."),
            ("TERCERO · Remuneración", f"El sueldo base mensual será de {sueldo}, "
             f"pagadero {frecuencia.lower()}. La gratificación y demás asignaciones "
             "se determinarán conforme al contrato y normativa aplicable."),
            ("CUARTO · Instrucciones y prevención",
             "El trabajador se compromete a respetar las instrucciones de trabajo, "
             "las medidas de prevención, los procedimientos aplicables y el reglamento "
             "interno vigente. Se dejará constancia de la información y entrega de EPP."),
            ("QUINTO · Vigencia",
             f"El contrato comienza el {_fecha_es(fecha)} y su término previsto es "
             f"el {termino}. Toda prórroga requerirá el acuerdo que corresponda."),
            ("SEXTO · Régimen previsional",
             f"AFP declarada: {_limpio(datos,'C38')}. Sistema de salud declarado: "
             f"{_limpio(datos,'C39')}."),
            ("SÉPTIMO · Ejemplares", "Se firma en ejemplares para las partes, "
             "quienes revisan previamente los antecedentes y condiciones indicadas."),
        ]

    if hoja == "Anexo Traslado":
        return "ANEXO DE TRASLADO DE CONTRATO DE TRABAJO", [
            ("Identificación", f"En {ciudad}, a {fecha_es}, {empresa}, RUT {rut_emp}, "
             f"y el trabajador {trabajador}, RUT {rut_trab}, acuerdan el siguiente anexo."),
            ("PRIMERO · Destino", f"Cargo: {cargo}. Obra actual: {obra}, "
             f"dirección: {direccion_obra}."),
            ("SEGUNDO · Obras autorizadas",
             "El eventual traslado solo comprenderá los destinos acordados: "
             f"{_limpio(datos,'C43')}."),
            ("TERCERO · Condiciones", "Los traslados serán comunicados oportunamente "
             "y no podrán implicar menoscabo de las condiciones laborales. "
             f"Locomoción acordada: {_limpio(datos,'C44','Por definir')}."),
            ("CUARTO · Continuidad", "Las cláusulas del contrato principal "
             "que no se modifiquen expresamente mantendrán su vigencia."),
        ]

    if hoja == "Anexo extension contrato":
        nueva = _limpio(datos, "ANEXO_M4")
        if not nueva:
            raise ErrorPDFWeb("Debes indicar la nueva fecha de término del anexo.")
        termino = _fecha(nueva, fecha)
        if termino <= fecha:
            raise ErrorPDFWeb("La fecha de prórroga debe ser posterior a la fecha del documento.")
        return "ANEXO DE EXTENSIÓN DE CONTRATO A PLAZO FIJO", [
            ("Identificación", f"En {ciudad}, a {fecha_es}, {empresa}, RUT {rut_emp}, "
             f"representada por {representante}, RUT {rut_rep}, y "
             f"{trabajador}, RUT {rut_trab}, suscriben este acuerdo."),
            ("PRIMERO · Contrato original", "Las partes ratifican la existencia "
             "del contrato a plazo fijo vigente y su fecha de término original, "
             "que deberá comprobarse contra el instrumento firmado."),
            ("SEGUNDO · Prórroga", f"Las partes acuerdan modificar la fecha de "
             f"término, estableciéndose como nuevo vencimiento el {_fecha_es(termino)}."),
            ("TERCERO · Vigencia de otras cláusulas", "Las restantes condiciones "
             "del contrato original se mantienen inalteradas."),
        ]

    if hoja == "INDUCCION PREVENCION":
        return "INDUCCIÓN DE PREVENCIÓN · EMPRESA CONTRATISTA", [
            ("Antecedentes", f"Empresa: {empresa} · RUT: {rut_emp}. "
             f"Representante: {representante} · RUT: {rut_rep}. "
             f"Rubro: {_limpio(datos,'C14')}."),
            ("Faena", f"Obra: {obra}. Dirección: {direccion_obra}. "
             f"Fecha de inducción programada: {fecha_es}."),
            ("Temario a impartir", "1. Organización preventiva de la obra y reglamento "
             "para contratistas. 2. Identificación de peligros y análisis de tareas. "
             "3. Procedimientos seguros y permisos de trabajo. 4. Uso, inspección y "
             "reposición de EPP. 5. Emergencias, primeros auxilios y comunicación de "
             "incidentes. 6. Coordinación entre empresa mandante y contratistas."),
            ("Constancia", "Esta es una ficha de inducción para completar. "
             "La capacitación real, asistencia, contenidos impartidos y firmas "
             "deben registrarse por separado; generar el PDF no acredita su ejecución."),
        ]

    if hoja == "IRL":
        medidas = [
            ("Orden y desplazamientos",
             "Mantener vías despejadas, señalizar desniveles y prevenir tropiezos y golpes."),
            ("Manipulación de cargas",
             "Evaluar pesos, utilizar ayudas mecánicas y aplicar técnicas seguras de levantamiento."),
            ("Herramientas y maquinaria",
             "Inspeccionar protecciones, conexiones y estado de los equipos antes de usarlos."),
            ("Trabajo en altura, si aplica",
             "Revisar andamios, barandas, puntos de anclaje y permisos conforme al riesgo real."),
            ("Exposición al ambiente",
             "Controlar polvo, ruido, radiación UV y productos químicos cuando corresponda."),
        ]
        return "INFORMACIÓN DE RIESGOS LABORALES · IRL", [
            ("Identificación", f"Trabajador: {trabajador}, RUT {rut_trab}. "
             f"Empleador: {empresa}, RUT {rut_emp}. Cargo: {cargo}. "
             f"Obra: {obra} ({direccion_obra}). Fecha: {fecha_es}."),
            ("Marco preventivo", "Ficha de información de riesgos laborales basada en "
             "las tareas declaradas y los controles generales. Debe complementarse "
             "y validarse con la matriz de riesgos vigente del puesto y la faena "
             "antes de efectuar una entrega formal."),
            *medidas,
            ("Acreditación", "La entrega de esta información y su explicación "
             "deben quedar respaldadas con firma y registro de capacitación."),
        ]

    if hoja == "PTS.":
        temas = {
            "PINTOR": [
                ("Objetivo", "Preparar y aplicar revestimientos evitando exposición a "
                 "vapores, contacto dérmico, proyección de partículas y caídas."),
                ("Herramientas", "Brochas, rodillos, lijadoras, equipos pulverizadores "
                 "y escaleras o andamios conforme a la evaluación de la actividad."),
                ("Medidas", "Ventilar recintos; revisar fichas de seguridad de pinturas "
                 "y solventes; usar protección respiratoria, ocular y de manos "
                 "según exposición; controlar trabajo en altura y mantener orden."),
            ],
            "GASFITER": [
                ("Objetivo", "Realizar instalaciones sanitarias y reparaciones "
                 "previniendo cortes, quemaduras y exposiciones a gases."),
                ("Herramientas", "Llaves de apriete, cortatubos, soldadura, "
                 "equipos de ensayo y herramientas manuales autorizadas."),
                ("Medidas", "Verificar aislamiento y cierre de suministros, "
                 "ventilación, estabilidad de excavaciones y protección adecuada "
                 "antes de iniciar trabajos."),
            ],
            "ALBAÑIL": [
                ("Objetivo", "Ejecutar albañilería y terminaciones previniendo "
                 "caídas, golpes, manipulación excesiva de cargas y polvo."),
                ("Herramientas", "Nivel, plomada, pala, carretilla, "
                 "llana, herramientas de corte y mezclado."),
                ("Medidas", "Ordenar material y escombros, controlar polvo "
                 "de sílice y proyección de partículas, inspeccionar "
                 "andamios y usar EPP apropiado."),
            ],
        }
        if cargo not in temas:
            raise ErrorPDFWeb("No hay PTS completo para este cargo. No se generará un procedimiento ficticio.")
        return f"PROCEDIMIENTO DE TRABAJO SEGURO · {cargo}", [
            ("Empresa", f"{empresa} · RUT {rut_emp}. "
             f"Representante legal: {representante} · RUT {rut_rep}. "
             f"Domicilio: {domicilio}. Fecha de elaboración: {fecha_es}."),
            *temas[cargo],
            ("Responsabilidades", "La supervisión debe informar el procedimiento, "
             "verificar las condiciones de ejecución y dejar registro de la capacitación. "
             "Cada trabajador debe respetar los controles de la faena."),
            ("Revisión técnica", "Este documento web es una versión resumida. "
             "Antes de utilizarlo como PTS formal, el prevencionista debe "
             "contrastarlo con el contenido íntegro de la matriz original."),
        ]

    if hoja == "ENTREGA PTS":
        return "CONSTANCIA DE ENTREGA DE PROCEDIMIENTO DE TRABAJO SEGURO", [
            ("Identificación", f"Trabajador: {trabajador}, RUT {rut_trab}. "
             f"Empresa: {empresa}, RUT {rut_emp}. Cargo: {cargo}. Fecha: {fecha_es}."),
            ("Procedimiento", f"Procedimiento de trabajo seguro correspondiente "
             f"al cargo de {cargo}."),
            ("Registro de entrega", "Complete y firme este documento solo después "
             "de realizar la entrega y capacitación efectivas. "
             "La emisión del PDF por sí sola no acredita recepción."),
            ("Observaciones", "Fecha y hora efectiva: ____________________. "
             "Capacitador: ____________________."),
        ]

    if hoja == "Registros Entrega EPP":
        return "REGISTRO DE ENTREGA DE ELEMENTOS DE PROTECCIÓN PERSONAL", [
            ("Identificación", f"Trabajador: {trabajador}, RUT {rut_trab}. "
             f"Cargo: {cargo}. Obra: {obra}. Empresa: {empresa}, RUT {rut_emp}. "
             f"Fecha del registro: {fecha_es}."),
            ("EPP a verificar", "Casco de seguridad; calzado de seguridad; "
             "protección visual; guantes; protección auditiva o respiratoria "
             "según riesgos; arnés si la tarea exige trabajo en altura."),
            ("Constancia", "La tabla de entrega efectiva se completa en el acto "
             "de suministro. No se deben declarar como recibidos EPP que aún "
             "no se hayan proporcionado."),
        ]

    if hoja == "REGLAMENTO INTERNO":
        return "RECEPCIÓN DE REGLAMENTO INTERNO", [
            ("Identificación", f"Trabajador: {trabajador}, RUT {rut_trab}. "
             f"Empleador: {empresa}, RUT {rut_emp}. Fecha: {fecha_es}."),
            ("Recepción", "Declaro que recibí un ejemplar íntegro del Reglamento "
             "Interno de Orden, Higiene y Seguridad y que se me informó dónde "
             "consultar su versión vigente. Esta constancia debe suscribirse "
             "después de la entrega efectiva."),
            ("Información adicional", "Se indicó la existencia de normas "
             "de prevención de riesgos, deberes de seguridad y procedimientos "
             "internos de consulta y reporte."),
        ]

    if hoja == "DECLARACION JURADA":
        nacionalidad = _limpio(datos, "C19")
        if not nacionalidad:
            raise ErrorPDFWeb("Falta la nacionalidad del representante declarante.")
        return "DECLARACIÓN JURADA · EMPRESA CONTRATISTA", [
            ("Declarante", f"Yo, {representante}, RUT {rut_rep}, de nacionalidad "
             f"{nacionalidad}, en representación de {empresa}, RUT {rut_emp}, "
             f"domiciliada en {domicilio}, ciudad de {ciudad}, declaro bajo juramento:"),
            ("Declaración", f"Durante el mes de {fecha.strftime('%m/%Y')}, "
             f"no he mantenido trabajadores bajo subordinación o dependencia "
             f"en la obra {obra}, ubicada en {direccion_obra}."),
            ("Responsabilidad", "Esta declaración deberá emitirse únicamente "
             "cuando los hechos indicados sean ciertos. El firmante asume "
             "la responsabilidad por el contenido y alcance de la declaración."),
        ]

    raise ErrorPDFWeb("No existe un generador para esta hoja.")


def _pie_pagina(canvas, doc):
    canvas.saveState()
    w, _ = A4
    canvas.setStrokeColor(BORDE)
    canvas.line(18*mm, 17*mm, w-18*mm, 17*mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRIS)
    canvas.drawString(18*mm, 12*mm, "ALCANTO | Documento web para revisión y firma")
    canvas.drawRightString(w-18*mm, 12*mm, f"Página {doc.page}")
    canvas.restoreState()


def generar_pdf_web(hoja: str, datos: dict[str, str], *,
                    fecha: date | None = None,
                    confirma_jurada: bool = False) -> bytes:
    """PDF imprimible de una sola hoja/documento lógico, 100% Python.

    Los datos identificatorios no se transmiten a servicios de terceros.
    No modifica XLSX. No sustituye la validación laboral o preventiva.
    """
    if hoja not in HOJAS:
        raise ErrorPDFWeb("Documento no reconocido.")
    if hoja == "DECLARACION JURADA" and not confirma_jurada:
        raise ErrorPDFWeb("No se confirmó la veracidad de la declaración jurada.")
    fecha = fecha or hoy_chile()
    doc_cfg = HOJAS[hoja]
    faltan = [x for x in doc_cfg.requeridos if not _limpio(datos, x)]
    if faltan:
        raise ErrorPDFWeb("Faltan campos para imprimir: " + ", ".join(faltan))
    title, secciones = _plantilla(hoja, datos, fecha)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="AlcantoTitle", fontName="Helvetica-Bold", fontSize=13, leading=17,
        alignment=TA_CENTER, textColor=AZUL, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="AlcantoSection", fontName="Helvetica-Bold", fontSize=10.1,
        leading=14, textColor=AZUL, spaceBefore=12, spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="AlcantoBody", fontName="Helvetica", fontSize=9.25,
        leading=14, textColor=AZUL, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="AlcantoNote", parent=styles["AlcantoBody"],
        fontSize=8.3, leading=12, textColor=GRIS,
    ))

    output = BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
        topMargin=19*mm, bottomMargin=22*mm, title=title,
        author="PROYECTO ALCANTO",
    )
    story = [
        Paragraph("PROYECTO ALCANTO", styles["AlcantoSection"]),
        HRFlowable(width="100%", thickness=1.1, color=VERDE, spaceAfter=12),
        Paragraph(escape(title), styles["AlcantoTitle"]),
    ]
    if hoja in ("INDUCCION PREVENCION", "IRL", "PTS."):
        story.append(Paragraph(
            "Verificar contenido técnico, faena y requisitos aplicables con "
            "el responsable de prevención antes de usar formalmente.",
            styles["AlcantoNote"],
        ))
    for encabezado, texto in secciones:
        story.append(Paragraph(escape(encabezado), styles["AlcantoSection"]))
        story.append(Paragraph(escape(texto).replace("\n", "<br/>"), styles["AlcantoBody"]))

    if hoja == "Registros Entrega EPP":
        epp = ["Casco de seguridad", "Calzado de seguridad", "Lentes de seguridad",
               "Guantes de protección", "Protección respiratoria/auditiva",
               "Arnés (si corresponde)", "Otro EPP especificado"]
        celda = lambda txt: Paragraph(escape(txt), styles["AlcantoNote"])
        tabla = [[celda("Equipo"), celda("Talla"), celda("Cantidad"), celda("Fecha")]]
        tabla += [[celda(item), "", "", ""] for item in epp]
        tbl = Table(tabla, colWidths=[72*mm, 30*mm, 32*mm, 40*mm], repeatRows=1,
                    rowHeights=[9*mm]+[10*mm]*len(epp))
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,0), CLARO),
            ("GRID",(0,0),(-1,-1),.4,BORDE),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("LEFTPADDING",(0,0),(-1,-1),7),
        ]))
        story.append(Spacer(1, 8))
        story.append(tbl)

    if hoja not in ("IRL", "PTS.", "INDUCCION PREVENCION"):
        trabajador = _limpio(datos, "C17")
        empresa = _limpio(datos, "C5")
        representante = _limpio(datos, "C7", empresa)
        firmantes = [
            ("EMPRESA / REPRESENTANTE", representante, _limpio(datos, "C8")),
            ("TRABAJADOR", trabajador, _limpio(datos, "C18")),
        ]
        if hoja == "DECLARACION JURADA":
            firmantes = [firmantes[0]]
        story.append(Spacer(1, 14*mm))
        for titulo_firma, persona, rut in firmantes:
            story.append(Paragraph("_" * 47, styles["AlcantoBody"]))
            story.append(Paragraph(escape(titulo_firma + " · " + persona +
                                         (" · RUT " + rut if rut else "")),
                                   styles["AlcantoNote"]))
            story.append(Spacer(1, 9*mm))
    else:
        story.extend([
            Spacer(1, 10*mm),
            Paragraph("Nombre, fecha y firma del responsable: ______________________________",
                      styles["AlcantoNote"]),
            Spacer(1, 6*mm),
            Paragraph("Recepción / capacitación efectiva (cuando corresponda): ______________________________",
                      styles["AlcantoNote"]),
        ])

    doc.build(story, onFirstPage=_pie_pagina, onLaterPages=_pie_pagina)
    result = output.getvalue()
    if not result.startswith(b"%PDF-") or len(result) < 500:
        raise ErrorPDFWeb("No fue posible generar un PDF válido.")
    return result
