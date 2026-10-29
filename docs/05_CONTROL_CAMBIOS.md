# Protocolo de preservación, mejoras y validación

## Regla central
**No quitar nada. No romper lo que funciona. Completar solo lo pendiente y añadir funcionalidades de forma compatible.**

## Base original de referencia
- Archivo facilitado: `PROYECTO AUTOMATIZACION GESTION CONTRATISTAS FINAL.xlsx`
- SHA-256 de la versión recibida: `b24a43377506a85afd1f4dbe5c78f24b15dbdb6dc7e51ac1fdad842784e1e034`
- El archivo contiene información personal y **no está publicado** en el repositorio público.

## Flujo obligatorio para todo cambio

1. Resguardar el Excel original y verificar su SHA-256.
2. Editar solo una **copia** y documentar la celda/rango intervenido.
3. Conservar nombres de hojas, fórmulas, estilos, áreas de impresión y matrices.
4. Completar campos técnicos pendientes, sin alterar procedimientos ya completos.
5. Probar con **datos ficticios**, al menos los cargos albañilería, gasfitería, pintura y un cargo PTS pendiente.
6. Comparar salidas antes/después: contrato, anexos, inducción, IRL, PTS, entrega PTS, EPP, reglamento y declaración.
7. Verificar que se generen las mismas páginas y formato; comprobar que las fechas, identificación y contenido técnico correspondan.
8. Registrar en GitHub qué cambió, qué se validó y qué quedó pendiente.

## Requisitos para nuevas funciones de documentos
- Seleccionar empresa y trabajador sin sobrescribir historiales anteriores (si se incorpora base histórica).
- Presentar un estado por documento: `datos incompletos`, `datos completos / revisar`, `contenido técnico pendiente`, `validado`.
- No marcar como «listo para firma» un documento con datos faltantes o matriz PTS incompleta.
- Si se implementa exportación PDF, respetar estrictamente el diseño e impresión que ya entrega el Excel.
- Evitar publicar documentos reales y datos personales en GitHub; privilegiar almacenamiento privado y control de acceso.

## Alcance de la documentación actual
Esta documentación describe las dependencias identificadas en las fórmulas. No reemplaza una prueba integral en Excel ni la revisión profesional del cumplimiento normativo.
