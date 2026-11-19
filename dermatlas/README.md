# Entrega actual: atlas de tipos de psoriasis

La versión actual permite importar fotos locales y también registrar enlaces externos. Al iniciar crea cinco fichas: psoriasis en placas, guttata, inversa, eritrodérmica y pustular. Las tarjetas generales de Psoriasis, Eccema y Dermatitis seborreica están ocultas en Inicio y Atlas, sin borrar registros. Cada galería permite ampliar sus imágenes; también hay comparador y administración.

## Qué contiene esta entrega para GitHub

Código fuente, pruebas, documentación y `frontend/pnpm-lock.yaml`. No incluye las 11 fotografías aportadas por la usuaria, la base de datos de trabajo, respaldos, capturas de pantalla, credenciales ni dependencias instaladas. En otro computador las galerías empezarán vacías: las fotos deben importarse por separado con su fuente y permiso. La carpeta local `data/` queda excluida de Git.

## Inicio rápido

Requisitos: Python 3.10+ y Node.js 22+. Desde la carpeta del proyecto:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cd frontend
npm install
npm run build
cd ..
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Abre `http://127.0.0.1:8000`. En Windows activa el entorno con `.venv\Scripts\Activate.ps1`. VS Code es opcional: los comandos también pueden ejecutarse desde Codex o una terminal.

Administración → «Agregar fotos desde tu carpeta»: selecciona varias fotos del mismo tipo, elige su diagnóstico y registra fuente, permiso y revisión de privacidad. Se conservan los originales y se guardan copias JPEG sin EXIF. La eliminación de EXIF no elimina datos identificatorios visibles. Los enlaces externos se agregan en el formulario siguiente.

Pruebas: `python -m pytest -q` desde la raíz. Compilación: `npm run build` dentro de `frontend`. Las cuatro pruebas HTTP y la compilación pasaron en esta entrega; la última ocultación de tarjetas se verificó por compilación, sin revisión visual posterior.

Las fichas médicas están pendientes de completar y validar. No hay clasificación automática ni IA. La aplicación local no incluye autenticación ni cifrado propios. No está preparada para publicarse en internet con datos de pacientes.

---

Las instrucciones ampliadas siguientes conservan la evolución del proyecto; el flujo actual de importación local está descrito arriba.

# DermAtlas local

Biblioteca dermatológica académica con FastAPI, SQLite y React/TypeScript. Incluye fichas editables, imágenes mediante enlaces HTTPS, etiquetas, varios diagnósticos por imagen, galerías ampliables, búsqueda, asociaciones diferenciales manuales, comparador, fases evolutivas y respaldo ZIP.

**Versión actual: imágenes mediante enlaces.** Las fichas y URLs se guardan localmente en SQLite; no se necesita contratar almacenamiento para fotografías. El navegador consulta el sitio de origen al mostrar cada imagen y puede usar su caché normal. Se necesita internet para las imágenes externas. No se ha publicado ni contratado alojamiento. La aplicación todavía requiere instalar sus dependencias y comprobar su ejecución completa.

Puedes trabajar con Codex: pedir que instale, inicie y abra la aplicación en su navegador integrado. Las instrucciones siguientes son también una alternativa manual; VS Code es opcional.

## Instalar y abrir en VS Code

Requisitos: Python 3.10 o superior, Node.js 22 LTS y Git. Abre **esta carpeta `dermatlas`** desde Archivo → Abrir carpeta en VS Code. En Terminal → Nueva terminal, en macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cd frontend
npm install
npm run build
cd ..
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

En Windows, crea el entorno con `py -m venv .venv` y actívalo con `.venv\Scripts\Activate.ps1`; los demás comandos son iguales.

Abre `http://127.0.0.1:8000` en tu navegador. Para detener: Ctrl+C. En sesiones siguientes solo activa el entorno y ejecuta el último comando desde la raíz. No uses `--host 0.0.0.0`.

Para desarrollo del frontend, ejecuta el backend y, en otra terminal dentro de `frontend`, `npm run dev`. Abre `http://127.0.0.1:5173`. El proxy envía `/api` al backend local. Para visualizar cambios en el servidor de puerto 8000, recompila el frontend y reinicia el backend.

## Uso

1. Administración → crea una ficha o elige una existente para editarla. Completa características y referencias. Las fichas iniciales son ejemplos vacíos de conocimiento médico.
2. Selecciona una enfermedad y agrega fases con nombre, orden y descripción.
3. Administración → Agregar imagen mediante enlace. Pega una URL HTTPS directa al archivo de imagen y, por separado, la página de origen. Registra autor/institución, procedencia y permiso/licencia. Selecciona uno o varios diagnósticos (⌘ en Mac, Ctrl en Windows). Si asignas una fase, debe pertenecer a uno de los diagnósticos seleccionados. Confirma la revisión de privacidad y guarda el enlace.
4. El atlas, el comparador y la evolución muestran las imágenes desde su sitio externo. Si falla la visualización, abre el detalle y pulsa «Abrir imagen original» o «Consultar página de origen». El programa no verifica que la URL responda con una imagen ni que su licencia sea válida: debes revisar la fuente. No uses enlaces con credenciales, tokens temporales o fotografías identificables de pacientes.
5. Busca por nombre o características y abre una tarjeta en Atlas. Pulsa una imagen para ampliarla y consultar sus datos.
6. Registra diferenciales en Administración. Puedes actualizar una asociación guardando otra vez el mismo par. La referencia es obligatoria para marcarla revisada.
7. Selecciona dos diagnósticos en Comparador o accede desde los diferenciales de una ficha. Evolución organiza fotografías por fase; el detalle muestra fecha y código de serie si existen.
8. Descarga periódicamente un respaldo desde Administración.

Quitar EXIF **no anonimiza visualmente una fotografía**. No importes material clínico sin autorización ni datos identificatorios. El programa es una herramienta académica y no realiza diagnóstico.

## Pruebas

Desde la raíz, con el entorno activado:

```bash
python -m pytest -q
cd frontend
npm run build
```

Las pruebas usan carpetas temporales, verifican persistencia, búsqueda, edición, importación con múltiples diagnósticos, eliminación de EXIF, reconstrucción del respaldo, relaciones y restricciones de origen. No requieren fotografías clínicas.

Consulta `VERIFICATION.md` para conocer qué comprobaciones se ejecutaron al entregar esta versión. No se deben confundir pruebas incluidas con pruebas ejecutadas.

## Respaldar y restaurar

El ZIP incluye `restore.sql`, que conserva fichas y enlaces. Solo incluye `images/` si existen fotografías locales de la versión anterior. Los archivos externos no se descargan ni se respaldan; si desaparece su fuente, el enlace dejará de funcionar. Para restaurar manualmente, detén el servidor, conserva una copia de tu `data/` actual y extrae el respaldo de confianza en una carpeta vacía. Crea `data/`, copia allí la carpeta `images/` si existe y reconstruye la base de datos:

```bash
python -c "import sqlite3; from pathlib import Path; c=sqlite3.connect('data/atlas.sqlite'); c.executescript(Path('RUTA_AL_RESPALDO/restore.sql').read_text()); c.close()"
```

Sustituye `RUTA_AL_RESPALDO` por la carpeta extraída. `data/atlas.sqlite` debe ser nuevo y estar vacío antes de ejecutar este comando. Reinicia la aplicación. Guarda respaldos fuera del repositorio y en almacenamiento protegido.

## Subir al repositorio que te compartieron

Acepta primero la invitación y comprueba que tienes permiso para subir ramas. La opción más sencilla es **clonar el repositorio compartido** en otra carpeta:

```bash
git clone URL_DEL_REPOSITORIO
cd NOMBRE_DEL_REPOSITORIO
git switch -c entrega/dermatlas-local
```

Copia dentro del clon el contenido de esta carpeta, incluida `.gitignore`. Si el repositorio ya contiene un proyecto, pon DermAtlas en una subcarpeta y respeta sus instrucciones. No copies `data`, `.venv`, `node_modules`, respaldos ni imágenes clínicas. Luego, desde el clon:

```bash
git status --short
git add .gitignore README.md ARCHITECTURE.md VERIFICATION.md backend frontend tests
git diff --cached --stat
git diff --cached
git commit -m "Implementa MVP local de biblioteca dermatológica"
git push -u origin entrega/dermatlas-local
```

Revisa antes de confirmar que no se incluyan datos privados. Si pusiste el proyecto en una subcarpeta, ajusta las rutas de `git add` a esa subcarpeta. Tras el push, abre GitHub y crea un **Pull Request** desde `entrega/dermatlas-local` hacia la rama indicada por quien compartió el repositorio. No hace falta subir directamente a `main`. Si no tienes permisos de escritura, necesitarás un fork o que te habiliten acceso. Si `npm install` genera `package-lock.json`, inclúyelo también en la entrega.

No se ha conectado ni subido nada a GitHub desde esta entrega.

## Privacidad de enlaces

El proveedor externo recibe la solicitud de imagen, incluida la dirección IP del navegador. Se envía `no-referrer` para no compartir la dirección de la ficha. Los enlaces públicos no son un mecanismo apropiado para compartir fotografías clínicas identificables. La carga externa no elimina EXIF ni modifica el archivo de origen. No hay miniaturas remotas generadas: se muestra el original a tamaño reducido; una imagen grande sigue consumiendo datos. Los enlaces pueden caducar o bloquear su visualización. La antigua API de importación local se mantiene para compatibilidad, pero la interfaz actual agrega enlaces.
