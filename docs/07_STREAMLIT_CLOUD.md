# PROYECTO ALCANTO — Streamlit Community Cloud

Sistema web para gestión de empresas y trabajadores de subcontrato y prevención. Usa las **17 hojas y fórmulas originales** de la plantilla Excel como fuente, sin requerir Microsoft Excel ni Windows en el computador del usuario.

> **Estado actual**: aplicación web preparada y pruebas de manipulación XLSX realizadas. La conversión definitiva y la identidad visual **aún no están certificadas en Aspose.Cells Cloud**, porque se requieren credenciales y pruebas con PDF de referencia. Una prueba con LibreOffice generó `#NAME?` al evaluar una fórmula LET/LAMBDA/TEXTSPLIT del sueldo, por lo que LibreOffice NO se utiliza como motor de producción.

## Despliegue

1. Entrar a [Streamlit Community Cloud](https://share.streamlit.io/) con GitHub.
2. **Create app** → repositorio `Alvarofritzsolis1/PROYECTO-ALCANTO`, rama `main`, archivo `app.py` (raíz).
3. Python 3.12 en Advanced settings (compatible con dependencias).
4. En **Secrets** agregar (no al repositorio):

```toml
ALCANTO_APP_PASSWORD = "CONTRASENA-LARGA-ALEATORIA-DE-MAS-DE-16-CARACTERES"
ASPOSE_CLIENT_ID = "CLIENT_ID_REAL"
ASPOSE_CLIENT_SECRET = "CLIENT_SECRET_REAL"
```

5. Si quieres guardar plantilla/empresas/trabajadores para próximas sesiones, configura además un **bucket S3 PRIVADO** (Amazon S3 o Cloudflare R2) y añade:

```toml
[storage]
bucket = "alcanto-privado"
endpoint_url = "https://TU_CUENTA.r2.cloudflarestorage.com" # Quitar en AWS S3
region = "auto"  # para AWS, usar region real del bucket
access_key_id = "TU_ACCESS_KEY"
secret_access_key = "TU_SECRET_KEY"
```

**Importante:** no hacer público el bucket. Los RUT y otros datos personales deben tener controles de acceso, conservación y eliminación conforme a las normas aplicables.

6. Desplegar y abrir el enlace suministrado por Streamlit. Entrar con la contraseña.
7. Subir la plantilla XLSX original **solo desde el panel protegido**. No subirla a GitHub público.
8. Completar una empresa, luego sus trabajadores. En Documentación seleccionar y generar PDFs.

Si no configuras `[storage]`, la app permite pruebas **solo durante la sesión** y requerirá volver a cargar plantilla y datos cuando el servidor se reinicie. No llamar a este modo una base histórica persistente.

## Motor de conversión

El programa usa el API oficial `PUT https://api.aspose.cloud/v4.0/cells/convert/worksheet/pdf` (Aspose.Cells Cloud). El libro completo se envía por HTTPS en una **copia temporal**: existe un coste y tratamiento de datos por un proveedor externo que debe ser autorizado. La librería local ZIP/XML modifica exclusivamente entradas en `xl/worksheets/sheet1.xml`, sin borrar fórmulas o tocar el maestro. El motor contratado recalcula e imprime cada hoja.

Documentos contemplados: contrato, traslado, prórroga, inducción, IRL, PTS, entrega PTS, EPP, recepción de reglamento y declaración. **Los 23 contenidos PTS faltantes no se inventan ni completan automáticamente.**

## Garantías y límites

- No se guarda ningún PDF en GitHub: solo se ofrece descarga privada en la sesión.
- La aplicación bloquea errores de fórmula visibles como `#NAME?` y `#REF!` en PDF, cuando puede extraer el texto. No sustituye una verificación visual y documental.
- Las casillas C33 (sueldo en palabras), C36 (HOY), C37 (término) y C40 (fecha firma) **son fórmulas y nunca se editan**.
- La prórroga puede requerir revisar su fecha configurada en la propia plantilla original. La primera versión online no modifica esa celda.
- La plantilla puede contener información personal antigua en valores en caché y celdas estáticas: antes de procesar en servicios externos, revisar los permisos y consentimiento de uso.
- No se garantiza la identidad de PDF de un motor diferente a Excel hasta realizar pruebas reales de los 10 documentos.
- La sesión de Streamlit con contraseña compartida es una protección básica; para operación multiusuario real hacen falta usuarios individuales, trazabilidad, políticas de retención y auditoría.

## Verificación local sin credenciales ni datos reales

```bash
python -m unittest discover -s tests -v
```

Prueba opcional estructural con el libro verdadero, que **no se sube a GitHub**:

```bash
ALCANTO_TEST_WORKBOOK="/ruta/privada/PROYECTO AUTOMATIZACION GESTION CONTRATISTAS FINAL.xlsx" python -m unittest discover -s tests -v
```

## Referencias

- [Deploy en Streamlit](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Dependencias de Streamlit](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)
- [API conversión de hoja a PDF (Aspose.Cells Cloud)](https://docs.aspose.cloud/cells/cells/convert/worksheet/pdf/)
