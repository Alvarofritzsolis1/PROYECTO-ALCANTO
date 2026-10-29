# Arquitectura del libro — PROYECTO ALCANTO

## Objetivo
Gestionar contratos de subcontratistas y documentación de prevención de riesgos mediante un libro Excel que reutiliza los antecedentes ingresados en **Datos Contrato**.

**Condición del proyecto:** el propietario ha probado el funcionamiento del libro. La misión de este repositorio es **preservar lo que existe y completar lo pendiente**, especialmente el contenido PTS; no rehacer ni eliminar hojas, fórmulas o formatos.

## Flujo operativo

1. Se llenan los antecedentes de empresa y representante en `Datos Contrato`.
2. Se llenan los antecedentes personales del trabajador.
3. Se eligen cargo, obra, condiciones del contrato, fechas y otras variables.
4. Las hojas de salida reciben los datos por fórmulas y búsquedas.
5. Las matrices de cargos, IRL, sustancias y PTS aportan contenido técnico.
6. Se revisan, imprimen o guardan los documentos según corresponda. El **llenado automático dentro de Excel** está presente; la exportación automática a PDF y el archivado histórico no se consideran implementados sin prueba específica.

## Inventario de las 17 hojas

| Hoja | Función |
|---|---|
| Datos Contrato | Captura de antecedentes, parámetros y selección de obra |
| Contrato Imprimible | Contrato de trabajo |
| Anexo Traslado | Anexo de traslado entre obras |
| Anexo extension contrato | Prórroga de contrato |
| INDUCCION PREVENCION | Inducción y registros preventivos |
| IRL | Información de riesgos laborales por cargo |
| Base_Datos_Sustancias | Base auxiliar de sustancias químicas (oculta) |
| Matriz IRL Optimizada | Condiciones y herramientas por especialidad (oculta) |
| PTS. | Procedimiento de trabajo seguro a partir de la matriz |
| ENTREGA PTS | Constancia de entrega de PTS |
| Registros Entrega EPP | Comprobante de entrega de protección personal |
| REGLAMENTO INTERNO | Constancia de recepción del reglamento |
| MATRIZ PTS | Catálogo de contenido técnico para procedimientos |
| Hoja1 | Listados auxiliares (oculta) |
| DECLARACION JURADA | Declaración del representante |
| MATRIZ IRL | Catálogo de actividades, peligros, riesgos y medidas |
| MATRIZ DESCRIPCION DE CARGO IRL | Descripción de funciones por cargo |

Inventario observado en la versión recibida el 29-10-2026: **17 hojas, 310 fórmulas, 14 hojas visibles y 3 ocultas**.

## Principios de preservación

- Mantener **todas** las hojas originales, sus fórmulas, enlaces, formatos y estructura de impresión.
- No corregir ni suprimir fórmulas solo por un hallazgo teórico; primero reproducir cualquier problema sobre una copia de prueba.
- Completar la información faltante de las matrices sin destruir contenido anterior.
- Proponer extensiones en ramas o copias y validar contrato, IRL, PTS, anexos, entregas e inducción con casos reales **anonimizados**.
- La conformidad laboral y preventiva debe verificarse por responsables competentes antes de usar documentos formalmente.

## Privacidad del repositorio
El repositorio **actualmente es público**. No almacenar RUT, nombres, direcciones, cuentas bancarias, teléfonos, correos de trabajadores o empleadores, ni subir el Excel operativo sin anonimizar. La versión maestra se conserva fuera de este repositorio mientras no exista un almacenamiento privado autorizado.

## Rutas de consulta
- [Documentos disponibles](02_DOCUMENTOS_GENERABLES.md)
- [Qué dato alimenta cada documento](03_CAMPOS_Y_SALIDAS.md)
- [Contenido PTS pendiente](04_PTS_PENDIENTES.md)
- [Reglas de evolución y pruebas](05_CONTROL_CAMBIOS.md)
