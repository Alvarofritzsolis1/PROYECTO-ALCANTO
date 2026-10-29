# Matriz de datos: ¿qué documento se completa al rellenar cada campo?

## Cómo leer esta guía
La **hoja de origen** es `Datos Contrato`. Las referencias de salida se determinaron leyendo las fórmulas de la versión original. Esta tabla describe **uso directo en fórmulas**, no asegura por sí sola que el contenido esté validado o listo para firmar.

**Abreviaturas:** CONTRATO = Contrato Imprimible; TRASLADO = Anexo Traslado; PRÓRROGA = Anexo extension contrato; INDUCCIÓN = INDUCCION PREVENCION; IRL = IRL; PTS = PTS.; ENTREGA PTS = ENTREGA PTS; EPP = Registros Entrega EPP; REGLAMENTO = REGLAMENTO INTERNO; JURADA = DECLARACION JURADA.

## 1. Empresa y representante

| Celda | Qué rellenar | Documentos que usan el dato |
|---|---|---|
| **C5** | Identificación/nombre empleador según el formulario | CONTRATO, TRASLADO, PRÓRROGA, INDUCCIÓN, IRL, PTS, ENTREGA PTS, EPP, REGLAMENTO, JURADA |
| **C6** | RUT empleador | CONTRATO, TRASLADO, PRÓRROGA, INDUCCIÓN, IRL, PTS, ENTREGA PTS, EPP, REGLAMENTO, JURADA |
| **C7** | Representante legal | CONTRATO, PRÓRROGA, INDUCCIÓN, PTS, JURADA |
| **C8** | RUT representante | CONTRATO, PRÓRROGA, INDUCCIÓN, PTS, JURADA |
| **C9** | Teléfono empresa | INDUCCIÓN |
| **C10** | Domicilio empresa | CONTRATO, PRÓRROGA, INDUCCIÓN, PTS, JURADA |
| **C11** | Comuna empresa | CONTRATO, PRÓRROGA |
| **C12** | Ciudad empresa | CONTRATO, ENTREGA PTS, REGLAMENTO, JURADA |
| **C13** | Correo empresa | CONTRATO, INDUCCIÓN |
| **C14** | Rubro empresa | INDUCCIÓN, ENTREGA PTS, JURADA |

**Ejemplo:** al rellenar `C5` y `C6`, el nombre y el RUT del empleador alimentan las **10 hojas de documentos**. Eso no significa que los diez documentos estén terminados: también requieren antecedentes del trabajador u otras condiciones.

## 2. Trabajador

| Celda | Qué rellenar | Documentos que usan el dato |
|---|---|---|
| **C17** | Nombre trabajador | CONTRATO, TRASLADO, PRÓRROGA, IRL, ENTREGA PTS, EPP, REGLAMENTO |
| **C18** | RUT trabajador | CONTRATO, TRASLADO, PRÓRROGA, IRL, ENTREGA PTS, EPP, REGLAMENTO |
| **C19** | Nacionalidad | CONTRATO, ENTREGA PTS, JURADA |
| **C20** | Fecha nacimiento | CONTRATO |
| **C21** | Estado civil | CONTRATO, ENTREGA PTS |
| **C22** | Domicilio trabajador | CONTRATO |
| **C23** | Comuna trabajador | CONTRATO |
| **C24** | Ciudad de procedencia | CONTRATO |
| **C25** | Correo trabajador | CONTRATO |
| **C26** | Teléfono trabajador | CONTRATO |

**Atención:** «aparece como referencia en la fórmula» no garantiza que el campo se esté usando con el significado deseado. Si se decide corregir alguna referencia, hacerlo **solo en una copia con pruebas**.

## 3. Contrato, cargo y obra

| Celda | Qué rellenar | Documentos que usan el dato |
|---|---|---|
| **C29** | Cargo/especialidad | CONTRATO, TRASLADO, IRL, PTS, EPP |
| **D30** | Selección de obra/faena | TRASLADO, INDUCCIÓN, IRL, EPP, JURADA |
| **C30** | Nombre de la obra obtenido mediante búsqueda desde D30 | CONTRATO, TRASLADO, INDUCCIÓN, JURADA |
| **C31** | Jornada semanal | CONTRATO |
| **C32** | Sueldo base | CONTRATO; también alimenta C33 |
| **C33** | Sueldo en palabras (fórmula automática) | CONTRATO |
| **C34** | Frecuencia de pago | CONTRATO |
| **C35** | Cuenta bancaria/detalle de pago | CONTRATO |
| **C36** | Fecha de ingreso (fórmula `HOY` en el archivo recibido) | CONTRATO, PRÓRROGA |
| **C37** | Fecha término inicial (fórmula dependiente de C36) | CONTRATO, PRÓRROGA |
| **C38** | AFP | CONTRATO |
| **C39** | Régimen de salud | CONTRATO |
| **C40** | Fecha firma (deriva de C36) | CONTRATO |
| **C43** | Obras/destinos autorizados | TRASLADO |
| **C44** | Asignación de locomoción | TRASLADO |
| **Anexo extension contrato!M4** | Fecha nueva de término | PRÓRROGA |

La selección de faena en `D30` alimenta `C30` mediante la tabla auxiliar `T15:U18` de `Datos Contrato`.

## 4. Reglas de disponibilidad documental

| Si ya ingresaste… | Puedes revisar las siguientes salidas |
|---|---|
| Empresa y representante | Encabezados/identificaciones de inducción, PTS y documentos laborales |
| Empresa + trabajador | Identificación en contrato, anexos, IRL, EPP y constancias |
| + cargo correcto | Descripción contractual, riesgos IRL y plantilla PTS asociada al cargo |
| + obra | Contrato, traslado, inducción, IRL y EPP contextualizados con la faena |
| + sueldo, jornada, previsión y fechas | Contrato laboral con información contractual |
| + destinos autorizados y locomoción | Anexo de traslado |
| + fecha nueva en el anexo | Prórroga para revisión |
| + contenido técnico completo del cargo en MATRIZ PTS | PTS desarrollados, no solo la plantilla |
| + constatación real de entrega/capacitación y firma | Registros de entrega de EPP, PTS e inducción respaldados por la actividad real |

## 5. Qué se puede automatizar después (no implementado aún)
Crear un panel que indique, en tiempo real, si cada salida está **incompleta**, **generable / pendiente de revisión**, **PTS sin contenido técnico**, o **validada**, y que permita exportar los PDFs preservando exactamente la presentación actual. Debe probarse primero en una copia del Excel.
