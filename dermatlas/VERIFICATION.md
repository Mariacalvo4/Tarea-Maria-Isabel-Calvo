# Verificación de la entrega

Fecha: 10 de noviembre de 2026.

Comprobaciones ejecutadas correctamente:

- Análisis sintáctico de todos los archivos Python mediante `ast.parse`.
- Ejecución del código real de inicialización y conexión SQLite en una carpeta temporal, aislado de las importaciones de FastAPI.
- Dos inicializaciones consecutivas sin duplicar las tres fichas de ejemplo.
- `PRAGMA integrity_check`: `ok`.
- `PRAGMA foreign_key_check`: sin errores.
- Claves foráneas activadas.

No ejecutado: instalación de dependencias, servidor FastAPI, suite pytest, compilación TypeScript/Vite y revisión visual en navegador. El entorno de entrega tiene Python 3.9.6, no tiene Node.js/npm y no tiene instalados FastAPI, Pillow, pytest ni httpx. Por tanto, esta entrega es código implementado con verificación parcial, no una aplicación validada de extremo a extremo. Ejecutar las instrucciones de README y resolver cualquier fallo antes de usarla con material real.

La primera comprobación con `compileall` no pudo escribir el caché de Python fuera del espacio de trabajo; se sustituyó por análisis sintáctico en memoria. No fue un error de sintaxis del proyecto.

Límites del MVP y funciones futuras documentados en ARCHITECTURE.md.

## Verificación de imágenes por enlace

Se ejecutó además el código real de funciones de persistencia de enlaces, aislado mediante AST de las dependencias web no instaladas. Se comprobaron migración aditiva repetible desde el esquema anterior, rechazo de siete URLs inválidas, asociación con dos diagnósticos, persistencia de URL, ausencia de archivos de imagen descargados y restauración del SQL de respaldo con enlaces. No se hizo ninguna solicitud a las URLs de prueba. Esto no equivale a una prueba HTTP de FastAPI ni a una revisión del frontend en navegador. Se añadieron pruebas pytest para esos flujos; siguen pendientes de ejecución por falta de dependencias.

## Aplicación ejecutada en Codex

Se localizaron Python 3.12 y Node.js 24 en el runtime integrado de Codex y se instalaron las dependencias dentro del proyecto. Esto resuelve las limitaciones del entorno descritas en las secciones anteriores.

- Suite HTTP real con FastAPI/TestClient: **4 pruebas aprobadas**. Incluye fichas, búsqueda, relaciones, privacidad/origen, imágenes locales, EXIF, imágenes por enlace y respaldo restaurable.
- TypeScript (`tsc`): aprobado.
- Compilación de producción con Vite: aprobada.
- Servidor iniciado en `http://127.0.0.1:8000`.
- Interfaz real abierta en el navegador integrado: Inicio y formulario de enlaces revisados. La biblioteca permanece vacía de fotografías; no se han cargado imágenes externas de terceros.
- Corregido un error de número de parámetros SQL en la importación local antigua, detectado por la suite.

Queda pendiente una prueba visual completa de agregar una URL real, cargar su imagen, compararla y revisar el comportamiento en distintos anchos. El éxito de las pruebas actuales no certifica seguridad para datos clínicos ni disponibilidad de enlaces externos.

pnpm descargó las dependencias y señaló que omitió el script de instalación de esbuild. La compilación posterior de Vite se ejecutó correctamente con el binario disponible. Se conserva `frontend/pnpm-lock.yaml` para registrar las versiones resueltas.
