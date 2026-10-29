# Aplicación ALCANTO — PDF imprimibles conservando fórmulas

**Decisión técnica:** ejecutar en el computador del usuario **Microsoft Excel para Windows** mediante `pywin32`, con una interfaz **Streamlit local** (`app.py`). No utilizar LibreOffice para exportación definitiva ni reconstruir documentos con otro motor.

## Cómo instalar en Windows
Requisitos: Microsoft Excel de escritorio instalado y activado, Python 3.10 o posterior y sesión iniciada de usuario (no ejecutar como servicio del servidor).

1. Abrir PowerShell en la carpeta clonada del repositorio.
2. Ejecutar:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

3. Abrir la dirección local indicada (habitualmente `http://127.0.0.1:8501`).
4. Cargar el Excel ALCANTO desde el computador. **No subirlo a GitHub público.**
5. Seleccionar **Usar datos que ya están completos en el Excel** o **Completar una copia temporal**.
6. Revisar los estados por documento; seleccionar documentos generables y confirmar su revisión.
7. Pulsar **Crear PDF imprimibles** y descargar un ZIP de los archivos PDF.

## Qué hace exactamente

- Lee el documento aportado sin sobrescribirlo.
- Crea una **copia efímera** bajo una carpeta temporal.
- Solo si se pide, escribe valores en celdas de entrada autorizadas de `Datos Contrato`. Antes de cada escritura comprueba que **no contenga fórmula**.
- Las fórmulas originales **se mantienen**; es Excel quien recalcula con `CalculateFullRebuild()`.
- Para cada documento elegido ejecuta `Worksheet.ExportAsFixedFormat(Type=0, IgnorePrintAreas=False)`. Así Excel usa sus áreas de impresión y presentación existentes.
- Cierra sin guardar y destruye la copia temporal. Entrega un ZIP de PDF.

## Documentos compatibles
Contrato, anexo de traslado, prórroga, inducción, IRL, PTS, entrega PTS, entrega EPP, recepción de reglamento y declaración jurada.

La pantalla informa los requisitos mínimos de datos: **FALTAN DATOS**, **GENERABLE / REVISAR** o **PTS PENDIENTE**. Un PTS no se marca generable si su matriz de 17 campos D:T no está completa. La validación es orientativa: no reemplaza comprobar el contenido, la entrega real de EPP, firmas y seguridad preventiva.

## Limitaciones y protección
- **NO se modificó ni se publicó el Excel original.**
- **NO** se guardan modificaciones en el maestro, las fórmulas o estilos.
- Los valores ya existentes permanecen salvo modificaciones opcionales **en la copia temporal únicamente**.
- Las fechas basadas en `HOY()` se actualizan al recalcular; revisar los PDF antes de imprimir.
- La nueva fecha de prórroga en `Anexo extension contrato!M4` sigue a cargo del documento Excel; la primera versión de la aplicación no la cambia.
- No hay una prueba de exportación real en este entorno Linux. **Antes de usar con terceros, hacer prueba visual en PC Windows con Excel, con datos ficticios.**
- Los PDF contienen datos personales, por lo tanto deben guardarse de forma privada.
- **No** alojar la app en Streamlit Cloud, Linux/Vercel, Windows Service ni servidor desatendido. Microsoft no respalda la automatización de Office sin sesión interactiva. Para una futura plataforma web, analizar Microsoft Graph y un entorno de almacenamiento privado.

## Fuentes
- Excel, exportar a PDF: https://learn.microsoft.com/en-us/office/vba/api/excel.worksheet.exportasfixedformat
- Excel, recálculo: https://learn.microsoft.com/en-us/office/vba/api/excel.application.calculatefullrebuild
- Consideraciones Microsoft sobre automatización sin supervisión: https://learn.microsoft.com/en-us/office/client-developer/integration/considerations-unattended-automation-office-microsoft-365-for-unattended-rpa

## Continuidad
Ver `docs/03_CAMPOS_Y_SALIDAS.md` y `docs/04_PTS_PENDIENTES.md` para mapa de datos y procedimientos pendientes.
