# ALCANTO: auditoría del PDF desde el XLSX original

Fecha: 30-10-2026. Estado: motor original probado localmente; **no certificado en el Streamlit público**, cuyo URL todavía falta.

## Errores encontrados

La matriz auxiliar «MATRIZ IRL» tiene un área con formato hasta la fila 1.048.576. Una exportación sin selección de hojas llegó a producir 3.187 páginas, muchas vacías.

El libro original contiene LET/TEXTSPLIT, funciones _xlfn._LONGTEXT y un patrón de sueldo incompatible con la configuración de LibreOffice. La salida inicial mostró #NAME?, fechas inválidas y $640000.000 en vez de $640.000.

El generador web antiguo no estaba usando las hojas originales; producía borradores resumidos.

## Corrección

- scripts/uno_sheet_export.py abre una copia de solo lectura del XLSX privado, incorpora los datos solo en memoria, recalcula, selecciona una sola hoja y exporta su rango de impresión.
- alcanto_cloud/pdf_excel_local.py valida cantidad de páginas, errores de fórmula, fechas, sueldo en letras e identidad. El proceso UNO y todos los archivos temporales se eliminan.
- packages.txt instala libreoffice-calc y python3-uno en Linux.
- app.py ofrece el PDF desde el Excel original cuando motor y plantilla privada existen en el servidor. Sin ellos solo está habilitado el borrador web, sin prometer equivalencia.
- El libro original y sus fórmulas no se sobrescriben. Las adaptaciones de fórmula ocurren exclusivamente en memoria del motor de impresión.

## Resultado verificable en el archivo original con datos ficticios

| Hoja | PDF páginas | Errores detectados |
| --- | ---: | ---: |
| Contrato Imprimible | 2 | 0 |
| Anexo Traslado | 1 | 0 |
| Anexo extension contrato | 2 | 0 |
| INDUCCION PREVENCION | 12 | 0 |
| IRL | 6 | 0 |
| PTS. | 5 | 0 |
| ENTREGA PTS | 1 | 0 |
| Registros Entrega EPP | 1 | 0 |
| REGLAMENTO INTERNO | 1 | 0 |
| DECLARACION JURADA | 1 | 0 |

El contrato se comprobó además con una renta de $640.000 expresada correctamente en cifras y palabras, fecha de nacimiento 14/03/1995, obra Lomas Verdes y ausencia de datos personales anteriores. La salida del motor individual quedó en dos páginas.

**No equivale todavía a una certificación de fidelidad visual píxel a píxel con Microsoft Excel**, ni reemplaza la revisión legal y preventiva de documentos.

## Pendientes para certificar producción

1. Provisionar una sola vez el XLSX maestro en almacenamiento privado del servidor, sin colocar archivos con RUT en GitHub público. El usuario final no debe subir Excel.
2. Verificar que el despliegue Streamlit instaló LibreOffice/UNO y reconoce la plantilla privada.
3. Abrir el URL exacto del Streamlit público y ejecutar la descarga PDF desde Chromium.
4. Revisar las páginas, campos calculados y contenido técnico de cada documento, y completar los PTS aún pendientes.

La prueba pública se preparó en .github/workflows/test_production_streamlit.yml; se ejecuta manualmente con el URL real de la aplicación y deja evidencia en GitHub Actions. Nunca debe declararse «100% validado» mientras las verificaciones anteriores no estén completas.
