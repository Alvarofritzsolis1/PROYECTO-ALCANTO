# ALCANTO — Auditoría funcional, 15 casos por documento

**Fecha:** 29 de octubre de 2026 (Chile).  
**Repositorio:** `Alvarofritzsolis1/PROYECTO-ALCANTO`.  
**Pruebas de plataforma:** `tests/test_150_documentos.py`, ejecutadas con GitHub Actions.  
**Integridad de la plantilla:** 10 copias de prueba locales a partir del XLSX original, sin publicación de datos personales.

## Resultados comprobados

| Documento | Pruebas funcionales de prevalidación | Copia XLSX sin alterar fórmulas | PDF real en Aspose |
|---|---:|---|---|
| Contrato Imprimible | 15/15 | Conforme | Pendiente |
| Anexo Traslado | 15/15 | Conforme | Pendiente |
| Anexo extension contrato | 15/15 | Conforme | Pendiente |
| INDUCCION PREVENCION | 15/15 | Conforme | Pendiente |
| IRL | 15/15 | Conforme | Pendiente |
| PTS. | 15/15 | Conforme | Pendiente |
| ENTREGA PTS | 15/15 | Conforme | Pendiente |
| Registros Entrega EPP | 15/15 | Conforme | Pendiente |
| REGLAMENTO INTERNO | 15/15 | Conforme | Pendiente |
| DECLARACION JURADA | 15/15 | Conforme | Pendiente |
| **TOTAL** | **150/150** | **10/10** | **0/10 validados** |

Las 150 pruebas son **unitarias de disponibilidad documental, combinación de datos, validación y controles de errores**. NO significan 150 PDFs impresos o verificados visualmente. La integración de cada hoja con un PDF real exige el servicio Aspose.Cells Cloud y sus credenciales.

### Los 15 casos por documento

1. Todos los datos necesarios presentes, documento habilitado.
2. Datos completamente ausentes, documento bloqueado.
3. Solo empresa registrada, sin trabajador.
4. Falta el primer campo requerido.
5. Falta el último campo requerido.
6. Campo obligatorio con espacios en blanco.
7. Empresa con caracteres acentuados y ñ.
8. Domicilio largo dentro de los límites.
9. Obra «Brisas de Junquillar».
10. Obra «Concepción».
11. Forzar contexto sin trabajador: documentos personales bloqueados.
12. Cargo inexistente en matrices: contrato, IRL y PTS protegidos.
13. Declaración jurada sin confirmación de veracidad: bloqueada.
14. Dos trabajadores diferentes: no mezclar nombres, RUT ni nacionalidades.
15. Archivo PDF no válido: rechazado.

Estas 15 pruebas se repiten para las diez hojas. GitHub también ejecuta pruebas adicionales existentes de sintaxis, catálogo y reglas de funcionamiento.

## Mejoras aplicadas

- **Documentación por empresa sin registrar trabajador.** Se puede mostrar la inducción de empresa, un PTS por cargo y la declaración jurada según antecedentes y verificaciones pertinentes.
- **Obra registrada en ficha de empresa.** Se hereda automáticamente a documentos de trabajador, salvo que éste tenga otra obra seleccionada.
- **No repetir información:** al elegir trabajador se reutilizan los antecedentes de su empresa.
- **PTS por cargo** con bloqueo para los 23 registros técnicos aún incompletos.
- **Declaración jurada** requiere nacionalidad del firmante por separado y confirmación explícita de veracidad. El documento afirma inexistencia de trabajadores dependientes; no se emite automáticamente.
- **Cargos fuera de matriz** bloqueados en contrato e IRL para evitar descripciones y riesgos «No encontrado».
- **Estado de confirmación y selección de PDF aislado por empresa/trabajador.**
- No se eliminó ninguna hoja, fórmula ni contenido original.

## Prueba de la interfaz Streamlit

La suite `tests/test_ui_empresa_sin_trabajador.py` simula una sesión real de Streamlit:

- Registrar empresa y obra con datos ficticios, sin trabajador.
- Comprobar que existe la vista **«Solo documentos de empresa»**.
- Seleccionar el PTS corporativo de **PINTOR**.
- Confirmar expresamente las condiciones de la declaración jurada.
- Comprobar que se habilitan las **tres hojas corporativas** cuando están todos los datos mínimos.
- Confirmar que no existe un cargador de Excel visible para el usuario.

**Resultado:** dos pruebas de interfaz aprobadas por GitHub Actions, además de los 150 casos documentales y las verificaciones previas. [Ver CI](../../actions).

## Comprobación estructural con el libro original

Archivo original: 17 hojas, 310 fórmulas (inventario previo); SHA-256:
`b24a43377506a85afd1f4dbe5c78f24b15dbdb6dc7e51ac1fdad842784e1e034`.

Se ejecutaron 10 comprobaciones de copias XLSX con datos ficticios, una por hoja de salida. En cada una se verificó:

- El archivo original conserva su SHA-256.
- Las fórmulas de `Datos Contrato` son iguales a las originales.
- Todas las otras partes del XLSX permanecen idénticas a las originales; únicamente se modifica la copia del XML de entradas y el indicador de recálculo.
- Los datos de empresa y trabajador de la ficha se reflejan sin cruzarse.
- El código de obra seleccionado coincide con el solicitado.

**Aclaración:** esta comprobación demuestra preservación de estructura y fórmulas, **no recálculo de todas las fórmulas ni coincidencia visual del PDF de cada hoja**.

## Observaciones y límites identificados

1. **Bloqueo externo pendiente:** el servidor Streamlit no tiene todavía provisionada la plantilla XLSX privada y/o las credenciales de Aspose.Cells Cloud. La descarga PDF no será operativa hasta configurarlos.
2. **Cálculo avanzado:** se observaron funciones como `FILTER`, `LET/LAMBDA`, `TEXTSPLIT` y `_xlfn._LONGTEXT` que requieren comprobar equivalencia en Aspose. LibreOffice no reprodujo algunas en una prueba anterior.
3. **PTS incompletos:** 23 de 26 registros de `MATRIZ PTS` requieren aún sus secciones técnicas.
4. **Fechas dinámicas:** las fórmulas `HOY()` y derivadas se actualizan con el recálculo. El programa no las sustituye.
5. **Declaración jurada:** contiene afirmaciones que solo puede validar el representante. Debe revisarse su veracidad y contexto normativo.
6. **Datos personales:** la versión sin contraseña utiliza sesiones temporales separadas y no expone historiales comunes. No colocar el libro original en GitHub público.
7. **Prueba de ejecución final no realizada:** no existe un comprobante de 10 PDFs generados por Aspose con cotejo visual. Debe realizarse antes de afirmar «100 % operativo».

## Evidencia

- [Suite de 150 pruebas](../tests/test_150_documentos.py).
- [Flujo documental empresa/trabajador](../alcanto_cloud/documentos.py).
- [Acciones de CI](../../actions).
