from contextlib import asynccontextmanager
from pathlib import Path
import os, sqlite3, uuid, io, json, zipfile
from datetime import datetime
from urllib.parse import urlsplit
import ipaddress
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from PIL import Image, ImageOps, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("DERMATLAS_DATA", str(ROOT / "data")))
FIELDS = ["name", "synonyms", "category", "description", "morphology", "locations", "manifestations", "dermoscopy", "histology", "evolution", "references"]
def connect():
    c = sqlite3.connect(DATA / "atlas.sqlite")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

def init_db():
    DATA.mkdir(parents=True, exist_ok=True, mode=0o700)
    (DATA / "images").mkdir(exist_ok=True, mode=0o700)
    with connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS diseases(id TEXT PRIMARY KEY, name TEXT NOT NULL, synonyms TEXT DEFAULT '', category TEXT DEFAULT '', description TEXT DEFAULT '', morphology TEXT DEFAULT '', locations TEXT DEFAULT '', manifestations TEXT DEFAULT '', dermoscopy TEXT DEFAULT '', histology TEXT DEFAULT '', evolution TEXT DEFAULT '', "references" TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS phases(id TEXT PRIMARY KEY, disease_id TEXT NOT NULL REFERENCES diseases(id), name TEXT NOT NULL, position INTEGER NOT NULL, description TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS images(id TEXT PRIMARY KEY, filename TEXT NOT NULL, modality TEXT NOT NULL, tags TEXT, phase_id TEXT REFERENCES phases(id), taken_on TEXT, series TEXT, provenance TEXT NOT NULL, authorization TEXT NOT NULL, privacy_reviewed INTEGER NOT NULL, illustrative INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS image_diseases(image_id TEXT REFERENCES images(id) ON DELETE CASCADE, disease_id TEXT REFERENCES diseases(id), PRIMARY KEY(image_id,disease_id));
        CREATE TABLE IF NOT EXISTS differentials(source TEXT REFERENCES diseases(id), target TEXT REFERENCES diseases(id), similarities TEXT, differences TEXT, reference TEXT, validated INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(source,target), CHECK(source != target));
        """)
        # Additive migration preserves existing local images and diagnoses.
        columns = {r[1] for r in c.execute("PRAGMA table_info(images)")}
        for column in ("external_url", "source_url", "author"):
            if column not in columns:
                c.execute(f"ALTER TABLE images ADD COLUMN {column} TEXT NOT NULL DEFAULT ''")
        for subtype in ("Psoriasis en placas", "Psoriasis guttata", "Psoriasis inversa", "Psoriasis eritrodérmica", "Psoriasis pustular"):
            if not c.execute("SELECT 1 FROM diseases WHERE name=?", (subtype,)).fetchone():
                c.execute("INSERT INTO diseases(id,name,category,description) VALUES(?,?,?,?)", (str(uuid.uuid4()), subtype, "Psoriasis · tipo clínico", "Ficha pendiente de completar y revisar. Las fotografías se clasifican manualmente; la aplicación no determina el diagnóstico."))
        if not c.execute("SELECT 1 FROM diseases WHERE name=?", ("Psoriasis",)).fetchone():
            for name in ["Psoriasis", "Dermatitis seborreica", "Eccema"]:
                c.execute("INSERT INTO diseases(id,name,category,description) VALUES(?,?,?,?)", (str(uuid.uuid4()),name,"Ejemplo educativo","Ficha de demostración. Completar y revisar con bibliografía antes de utilizarla como material académico."))

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield
app = FastAPI(title="DermAtlas local", lifespan=lifespan)
@app.middleware("http")
async def local_only(request: Request, call_next):
    host = request.headers.get("host", "").split(":")[0]
    origin = request.headers.get("origin")
    if host not in ("127.0.0.1", "localhost", "testserver") or (origin and origin not in ("http://127.0.0.1:8000", "http://localhost:8000", "http://127.0.0.1:5173", "http://localhost:5173")):
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail":"Acceso permitido únicamente desde la aplicación local"}, status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; connect-src 'self'"
    return response

class Disease(BaseModel):
    name: str = Field(min_length=1,max_length=200)
    synonyms: str = ""
    category: str = ""
    description: str = ""
    morphology: str = ""
    locations: str = ""
    manifestations: str = ""
    dermoscopy: str = ""
    histology: str = ""
    evolution: str = ""
    references: str = ""
class Phase(BaseModel):
    name: str = Field(min_length=1)
    position: int = 0
    description: str = ""
class Differential(BaseModel):
    target: str
    similarities: str = ""
    differences: str = ""
    reference: str = ""
    validated: bool = False

def require(c, table, id):
    if not c.execute(f"SELECT 1 FROM {table} WHERE id=?", (id,)).fetchone():
        raise HTTPException(404,"Registro inexistente")

@app.get("/api/diseases")
def diseases(q: str = ""):
    import unicodedata
    def normalize(s):
        return ''.join(ch for ch in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(ch) != 'Mn')
    with connect() as c:
        rows = [dict(r) for r in c.execute("SELECT * FROM diseases ORDER BY name")]
        for r in rows:
            r["image_count"] = c.execute("SELECT count(*) FROM image_diseases WHERE disease_id=?",(r["id"],)).fetchone()[0]
        tokens = [t for t in normalize(q).split() if t not in ('en','de','la','el','y','con')]
        return [r for r in rows if all(t in normalize(' '.join(str(v) for v in r.values())) for t in tokens)]
@app.post("/api/diseases")
def create(d: Disease):
    id = str(uuid.uuid4())
    with connect() as c:
        c.execute('INSERT INTO diseases(id,'+','.join('"'+f+'"' for f in FIELDS)+') VALUES('+','.join('?' for _ in range(12))+')', [id]+[getattr(d,f) for f in FIELDS])
    return {"id":id}
@app.put("/api/diseases/{id}")
def update(id: str, d: Disease):
    with connect() as c:
        require(c,"diseases",id)
        c.execute('UPDATE diseases SET '+','.join('"'+f+'"=?' for f in FIELDS)+' WHERE id=?',[getattr(d,f) for f in FIELDS]+[id])
    return {"id":id}
@app.get("/api/diseases/{id}/phases")
def phases(id: str):
    with connect() as c:
        return [dict(r) for r in c.execute("SELECT * FROM phases WHERE disease_id=? ORDER BY position,name",(id,))]
@app.post("/api/diseases/{id}/phases")
def add_phase(id: str, p: Phase):
    pid=str(uuid.uuid4())
    with connect() as c:
        require(c,"diseases",id)
        c.execute("INSERT INTO phases VALUES(?,?,?,?,?)",(pid,id,p.name,p.position,p.description))
    return {"id":pid}
@app.get("/api/diseases/{id}/differentials")
def differentials(id: str):
    with connect() as c:
        return [dict(r) for r in c.execute("SELECT r.*, d.name FROM differentials r JOIN diseases d ON d.id=r.target WHERE source=?",(id,))]
@app.put("/api/diseases/{id}/differentials")
def relation(id: str, d: Differential):
    if id == d.target: raise HTTPException(400,"Selecciona otra enfermedad")
    if d.validated and not d.reference.strip(): raise HTTPException(400,"La validación requiere una referencia")
    with connect() as c:
        require(c,"diseases",id); require(c,"diseases",d.target)
        c.execute("INSERT OR REPLACE INTO differentials VALUES(?,?,?,?,?,?)",(id,d.target,d.similarities,d.differences,d.reference,int(d.validated)))
    return {"ok":True}
@app.get("/api/images")
def images(disease_id: Optional[str] = None, q: str = "", modality: str = ""):
    with connect() as c:
        rows = [dict(r) for r in c.execute("SELECT i.*,p.name AS phase_name FROM images i LEFT JOIN phases p ON p.id=i.phase_id ORDER BY coalesce(taken_on,'') DESC")]
        for r in rows:
            r["disease_ids"]=[x[0] for x in c.execute("SELECT disease_id FROM image_diseases WHERE image_id=?",(r["id"],))]
        return [r for r in rows if (not disease_id or disease_id in r["disease_ids"]) and (not modality or modality==r["modality"]) and q.lower() in (r["tags"] or '').lower()]
@app.post("/api/images")
async def upload(files: List[UploadFile] = File(...), disease_ids: str = Form(...), modality: str = Form("Clínica"), tags: str = Form(""), phase_id: str = Form(""), taken_on: str = Form(""), series: str = Form(""), provenance: str = Form(...), authorization: str = Form(...), privacy_reviewed: bool = Form(False)):
    if not privacy_reviewed or not provenance.strip() or not authorization.strip(): raise HTTPException(400,"Completa procedencia, autorización y revisión visual de privacidad")
    try: ids=json.loads(disease_ids)
    except ValueError: raise HTTPException(400,"Diagnósticos inválidos")
    if not isinstance(ids,list) or not ids or not all(isinstance(x,str) for x in ids): raise HTTPException(400,"Selecciona al menos un diagnóstico")
    if taken_on:
        try: datetime.strptime(taken_on,"%Y-%m-%d")
        except ValueError: raise HTTPException(400,"Fecha inválida")
    if len(files)>100: raise HTTPException(400,"Máximo 100 imágenes por lote")
    prepared=[]
    for f in files:
        raw=await f.read(20*1024*1024+1)
        if len(raw)>20*1024*1024: raise HTTPException(400,"Cada imagen debe ocupar como máximo 20 MB")
        try:
            with Image.open(io.BytesIO(raw)) as src:
                if src.width*src.height>40_000_000: raise ValueError()
                clean=ImageOps.exif_transpose(src).convert("RGB")
                out=io.BytesIO(); clean.save(out,format="JPEG",quality=92)
                prepared.append((str(uuid.uuid4()),out.getvalue()))
        except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombError): raise HTTPException(400,"Imagen inválida o demasiado grande; usa JPEG, PNG o WebP")
    paths=[]
    try:
        with connect() as c:
            for did in set(ids): require(c,"diseases",did)
            if phase_id:
                phase=c.execute("SELECT disease_id FROM phases WHERE id=?",(phase_id,)).fetchone()
                if not phase or phase[0] not in ids: raise HTTPException(400,"La fase no pertenece a los diagnósticos seleccionados")
            for iid,content in prepared:
                path=DATA/"images"/(iid+".jpg"); paths.append(path); path.write_bytes(content)
                c.execute("INSERT INTO images(id,filename,modality,tags,phase_id,taken_on,series,provenance,authorization,privacy_reviewed,illustrative) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(iid,path.name,modality,tags,phase_id or None,taken_on,series,provenance,authorization,1,0))
                c.executemany("INSERT INTO image_diseases VALUES(?,?)",[(iid,did) for did in set(ids)])
    except Exception:
        for path in paths: path.unlink(missing_ok=True)
        raise
    return {"imported":len(prepared)}
def validate_public_url(value: str) -> str:
    value = value.strip()
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme != "https" or not host or parsed.username or parsed.password or parsed.port not in (None, 443):
            raise ValueError()
        if host == "localhost" or host.endswith((".localhost", ".local", ".internal")) or "." not in host:
            raise ValueError()
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            address = None
        if address is not None and not address.is_global:
            raise ValueError()
    except ValueError:
        raise HTTPException(400, "Usa un enlace HTTPS público, sin contraseñas ni direcciones locales")
    return value

class ImageLink(BaseModel):
    external_url: str = Field(min_length=1, max_length=4096)
    source_url: str = Field(min_length=1, max_length=4096)
    author: str = Field(min_length=1, max_length=500)
    disease_ids: List[str] = Field(min_length=1)
    modality: str = "Clínica"
    tags: str = ""
    phase_id: Optional[str] = None
    taken_on: str = ""
    series: str = ""
    provenance: str = Field(min_length=1)
    authorization: str = Field(min_length=1)
    privacy_reviewed: bool = False

@app.post("/api/image-links")
def add_image_link(d: ImageLink):
    url = validate_public_url(d.external_url)
    source = validate_public_url(d.source_url)
    if not d.privacy_reviewed or not all(v.strip() for v in (d.author, d.provenance, d.authorization)):
        raise HTTPException(400, "Registra autor, procedencia, permiso de uso y revisión de privacidad")
    if d.taken_on:
        try: datetime.strptime(d.taken_on, "%Y-%m-%d")
        except ValueError: raise HTTPException(400, "Fecha inválida")
    iid = str(uuid.uuid4())
    with connect() as c:
        for did in set(d.disease_ids): require(c, "diseases", did)
        if d.phase_id:
            phase = c.execute("SELECT disease_id FROM phases WHERE id=?", (d.phase_id,)).fetchone()
            if not phase or phase[0] not in d.disease_ids:
                raise HTTPException(400, "La fase no pertenece a los diagnósticos seleccionados")
        c.execute("""INSERT INTO images(id,filename,modality,tags,phase_id,taken_on,series,provenance,authorization,privacy_reviewed,illustrative,external_url,source_url,author)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (iid,"",d.modality,d.tags,d.phase_id or None,d.taken_on,d.series,d.provenance,d.authorization,1,int(not bool(d.series)),url,source,d.author))
        c.executemany("INSERT INTO image_diseases VALUES(?,?)", [(iid,did) for did in set(d.disease_ids)])
    # Store only text: never fetch, download, proxy or validate remote content here.
    return {"id": iid}

@app.get("/api/images/{id}/file")
def image_file(id: str):
    with connect() as c:
        row=c.execute("SELECT filename,external_url FROM images WHERE id=?",(id,)).fetchone()
        if not row: raise HTTPException(404)
    if row[1]: raise HTTPException(400,"Imagen externa: usa su enlace original")
    return FileResponse(DATA/"images"/row[0],media_type="image/jpeg")
@app.get("/api/backup")
def backup():
    out=io.BytesIO()
    with connect() as source:
        target=sqlite3.connect(":memory:")
        source.backup(target)
        sql='\n'.join(target.iterdump()); target.close()
        with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
            z.writestr("restore.sql",sql)
            for row in source.execute("SELECT filename FROM images WHERE filename != ''"):
                z.write(DATA/"images"/row[0],"images/"+row[0])
    out.seek(0)
    return StreamingResponse(out,media_type="application/zip",headers={"Content-Disposition":"attachment; filename=dermatlas-backup.zip"})
if (ROOT/"frontend/dist").exists():
    app.mount("/",StaticFiles(directory=ROOT/"frontend/dist",html=True),name="frontend")
