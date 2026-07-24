# FUT-UNDAC Web

Versión web del asistente FUT-UNDAC. Reutiliza toda la lógica del
proyecto original (`core/`: catálogo de trámites, construcción del
FUT y generación del Word) detrás de un formulario en el navegador,
hecho con Flask. Genera el documento en **Word (.docx)**.

## Estructura

```
app.py              servidor Flask (rutas y lógica web)
core/                lógica de negocio (sin cambios respecto al proyecto original)
data/                logo, marca de agua, config de campos
templates/           páginas HTML
static/              CSS + logo
requirements.txt
Procfile             comando de arranque para Render
render.yaml          configuración opcional para "Blueprints" de Render
```

## Ejecutar en local

```bash
pip install -r requirements.txt
python app.py
```

Abre `http://localhost:5000`.

## Desplegar en Render

### Opción A — con render.yaml (recomendada)

1. Sube esta carpeta a un repositorio de GitHub/GitLab.
2. En Render: **New +** → **Blueprint** → conecta el repo. Render leerá
   `render.yaml` y creará el servicio automáticamente.
3. Cuando te lo pida, ingresa `AWS_ACCESS_KEY_ID` y
   `AWS_SECRET_ACCESS_KEY` (ver sección de IA abajo). Si no vas a usar
   la IA, puedes dejarlos vacíos: el sitio funciona igual, solo se
   oculta el botón "Redactar con IA".

### Opción B — manual

1. Sube la carpeta a un repositorio.
2. En Render: **New +** → **Web Service** → conecta el repo.
3. Configura:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
4. En **Environment**, agrega las variables:
   - `SECRET_KEY` → cualquier texto aleatorio
   - `AWS_ACCESS_KEY_ID` (opcional, para la IA)
   - `AWS_SECRET_ACCESS_KEY` (opcional, para la IA)
   - `AWS_DEFAULT_REGION` → `us-east-1`
5. Deploy.

## Redacción con IA (AWS Bedrock)

El botón "Redactar con IA" en el formulario usa Claude en AWS Bedrock
(`core/ia_aws.py`) para generar la fundamentación legal a partir de lo
que el estudiante escriba en lenguaje natural. Para que funcione en
Render:

1. En tu cuenta de AWS, activa el acceso al modelo Claude Sonnet en
   **Bedrock → Model access**, región `us-east-1`.
2. Crea un usuario IAM con permisos de `bedrock:InvokeModel` y copia su
   Access Key / Secret Key.
3. Configura esas dos claves como variables de entorno en Render
   (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).

Si las variables no están configuradas, o boto3 no puede conectarse,
el botón de IA simplemente no aparece / muestra un mensaje de error —
el resto del sitio (elegir trámite, llenar datos, generar el Word)
sigue funcionando sin ella.

## Notas

- Solo se genera **Word (.docx)**. La conversión a PDF del proyecto
  original depende de LibreOffice, que no está instalado en Render por
  defecto — si más adelante lo necesitas, se puede agregar con un
  `Aptfile` / Docker, pero complica el despliegue.
- Los documentos generados se sirven directamente en la respuesta y se
  borran del disco del servidor al instante (Render usa disco efímero,
  así que de todas formas no conviene depender de guardarlos ahí).
- La API institucional de UNDAC (autocompletar por código) y las
  funciones de perfil/plantilla local del proyecto original siguen
  disponibles en `core/`, por si luego quieres exponerlas también en
  la web.
