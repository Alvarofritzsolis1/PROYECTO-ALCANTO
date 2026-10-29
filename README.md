# PROYECTO ALCANTO
### Automatización de documentación laboral y prevención para empresas contratistas

**Base del sistema:** un Excel existente, probado por su propietario, que autocompleta documentos cuando se ingresan datos de empresa, representante, trabajador, especialidad y obra. **No se reconstruye ni se elimina lo que ya funciona.**

## Aplicación local para generar PDF imprimibles

Ya existe [`app.py`](app.py): interfaz **Streamlit** conectada a **Microsoft Excel de escritorio** mediante `pywin32`.

- **No altera el Excel original:** trabaja sobre una copia temporal y la descarta al terminar.
- **No modifica fórmulas:** bloquea escrituras en celdas con fórmulas; Excel recalcula sus propias fórmulas.
- **Conserva el archivo para imprimir:** exporta cada hoja seleccionada con `Worksheet.ExportAsFixedFormat` respetando áreas de impresión.
- **Identifica qué documentos se pueden generar** a partir de los datos rellenados y marca contenido PTS pendiente.
- **Estado:** implementación publicada, validación de PDF real en Windows + Excel aún pendiente.

**Instalar y usar:** [Instrucciones app para Windows](docs/06_APP_IMPRESION.md).

Ejecutar en PowerShell desde la carpeta del proyecto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

**No publicar en Streamlit Cloud o servidores externos:** procesa RUT y datos laborales; Microsoft desaconseja automatización de Office sin escritorio interactivo.

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
