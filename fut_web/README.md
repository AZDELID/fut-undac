# FUT-UNDAC — versión web (para Render)

Esta es la adaptación web de la app de escritorio (`gui.py`, Tkinter) a
Flask, con la misma interfaz (sidebar oscuro, tarjetas de trámites,
paleta de colores, flujo de 4 pasos) para poder publicarla en Render y
que cualquier estudiante la use desde el navegador, sin instalar nada.

El motor de generación de documentos (`core/catalogo.py`,
`generar_docx_py.py`, `constructor.py`, etc.) es el mismo que usaba la
app de escritorio — no se reescribió, solo se le puso una interfaz web
encima.

## Flujo

1. **Inicio** — catálogo de trámites con buscador (`/`)
2. **Datos personales** — formulario + autocompletar con la API de UNDAC
3. **Fundamentación** — sugerencia editable
4. **Vista previa** — resumen + elección de formato
5. **Resultado** — descarga de Word y/o PDF

## Desplegar en Vercel

El error `FUNCTION_INVOCATION_FAILED` que viste antes pasaba porque el
código intentaba escribir archivos dentro de la carpeta del proyecto,
y en Vercel esa carpeta es de **solo lectura** (solo `/tmp` es
escribible). Ya está corregido: todos los archivos temporales y el
"perfil recordado" ahora se guardan en `/tmp`, y cada documento se
genera y se descarga **en la misma petición** (no se guarda para
servirlo después), porque en serverless cada request puede caer en una
instancia distinta.

Pasos:

1. Sube esta carpeta (`fut_web`) a un repositorio de GitHub.
2. En Vercel: **Add New... → Project**, importa el repo. Vercel detecta
   `vercel.json` automáticamente (ya incluido).
3. En **Settings → Environment Variables**, agrega `SECRET_KEY` con una
   cadena larga aleatoria (importante: sin esto, el formulario de 4
   pasos puede "perder" los datos a mitad de camino si el usuario cae
   en una instancia distinta entre paso y paso).
4. Deploy.

**Limitación en Vercel:** no hay LibreOffice disponible, así que la
opción de **PDF no funcionará** ahí (se genera el Word igual; si el
usuario pide PDF o "ambos", verá un aviso). Si necesitas PDF también,
usa Render con el `Dockerfile` incluido (ver abajo) — Vercel no soporta
instalar paquetes de sistema como LibreOffice.

## Desplegar en Render (opción recomendada — solo Word)

1. Sube esta carpeta a un repositorio de GitHub.
2. En Render: **New + → Web Service**, conecta el repo.
3. Render detecta `render.yaml` automáticamente (Blueprint), o configúralo
   a mano:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Deploy. Ya tienes la app pública generando `.docx`.

> Con este método **el PDF no está disponible** (Render no trae
> LibreOffice instalado). La descarga en Word siempre funciona.

## Desplegar con PDF incluido (Docker)

Este repo también trae un `Dockerfile` que instala LibreOffice para
poder convertir a PDF:

1. En Render: **New + → Web Service → Docker** (en vez de Python nativo),
   apuntando al mismo repo (Render detecta el `Dockerfile`).
2. No hace falta build/start command: ya están en el `Dockerfile`.
3. El primer build tarda más (~5-8 min) porque instala LibreOffice.

## Variables de entorno

- `SECRET_KEY` — clave para firmar la sesión de Flask. En el deploy con
  `render.yaml` se genera sola. Si configuras el servicio a mano, agrega
  una variable de entorno `SECRET_KEY` con cualquier cadena larga
  aleatoria.

## Notas importantes

- Los datos del formulario viven en la **sesión del navegador** (cookie
  firmada), no en una base de datos — cada visitante tiene su propio
  flujo aislado.
- Los documentos generados se guardan temporalmente en `output/<token>/`
  dentro del contenedor y se sirven para descarga inmediata. En el plan
  gratuito de Render el disco es efímero: no uses esto como
  almacenamiento permanente de archivos generados.
- `core/perfil.py` guarda un "perfil recordado" en el disco del
  contenedor (`~/.fut_undac/perfiles/`). En el plan free ese disco se
  reinicia con cada deploy/reinicio — es solo una comodidad, no persistencia
  real. Si más adelante quieres perfiles persistentes de verdad, se puede
  cambiar a una base de datos (Render Postgres free tier, por ejemplo).
- El módulo `core/ia_aws.py` (IA vía AWS Bedrock) de la app de escritorio
  **no se incluyó** en esta versión web para mantener el deploy simple y
  sin credenciales de AWS. Se puede volver a conectar más adelante si
  quieres esa función también en la web.
- La integración con la API de UNDAC (`core/api_undac.py`) se mantiene
  igual; si esa API solo responde desde la red institucional, el botón
  "Consultar API" fallará cuando Render (fuera del campus) intente
  llamarla — en ese caso el estudiante simplemente llena los datos a mano.

## Correr en local antes de desplegar

```bash
cd fut_web
pip install -r requirements.txt
python app.py
# abre http://localhost:5000
```
