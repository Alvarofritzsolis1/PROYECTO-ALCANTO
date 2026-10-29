# Documentos que se pueden obtener desde el Excel

**Interpretación:** «Automático» significa que la hoja de salida **se rellena mediante las fórmulas ya existentes al introducir datos en el libro**. No significa que el archivo se exporte, firme, envíe o archive como PDF de manera autónoma.

| Documento / hoja de salida | Datos principales que utiliza | Resultado y condición |
|---|---|---|
| **Contrato de trabajo — Contrato Imprimible** | Empresa, representante, trabajador, cargo, obra, jornada, sueldo, fechas, AFP y salud | Contrato completado por fórmulas, listo para revisión e impresión |
| **Anexo de traslado — Anexo Traslado** | Empresa, trabajador, cargo, obra inicial, destinos autorizados y locomoción | Anexo completado para revisión |
| **Prórroga — Anexo extension contrato** | Partes, fechas originales y nueva fecha de término en la propia hoja | Anexo generado; la nueva fecha se debe revisar e ingresar cuando corresponda |
| **Inducción preventiva — INDUCCION PREVENCION** | Empresa, representante, rubro, contacto, obra y fecha | Formularios y registros de inducción identificados automáticamente; revisar cada sección |
| **IRL — IRL** | Trabajador, RUT, empresa, cargo y obra | Información de riesgos según matrices, tareas, peligros y medidas disponibles |
| **PTS — PTS.** | Empresa, representante, cargo y contenido de MATRIZ PTS | Plantilla se completa automáticamente **solo hasta donde exista contenido para el cargo** |
| **Constancia entrega PTS — ENTREGA PTS** | Empresa, trabajador, RUT, rubro, localidad y fecha | Constancia completada para revisión y firma |
| **Entrega EPP — Registros Entrega EPP** | Empresa, trabajador, RUT, cargo, obra y fecha | Identificación y encabezados automáticos; el registro específico de EPP se completa y valida según la entrega real |
| **Recepción reglamento — REGLAMENTO INTERNO** | Empresa, trabajador, RUT, ciudad y fecha | Constancia de recepción preparada para revisión y firma |
| **Declaración jurada — DECLARACION JURADA** | Empresa, representante, rubro, obra, fecha y otras condiciones | Declaración preparada; **verificar que el contenido declarado sea verdadero** antes de firmar |

## Flujo visual

```text
Datos Contrato
    |
    +-- Empresa / representante ------> documentos laborales e inducción
    +-- Trabajador / RUT -------------> contrato, IRL, anexos, entregas
    +-- Cargo / especialidad ---------> contrato, IRL, PTS, EPP
    +-- Obra -------------------------> contrato, traslado, inducción, IRL, EPP
    +-- Sueldo / jornada / fechas ----> contrato y prórrogas
    |
    +-- MATRIZ IRL -------------------> IRL por actividad y riesgo
    +-- MATRIZ PTS -------------------> PTS por cargo, si está completo
```

## Importante sobre disponibilidad

- **Tener una hoja que se autocompleta no equivale a que el documento esté completo para ser firmado.**
- En `MATRIZ PTS` se observaron **3 registros con contenido técnico completo y 23 registros pendientes** (17 campos de contenido revisados por registro). Ver [pendientes](04_PTS_PENDIENTES.md).
- Las hojas de matrices y listas auxiliares **no son documentos de salida para firma**.
- El libro es una ficha activa; la conservación de un historial por cada trabajador/empresa y la producción automatizada de PDFs requieren una mejora separada y pruebas que no alteren el resultado actual.
