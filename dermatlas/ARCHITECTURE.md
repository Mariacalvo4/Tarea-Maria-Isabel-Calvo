# Actualización: imágenes externas mediante enlaces

La preferencia actual del usuario reemplaza la importación local como flujo principal. La aplicación sigue siendo local, con fichas y enlaces persistentes en SQLite, pero requiere internet para mostrar imágenes externas. No se ha elegido ni conectado un proveedor de nube.

La tabla `images` agrega `external_url`, `source_url` y `author` con una migración aditiva e idempotente. Los registros antiguos se conservan. `POST /api/image-links` registra un enlace con diagnósticos, modalidad, etiquetas, fase y procedencia. Exige HTTPS, autor, permiso y revisión de privacidad. Rechaza esquemas inseguros, credenciales y hosts locales evidentes. No resuelve DNS ni garantiza que un dominio no cambie o redirija: esta validación no certifica seguridad o disponibilidad del sitio.

El backend nunca consulta ni descarga las URLs. El navegador usa el enlace directamente con `referrerPolicy="no-referrer"`; la CSP permite imágenes HTTPS. Si la carga falla, la interfaz ofrece el enlace original y la fuente en el detalle. No se incorpora un proxy, raspado de sitios ni descarga de fotografías. Los enlaces privados que requieren autenticación pueden no mostrarse; no se deben pegar URLs con credenciales o tokens secretos.

El respaldo incluye la base de datos con URLs y solo añade archivos locales preexistentes. No incluye copias de imágenes externas. No se puede garantizar disponibilidad, permanencia o licencia de material externo; la comprobación es manual. No hay miniaturas generadas: el navegador reduce visualmente el original.

A continuación se conserva el diseño de base del MVP; el formulario de importación local ha sido reemplazado por el de enlaces.

# Arquitectura del MVP

La aplicación separa una API FastAPI, persistencia SQLite y un frontend React/TypeScript. Tras compilar el frontend, FastAPI sirve todo desde `http://127.0.0.1:8000`: no hay CDN, telemetría, cuentas externas ni IA. La instalación inicial de dependencias sí requiere internet; el funcionamiento posterior es local.

## Modelo relacional

- `diseases`: UUID y los once campos de la ficha académica.
- `images`: UUID, archivo interno, modalidad, etiquetas libres, fase, fecha, código de serie, procedencia, autorización y constancia de revisión visual.
- `image_diseases`: relación muchos a muchos entre imágenes y diagnósticos.
- `phases`: fases ordenadas, cada una perteneciente a una enfermedad.
- `differentials`: relación dirigida entre dos diagnósticos, con semejanzas, diferencias, referencia y estado de revisión manual. No se generan relaciones automáticamente.

Claves foráneas habilitadas en cada conexión, consultas parametrizadas y transacciones al importar. La búsqueda de fichas normaliza acentos y combina términos; la interfaz también consulta etiquetas y modalidades. Las relaciones se exploran desde la ficha seleccionada. No hay búsqueda semántica ni inferencia clínica.

## Archivos

```text
backend/main.py          API, validaciones, persistencia y respaldo
backend/requirements.txt dependencias Python
frontend/src/main.tsx    cinco vistas y formularios
frontend/src/style.css   interfaz adaptable sin recursos externos
frontend/vite.config.ts  proxy local de desarrollo
tests/test_api.py        pruebas funcionales de la API
data/atlas.sqlite       se crea en el primer inicio; excluido de Git
data/images/            copias JPEG sin EXIF; excluidas de Git
```

## Decisiones y alcance

SQLite permite persistencia transaccional sin administrar un servidor. Los UUID desacoplan los nombres originales de los archivos. Pillow decodifica y reescribe las imágenes; no copia EXIF ni otros metadatos del original. Se admiten lotes de hasta 100 archivos, máximo 20 MB y 40 megapíxeles por imagen. Se preservan los originales. Una carpeta que contenga archivos no compatibles debe filtrarse antes de importar: un archivo inválido rechaza todo el lote.

La serie es un código educativo desidentificado: no se almacenan nombres ni identificadores de pacientes. Las imágenes sin serie se muestran como material ilustrativo. La fecha no se infiere del EXIF. No se incluyen fotografías reales ni conocimientos clínicos inventados: las tres fichas iniciales requieren completar y validar contenido. Los gráficos de las tarjetas son marcadores ficticios hechos con CSS.

La revisión de un diferencial es una declaración manual del editor, no una certificación del programa. Las relaciones son dirigidas: registrar A → B no crea B → A. El comparador muestra dos enfermedades, con fichas e imágenes lado a lado. La evolución usa fases de cada enfermedad y muestra los códigos de seguimiento en el detalle de la fotografía.

El MVP permite crear y editar fichas, agregar fases, importar imágenes con múltiples diagnósticos y crear/actualizar asociaciones diferenciales. La edición posterior de metadatos/asociaciones de imágenes, eliminación de registros, edición de fases, permisos multiusuario, cifrado de archivos y restauración mediante interfaz quedan fuera de esta versión. Actualmente la API está en un módulo pequeño; la separación por routers, repositorios y servicios es el siguiente paso cuando aumente el alcance.

## Privacidad y extensión

El servidor se enlaza a loopback y verifica Host/Origin. No sustituye la seguridad del equipo: no hay contraseña ni cifrado de base de datos, fotografías o ZIP. Usar una cuenta protegida y cifrado de disco; cualquier usuario o proceso con acceso a esos archivos puede leerlos. El respaldo contiene material sensible y debe protegerse igualmente. No publicar carpetas de datos ni respaldos en GitHub.

Una futura tabla `embeddings(image_id, model, version, vector_path)` y un servicio local separado podrían incorporar recuperación visual sin alterar fichas o asociaciones validadas. No hay modelos, descargas ni conexiones de IA en este MVP.
