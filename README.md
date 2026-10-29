# PROYECTO ALCANTO — Plataforma Streamlit 100% online

**Aplicación web sin contraseña.** Se abre directamente desde Streamlit Cloud y no requiere Excel, Windows ni registro de acceso para usar la interfaz. El usuario **no sube ningún XLSX**: solo completa los formularios de empresa y trabajador. El modelo original se instala una sola vez en el servidor, y la generación de PDF usa una copia temporal del libro, conservando sus fórmulas; el cálculo depende de Aspose.Cells Cloud.

**Importante sobre privacidad:** al eliminar la contraseña, los registros de empresas y trabajadores quedan aislados en la sesión temporal de cada visitante. La plantilla maestra se lee únicamente desde el servidor; no se recuperan registros de un almacenamiento común, aunque existan credenciales S3; tampoco se almacenan historiales permanentes. Al cerrar o perder la sesión puede ser necesario ingresar nuevamente la información. Esta decisión evita que terceros accedan a datos personales de otros usuarios.

**[Web sin subir Excel](docs/09_DESPLIEGUE_SIN_SUBIR_EXCEL.md)** · **[Ver cómo desplegar en Streamlit Community Cloud](docs/07_STREAMLIT_CLOUD.md)** · [Modo sin contraseña: privacidad y límites](docs/08_MODO_SIN_CONTRASENA.md) · [Entrar a Streamlit](https://share.streamlit.io/)

**Estado de verificación:** revisión del archivo real con **17 hojas y 310 fórmulas**, seis pruebas estructurales aprobadas. **Aún pendiente**: conectar credenciales de Aspose y almacenamiento privado, desplegar en la cuenta Streamlit del usuario y validar los PDFs de las diez hojas. No se garantiza equivalencia visual hasta realizar estas comprobaciones.

**Importante:** el código publicado es público, pero el Excel con RUT y nombres **no se ha subido a GitHub**. La versión Windows se conserva en `legacy/app_windows.py` y el prototipo Next.js en `web/`; ninguno es el punto de entrada del despliegue Streamlit.

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
