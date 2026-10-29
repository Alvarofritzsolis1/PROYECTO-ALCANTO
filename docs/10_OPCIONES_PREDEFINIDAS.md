# Opciones predefinidas de ALCANTO (verificadas en el Excel original)

Esta sección documenta las alternativas de los formularios online. No es una lista inventada: se extrajo del libro original y se contrastó con `MATRIZ PTS` y `Datos Contrato`.

## Obras — menú desplegable `Datos Contrato!D30`

La validación de datos original apunta a `$T$16:$T$18`. Son **exactamente tres obras**:

| Valor del menú | Celda del catálogo | Dirección correspondiente |
|---|---|---|
| Lomas Verdes | T16 | U16 |
| Brisas de Junquillar | T17 | U17 |
| Concepción | T18 | U18 |

La celda `C30` del Excel **no debe editarse manualmente**: su fórmula `IFERROR(VLOOKUP(D30,$T$15:$U$18,2,FALSE),"")` toma la dirección asociada de la tabla auxiliar.

**Comportamiento online:** el usuario elige una de esas tres obras; se conserva el valor exacto para que funcione la fórmula de búsqueda original.

## Renta y condiciones del contrato

| Campo | Ejemplo guardado en el Excel | Comportamiento del formulario |
|---|---:|---|
| `C31` Jornada | 42 horas | Muestra 42 como valor inicial, editable |
| `C32` Sueldo base | $553.553 | Muestra 553553 como valor inicial, editable por trabajador |
| `C34` Frecuencia de pago | MENSUALMENTE | Muestra MENSUALMENTE como valor inicial, editable |
| `C33` Sueldo en letras | Calculado con LET/LAMBDA/TEXTSPLIT | **No editable:** lo calcula el motor de Excel en la nube a partir de C32 |
| `C36` Fecha de ingreso | Fórmula HOY() | **No editable:** respetar la fórmula original |
| `C37` Fecha término | Fórmula C36+29 | **No editable:** respetar la fórmula original |

El importe $553.553 es un **valor de referencia encontrado en la versión recibida**, no una recomendación de sueldo mínimo ni una actualización normativa.

## Cargos / especialidades
La clave de cargo de `MATRIZ PTS!A2:A27` tiene 26 registros, con **25 claves únicas** por la duplicación de GASFITER. Los 25 valores están incorporados en `alcanto_cloud/catalog.py` y se presentan como un menú. Se conserva exactamente su escritura, incluyendo códigos internos, para que funcionen las búsquedas existentes.

## PTS
Solo los procedimientos de ALBAÑIL, GASFITER y PINTOR tienen completos los campos técnicos D:T identificados en la plantilla original; los otros 23 registros no se completarán inventando datos.

## Diferencia entre formulario y PDF

- **Formulario:** las opciones funcionan sin archivo Excel en el navegador y sin plantilla cargada en el servidor.
- **Cálculo e impresión:** el administrador debe instalar la plantilla maestra XLSX de forma privada y configurar el motor Aspose.Cells Cloud en los Secrets de Streamlit. Hasta entonces la exportación sigue deshabilitada; no esconder esta condición.
- No subir el XLSX operativo (contiene datos privados) a GitHub público.
- Las fórmulas originales, sus nombres de hojas y matrices se conservan sin modificación.

## Verificación

El test `tests/test_opciones_excel.py` comprueba que el catálogo del sitio contiene 3 obras, 25 cargos y los valores predeterminados. Cuando se facilita `ALCANTO_TEST_WORKBOOK` como ruta privada, también compara las listas y direcciones directamente con el libro original. Los tests corren en [GitHub Actions](../../actions).
