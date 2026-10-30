# PROYECTO ALCANTO — Gestión de contratistas 100% online

**Ya se pueden generar y descargar PDFs directamente desde Streamlit**, sin instalar Excel, sin subir archivos y sin configurar Aspose. Para un documento se descarga un **PDF**; para varios, un ZIP de PDFs. El generador usa ReportLab y sólo trabaja con los datos de los formularios.

**Flujo básico:** registrar empresa → elegir una de las tres obras → registrar trabajador (solo si el documento lo requiere) → elegir documento → confirmar revisión → **Generar PDF online para imprimir** → **Descargar PDF**.

**Autocompletado:** el trabajador hereda la obra seleccionada en la empresa y su dirección se obtiene del catálogo original. Renta sugerida, jornada y cargos predefinidos se pueden ajustar.

**Tres opciones de exportación según la configuración disponible:**
- **PDF desde las hojas originales XLSX, con LibreOffice/UNO en Linux:** reproduce la estructura y el contenido del Excel original. No necesita Aspose ni Excel instalado en el equipo del usuario. Requiere que el administrador provisione **una sola vez la plantilla privada** en el servidor. Probado con diez tipos de documentos, pero **no certificado visualmente al 100 % frente a Microsoft Excel**.
- **PDF web inmediato:** siempre disponible como **borrador resumido**, sin XLSX, para revisión. No tiene las cláusulas y matrices completas del Excel.
- **Aspose Cloud:** exportación alternativa con credenciales; su equivalencia aún no ha sido validada.

**Importante:** la descarga en la aplicación pública Streamlit NO está verificada sin su URL exacta. La plataforma no deberá anunciar equivalencia ni disponibilidad del motor XLSX si falta la plantilla o LibreOffice.

**Límite esencial:** los PDF web **no son idénticos en formato ni en contenido técnico completo a las salidas Excel**; son documentos resumidos que requieren revisión laboral y preventiva antes de firmar. Los 23 PTS pendientes no se habilitan como si estuvieran completos. El XLSX maestro y todas sus fórmulas permanecen intactos.

**Privacidad:** sin contraseña cada visitante utiliza una sesión temporal aislada; no existe historial compartido ni persistente. Los datos reales de trabajadores nunca se suben al repositorio público.

**[Auditoría del motor Excel original y estado de producción](docs/13_PARIDAD_XLSX_IMPRESION.md)** · **[Guía PDF web](docs/12_PDF_WEB_SIN_ASPOSE.md)** · **[Desplegar con Streamlit Cloud](docs/07_STREAMLIT_CLOUD.md)** · **[Auditoría 150 casos](docs/11_AUDITORIA_150_PRUEBAS.md)** · [Abrir Streamlit](https://share.streamlit.io/)

**Pruebas:** GitHub Actions ejecuta 150 pruebas documentales más pruebas que generan y abren los 10 PDF con datos ficticios y un recorrido completo de formulario en Streamlit.

**Importante:** el Excel con información personal no está publicado. La versión Windows se conserva en `legacy/app_windows.py` y el prototipo Next.js en `web/`; la aplicación activa se despliega desde `app.py`.

---

# PROYECTO ALCANTO
### Automatización de documentación laboral y prevención para empresas contratistas

**Base del sistema:** un Excel existente, probado por su propietario, que autocompleta documentos cuando se ingresan datos de empresa, representante, trabajador, especialidad y obra. **No se reconstruye ni se elimina lo que ya funciona.**

## Código legado (no usado por Streamlit Cloud)

La aplicación Windows con Excel de escritorio se conserva como código de referencia en `legacy/app_windows.py` y no corresponde a la versión que se despliega desde `app.py`.

## ¿Qué documentación genera el Excel?

| Documento | Origen | Estado |
|---|---|---|
| Contrato de trabajo | `Contrato Imprimible` | Se rellena desde `Datos Contrato` |
| Anexo de traslado | `Anexo Traslado` | Se rellena con cargo, obra y destinos |
| Anexo de prórroga | `Anexo extension contrato` | Se rellena; nueva fecha por revisar |
| Inducción de prevención | `INDUCCION PREVENCION` | Formularios y registros vinculados |
| Información de riesgos laborales (IRL) | `IRL` | Se personaliza por cargo y matrices |
| Procedimiento de trabajo seguro (PTS) | `PTS.` | Automatizado; faltan 23 contenidos en `MATRIZ PTS` |
| Constancia de entrega PTS | `ENTREGA PTS` | Se rellena para revisión y firma |
| Constancia de entrega EPP | `Registros Entrega EPP` | Identificación automática; entrega real por registrar |
| Recepción reglamento interno | `REGLAMENTO INTERNO` | Se rellena para revisión y firma |
| Declaración jurada | `DECLARACION JURADA` | Se rellena; declaraciones por comprobar |

## ¿Qué pasa cuando escribo cada dato?

| Dato rellenado | Documentación que se actualiza |
|---|---|
| **Empresa y RUT** | Las 10 hojas de salida, en sus campos de empresa |
| **Representante legal** | Contrato, prórroga, inducción, PTS, declaración |
| **Nombre/RUT del trabajador** | Contrato, traslado, prórroga, IRL, entrega PTS, EPP, reglamento |
| **Cargo/especialidad** | Contrato, traslado, IRL, PTS y EPP |
| **Obra/faena** | Contrato, traslado, inducción, IRL, EPP y declaración (según referencias directas y derivadas) |
| **Sueldo, jornada, AFP y salud** | Contrato de trabajo |
| **Fecha de ingreso y término** | Contrato y prórroga |
| **Destinos autorizados y locomoción** | Anexo de traslado |

**Detalle completo por celda:** [Qué campo alimenta cada documento](docs/03_CAMPOS_Y_SALIDAS.md).

## Documentación técnica del proyecto

1. [Arquitectura y 17 hojas](docs/01_ARQUITECTURA.md)
2. [Los 10 tipos de documentos generables](docs/02_DOCUMENTOS_GENERABLES.md)
3. [Campos del formulario → documentos](docs/03_CAMPOS_Y_SALIDAS.md)
4. [PTS pendientes — 23 registros](docs/04_PTS_PENDIENTES.md)
5. [Preservación y pruebas de cambios](docs/05_CONTROL_CAMBIOS.md)

## Consulta automática, sin cambiar el Excel

Una utilidad de **solo lectura** muestra qué hojas pueden revisarse según los campos completados y si el PTS del cargo cuenta con contenido técnico:

```bash
python scripts/estado_documental.py "/ruta/privada/PROYECTO AUTOMATIZACION GESTION CONTRATISTAS FINAL.xlsx" --salida estado.md
```

El reporte dice `GENERABLE / REVISAR`, `FALTAN DATOS` o `PTS PENDIENTE`. **No exporta PDFs, no firma documentos y no modifica el libro**. El autollenado de documentos sigue efectuándose con las fórmulas originales en Excel.

## Estado y próxima etapa

- Referencia analizada: **17 hojas, 310 fórmulas**, 14 visibles y 3 ocultas.
- **Prioridad:** completar D:T de 23 registros pendientes en `MATRIZ PTS`, sin tocar los tres procedimientos desarrollados.
- Mejoras futuras, separadas del Excel original: tablero de disponibilidad, historial por empresa/trabajador y validación de la exportación PDF local con el formato original.

## Protección de información

**Este repositorio es público.** El Excel original contiene información privada, por lo que **no se subió aquí**. Tampoco se publican datos personales, RUT o documentos reales de trabajadores. El libro maestro debe almacenarse en un espacio privado autorizado y las pruebas en GitHub usar datos ficticios.

---
_Registro inicial de documentación del sistema: 29 de octubre de 2026. La generación de documentos se realiza dentro de las hojas de Excel. La completitud del contenido y la validez legal requieren revisión humana._
