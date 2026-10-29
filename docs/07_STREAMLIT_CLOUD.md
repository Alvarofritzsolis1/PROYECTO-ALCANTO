# PROYECTO ALCANTO — Despliegue en Streamlit Community Cloud (sin contraseña)

La aplicación se abre directamente desde el navegador **sin contraseña de acceso**. El código principal es el archivo `app.py` en la raíz del repositorio.

## Pasos para actualizar o desplegar

1. Abrir [Streamlit Community Cloud](https://share.streamlit.io/) con la cuenta de GitHub que administra el proyecto.
2. Elegir el repositorio `Alvarofritzsolis1/PROYECTO-ALCANTO`, rama `main` y archivo `app.py`.
3. Si ya está desplegado, esperar a que Streamlit instale el cambio de GitHub y recargar la página. Si todavía muestra el aviso antiguo, reiniciar la aplicación desde **Manage app → Reboot app**.
4. **No hay que configurar `ALCANTO_APP_PASSWORD`**. Si existe esa variable en Secrets, la aplicación la ignora.
5. Para generar PDFs online, registrar únicamente las credenciales de Aspose.Cells Cloud en **Advanced settings → Secrets**:

```toml
ASPOSE_CLIENT_ID = "TU_CLIENT_ID"
ASPOSE_CLIENT_SECRET = "TU_CLIENT_SECRET"
```

6. Subir el XLSX desde la interfaz cuando sea necesario, completar empresa y trabajadores y generar los documentos disponibles.

## Privacidad del modo sin contraseña

- La página puede abrirla cualquier persona con su enlace. Nunca incluir RUT, nombres ni datos reales en el repositorio público.
- **No se emplea la base S3 compartida** en esta modalidad; cada visitante tiene registros y plantilla independientes, únicamente durante su sesión de Streamlit.
- Los registros **no se conservan permanentemente**: pueden perderse cuando se cierra la sesión, el servidor se reinicia o se borra la sesión desde la barra lateral.
- Si se desea conservar historiales permanentes **sin introducir contraseña**, debe implementarse otra identificación de usuarios (por ejemplo, acceso con identidad mediante un proveedor OAuth). No activar almacenamiento compartido anónimo con información privada de trabajadores.
- La plantilla original nunca se modifica. El programa prepara una copia en memoria y no altera las fórmulas existentes.
- El procesamiento externo por Aspose.Cells Cloud envía una copia del XLSX a un proveedor; debe aceptarse expresamente antes de generar los PDF. Puede tener coste por uso.

## Estado de la exportación

El acceso sin contraseña queda implementado en código. La producción de PDF está preparada, pero **la equivalencia con Microsoft Excel no está certificada** sin configurar el proveedor cloud, generar PDFs de muestra y compararlos visualmente. Una prueba de LibreOffice evidenció diferencias al evaluar una fórmula avanzada, por lo que no se utiliza ese motor como solución final.

Documentos previstos: contrato, traslado, prórroga, inducción, IRL, PTS, entrega PTS, EPP, reglamento y declaración. Las 23 entradas PTS que faltan siguen pendientes de completar.

## Comprobaciones locales (sin datos privados)

```bash
python -m unittest discover -s tests -v
```

## Enlaces
- [Documentación oficial de despliegue Streamlit](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Privacidad en el modo sin contraseña](08_MODO_SIN_CONTRASENA.md)
