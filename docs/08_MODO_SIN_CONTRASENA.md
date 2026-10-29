# ALCANTO — Acceso libre sin contraseña

A partir del cambio de 29-10-2026 la aplicación Streamlit abre **sin solicitar contraseña**: no requiere `ALCANTO_APP_PASSWORD` ni tiene pantalla de inicio de sesión.

## Protección de datos en la versión abierta

Los datos del proyecto incluyen nombres, RUT y antecedentes de contratos. Una página sin autenticación no puede mantener un único historial compartido de trabajadores sin el riesgo de mostrarlo a otros visitantes.

Por ello la aplicación opera con **sesiones temporales independientes**:
- Los formularios de empresas y trabajadores se guardan solo en la memoria de la sesión activa.
- La plantilla XLSX subida por una persona se mantiene únicamente en esa sesión y no se guarda en GitHub.
- No se utilizan credenciales ni un bucket S3 compartido aunque estén configurados.
- El usuario puede borrar sus datos temporales desde la barra lateral.
- Una recarga, cierre del navegador o reinicio del servidor pueden hacer perder el contenido. **No es una base de datos persistente.**
- Los documentos descargados pueden contener información personal: guardarlos en un lugar seguro.

## Lo que requiere una configuración aparte

Para PDF online se necesitan credenciales del motor de conversión Aspose.Cells Cloud en los **Secrets de Streamlit**. Estas credenciales son del servicio de conversión, **no son una contraseña de acceso a la aplicación**.

La conversión envía al proveedor externo una copia temporal del libro Excel para calcular sus fórmulas y crear los PDFs; el usuario debe autorizar ese tratamiento y verificar el resultado antes de firmar o usar documentos.

## Si en el futuro se necesitan historiales online permanentes

La recomendación es implementar una identificación individual **sin contraseña de la aplicación**, como inicio de sesión con Google/Microsoft mediante OAuth y permisos por empresa, con almacenamiento cifrado y políticas de retención. Nunca activar acceso anónimo a una base compartida con RUT y antecedentes laborales.

## Si aparece todavía la pantalla de contraseña
El despliegue puede estar mostrando una versión anterior. Verificar que Streamlit use `main` / `app.py`, actualizar el despliegue desde el último commit y reiniciarlo desde **Manage app → Reboot app**. La variable antigua `ALCANTO_APP_PASSWORD` puede borrarse de Secrets; el nuevo código no la consulta.
