# PDF directamente desde Streamlit — sin Excel ni Aspose

## Problema corregido
Anteriormente el botón `Generar PDF online para imprimir` exigía:
1. Que el servidor tuviera la plantilla interna `ALCANTO_MODELO.xlsx`.
2. Que en Streamlit Secrets estuvieran `ASPOSE_CLIENT_ID` y `ASPOSE_CLIENT_SECRET`.

Sin esas condiciones, el botón permanecía deshabilitado aun cuando empresa y trabajador estuvieran correctamente registrados.

## Solución operativa
Se incorporó `alcanto_cloud/pdf_web.py`, con **ReportLab** (Python puro). Crea PDF en Streamlit Community Cloud **sin claves, sin Excel instalado y sin subir archivos**.

El usuario:
1. Registra una empresa, selecciona una de las tres obras predefinidas.
2. Si necesita un documento personal, agrega o selecciona un trabajador; el formulario hereda automáticamente la obra principal de la empresa.
3. En **Documentación e impresión**, selecciona **Solo documentos de empresa** o un trabajador.
4. Elige los documentos disponibles, confirma que los revisará y pulsa **Generar PDF online para imprimir**.
5. Descarga un **PDF** cuando seleccionó solo un documento; o un ZIP de PDF si seleccionó varios.

Se conserva un segundo motor **opcional** cuando existen plantilla XLSX privada y Aspose configurado. Este último busca reproducir el formato original del Excel; la alternativa web usa una **maquetación diferente** y documentos abreviados.

## Las tres obras precargadas
- **Lomas Verdes** — Av. Jorge Alessandri 866 Interior, Lomas Verdes.
- **Brisas de Junquillar** — Ruta 160, Km 14,2 Interior, San Pedro de la Paz.
- **Concepción** — Av. Quiñenco N.º 4001, Escuadrón, Sector Praderas de Coronel.

La obra elegida en la empresa se muestra como selección inicial del trabajador y su dirección aparece automáticamente. Puede modificarse para otro destino. No se altera la fórmula `VLOOKUP` del Excel original.

## Documentos generados en modo web
Contrato, traslado, prórroga, inducción, IRL, PTS (solo cargos con contenido disponible), entrega PTS, entrega EPP, recepción de reglamento y declaración jurada (solo bajo confirmación expresa).

### Límites importantes
- El PDF web **no es un calco del diseño ni del contenido íntegro** del Excel original. Es un documento web con datos y apartados principales, útil para revisión e impresión de borradores.
- En IRL y PTS, el contenido técnico web es resumido. Debe contrastarse con las matrices originales y ser validado por prevención antes de firmar.
- Las entregas de EPP y capacitaciones reales solo pueden acreditarse cuando ocurrieron efectivamente; generar una hoja PDF no sustituye firma, recepción ni registro.
- Los 23 PTS de matriz incompleta siguen bloqueados.
- La declaración de inexistencia de trabajadores dependientes exige confirmación; no debe imprimirse si es falsa.
- La copia del Excel original sigue intacta, pero el motor web no ejecuta sus 310 fórmulas: usa directamente los campos y sus opciones validadas. La exportación idéntica al Excel requiere el motor opcional.

## Evidencia de funcionamiento
- `tests/test_pdf_web.py` genera y abre **10 PDF reales** con datos ficticios, valida nombres, obra, sueldo, fechas y ausencia de datos antiguos.
- `tests/test_ui_pdf_web_completo.py` simula la operación de Streamlit con empresa ficticia **sin trabajador** y comprueba que el documento PDF se produce.
- `tests/test_150_documentos.py` mantiene las 150 comprobaciones de reglas.
- [GitHub Actions](../../actions) ejecuta pruebas automáticamente.

## Para actualizar Streamlit
Desde [Streamlit Community Cloud](https://share.streamlit.io/), abrir la aplicación y usar **Manage app → Reboot app** si continúa cargando código antiguo. El archivo de despliegue es `app.py` en la rama `main`.

**Nota de privacidad:** en la versión pública sin contraseña, empresa y trabajador solo existen en la sesión temporal del visitante. No guardar datos de terceros en un repositorio público.
