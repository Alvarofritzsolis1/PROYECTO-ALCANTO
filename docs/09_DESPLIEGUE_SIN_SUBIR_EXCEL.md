# ALCANTO — Formularios web sin subir Excel

## Qué significa este cambio

A partir de la versión nueva, **los visitantes jamás deben seleccionar o subir un archivo XLSX**. La pantalla abre directamente la ficha de empresa y trabajador; una vez registrados, muestra los documentos disponibles y permite generar los PDF para revisar e imprimir.

El archivo Excel original sigue siendo la plantilla del proyecto **dentro del servidor**, reutilizando las 17 hojas y las fórmulas existentes. El usuario no ve el archivo, ni lo modifica.

```text
Streamlit web
    |
    +-- Formulario: empresa + representante
    +-- Formulario: trabajador + cargo + obra + condiciones
    |
    v
Modelo ALCANTO instalado una vez en almacenamiento privado
    |
    v
Crear copia temporal XLSX con los valores de formularios
    |
    v
Aspose.Cells Cloud recalcula y exporta la hoja seleccionada
    |
    v
PDF imprimible, para revisión humana
```

## Única configuración interna para un administrador

El repositorio GitHub es **público**, por eso **NUNCA** debe subirse allí el Excel con nombres, RUT, domicilios o valores guardados. Además no se debe convertir la plantilla en una URL pública. El archivo se instala solo una vez **fuera de la interfaz**.

El servidor tiene dos alternativas:

**A. Recomendada: almacenamiento de objetos S3 privado**, por ejemplo AWS S3 o Cloudflare R2, con un objeto en la clave fija `alcanto/plantilla_maestra.xlsx`. Se necesita un bucket privado y credenciales de lectura para el servidor Streamlit. La aplicación solo lee la plantilla; no permite subirla desde el navegador ni leer los registros de otras personas.

**B. Despliegue controlado y privado:** preinstalar `plantillas/ALCANTO_MODELO.xlsx` en el contenedor **antes del arranque**. Como Streamlit Community Cloud reconstruye desde GitHub, esta opción solo sirve si existe un procedimiento seguro de empaquetado del modelo sin publicar sus datos. Para un repositorio público, usar A.

Para S3, el administrador puede verificar el Excel original (sin alterarlo) y cargar una copia con los campos de entrada vacíos mediante el script:

```bash
export AWS_ACCESS_KEY_ID="..."              # Configuración privada del administrador
export AWS_SECRET_ACCESS_KEY="..."
export ALCANTO_S3_BUCKET="bucket-privado"
export ALCANTO_S3_REGION="auto"              # AWS: región real
export ALCANTO_S3_ENDPOINT_URL="https://..." # Solo R2; omitir en AWS

python scripts/provisionar_plantilla_privada.py "/ruta/privada/PROYECTO AUTOMATIZACION GESTION CONTRATISTAS FINAL.xlsx"
# Comprueba 17 hojas y las fórmulas. NO sube nada.
# Tras revisar política de privacidad y permisos del bucket:
python scripts/provisionar_plantilla_privada.py "/ruta/privada/PROYECTO AUTOMATIZACION GESTION CONTRATISTAS FINAL.xlsx" --confirmar-upload
```

**Atención:** los cachés y metadatos del libro original podrían mantener información anterior incluso después de limpiar los campos de entrada. Almacenar la plantilla exclusivamente en el bucket privado autorizado y verificar el resultado de los PDFs.

Luego configurar los secretos en **Streamlit Community Cloud > Manage app > Settings > Secrets**:

```toml
[storage]
bucket = "bucket-privado"
region = "auto"
endpoint_url = "https://CUENTA.r2.cloudflarestorage.com"
access_key_id = "SOLO-EN-STREAMLIT-SECRETS"
secret_access_key = "SOLO-EN-STREAMLIT-SECRETS"

ASPOSE_CLIENT_ID = "SOLO-EN-STREAMLIT-SECRETS"
ASPOSE_CLIENT_SECRET = "SOLO-EN-STREAMLIT-SECRETS"
```

En AWS S3, omite `endpoint_url` y usa la región real. El bucket **nunca debe ser público**. Las claves no se agregan a GitHub ni se muestran a usuarios.

## Qué ve el usuario

1. **Empresas**: ingresa RUT, razón social, representante y demás antecedentes.
2. **Trabajadores**: elige la empresa, completa nombre, RUT, cargo, obra, remuneración, AFP, salud, etc.
3. **Documentos**: ve qué registros cumplen campos mínimos, selecciona contrato, IRL, PTS, anexos, EPP, inducción y otros documentos.
4. **Descarga PDF**: el servidor usa el Excel interno con los datos ingresados, recalcula sus fórmulas mediante el motor cloud, y devuelve los documentos para revisión.

**No** necesita Microsoft Excel instalado, ni subir archivos.

## Seguridad en un sitio sin contraseña

El acceso a la página es público, pero **los datos de empresas y trabajadores son temporales por sesión**. Un visitante no puede consultar los registros de otro. La aplicación no lee el catálogo de registros S3 compartidos aunque exista la configuración `[storage]`: ese almacenamiento se utiliza **solo para la plantilla maestra**.

Si se desea un historial multiusuario persistente, hace falta una autenticación individual como Google/Microsoft y permisos por empresa. No activar un historial compartido de RUT sin identidad de usuario.

## Estado de validación

- **Completado en código:** no hay un cargador de Excel en la interfaz; se exige una plantilla interna instalada y se conserva la lógica de fórmulas.
- **Probado en copia del libro original:** 17 hojas; fórmulas originales conservadas al sustituir campos de entrada.
- **Pendiente de aprovisionar en Streamlit:** el modelo maestro privado debe instalarse una sola vez. No está en el repositorio público.
- **Pendiente de validar:** motor Aspose con credenciales reales y revisión visual de los diez tipos de PDF. No afirmar fidelidad 100% antes de estas pruebas.

Para problemas de despliegue, revisar `docs/07_STREAMLIT_CLOUD.md`.
