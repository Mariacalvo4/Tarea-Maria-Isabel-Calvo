# Subir la entrega al repositorio compartido

1. Acepta la invitación al repositorio de GitHub.
2. Descarga y descomprime `dermatlas-github.zip`.
3. Clona el repositorio compartido (sustituye las dos rutas de ejemplo):

```bash
git clone URL_DEL_REPOSITORIO
cd NOMBRE_DEL_REPOSITORIO
git switch -c entrega/atlas-psoriasis
```

4. Copia dentro del clon el contenido de la carpeta `dermatlas`, incluyendo `.gitignore`. Si el repositorio tiene otros archivos, no los reemplaces sin revisar; puedes colocar el proyecto en una subcarpeta.
5. Desde la carpeta clonada:

```bash
git status --short
git add .
git diff --cached --stat
git diff --cached
```

Revisa que solo aparezcan código y documentación. No deben aparecer fotos, `data/`, bases de datos, archivos `.env`, contraseñas ni respaldos. Luego:

```bash
git commit -m "Agrega atlas local con cinco tipos de psoriasis"
git push -u origin entrega/atlas-psoriasis
```

6. En GitHub abre un Pull Request desde tu rama hacia la rama que te indique quien compartió el repositorio.

Si no tienes permisos para subir ramas, pide acceso o utiliza un fork. No se ha realizado ningún push desde Codex. Las galerías del código entregado empiezan sin fotos; las imágenes personales permanecen en la biblioteca local y no forman parte del repositorio.
