import io
import sqlite3
import zipfile
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from backend import main

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'DATA', tmp_path)
    with TestClient(main.app) as client:
        yield client

def image_bytes():
    out = io.BytesIO()
    im = Image.new('RGB', (30,30), 'salmon')
    exif = Image.Exif(); exif[315] = 'Identificador privado'
    im.save(out, format='JPEG', exif=exif)
    return out.getvalue()

def test_persistence_search_and_update(client):
    r = client.post('/api/diseases', json={'name':'Prueba','morphology':'placas eritematodescamativas','locations':'cuero cabelludo'})
    assert r.status_code == 200
    did = r.json()['id']
    assert client.get('/api/diseases', params={'q':'placas en cuero cabelludo'}).json()[0]['id'] == did
    assert client.put('/api/diseases/'+did,json={'name':'Nombre actualizado'}).status_code == 200
    with main.connect() as db:
        assert db.execute('SELECT name FROM diseases WHERE id=?',(did,)).fetchone()[0] == 'Nombre actualizado'

def test_import_multiple_diagnoses_exif_and_backup(client):
    ds=client.get('/api/diseases').json()
    ids=[ds[0]['id'],ds[1]['id']]
    import json
    data={'disease_ids':json.dumps(ids),'provenance':'Ilustración propia','authorization':'Uso educativo autorizado','privacy_reviewed':'true'}
    r=client.post('/api/images',data=data,files=[('files',('test.jpg',image_bytes(),'image/jpeg'))])
    assert r.status_code==200, r.text
    photo=client.get('/api/images').json()[0]
    assert set(photo['disease_ids'])==set(ids)
    with Image.open(io.BytesIO(client.get('/api/images/'+photo['id']+'/file').content)) as im:
        assert not im.getexif()
    archive=zipfile.ZipFile(io.BytesIO(client.get('/api/backup').content))
    restored=sqlite3.connect(':memory:')
    restored.executescript(archive.read('restore.sql').decode())
    assert restored.execute('SELECT count(*) FROM images').fetchone()[0]==1
    assert 'images/'+photo['filename'] in archive.namelist()

def test_validation_and_relations(client):
    ds=client.get('/api/diseases').json(); a,b=ds[0]['id'],ds[1]['id']
    path='/api/diseases/'+a+'/differentials'
    assert client.put(path,json={'target':b,'validated':True}).status_code==400
    assert client.put(path,json={'target':a}).status_code==400
    assert client.put(path,json={'target':b,'reference':'Referencia revisada','validated':True}).status_code==200
    assert client.get(path).json()[0]['target']==b
    assert client.post('/api/images',data={'disease_ids':'[]','provenance':'x','authorization':'x'},files={'files':('x.jpg',image_bytes())}).status_code==400
    assert client.get('/api/diseases',headers={'Origin':'https://example.com'}).status_code==403
    assert client.get('/api/diseases',headers={'Host':'example.com'}).status_code==403

def test_external_links_persist_without_download(client):
    ds=client.get('/api/diseases').json()
    payload={'external_url':'https://example.org/image.jpg','source_url':'https://example.org/article','author':'Autor de prueba','disease_ids':[ds[0]['id'],ds[1]['id']],'provenance':'Colección educativa','authorization':'Permiso registrado','privacy_reviewed':True}
    r=client.post('/api/image-links',json=payload)
    assert r.status_code==200, r.text
    image=client.get('/api/images').json()[0]
    assert image['external_url']==payload['external_url']
    assert set(image['disease_ids'])==set(payload['disease_ids'])
    assert list((main.DATA/'images').iterdir())==[]
    assert client.get('/api/images/'+image['id']+'/file').status_code==400
    archive=zipfile.ZipFile(io.BytesIO(client.get('/api/backup').content))
    assert archive.namelist()==['restore.sql']
    restored=sqlite3.connect(':memory:')
    restored.executescript(archive.read('restore.sql').decode())
    assert restored.execute('SELECT external_url FROM images').fetchone()[0]==payload['external_url']
    assert 'https:' in client.get('/api/diseases').headers['content-security-policy']
    for url in ['http://example.org/a.jpg','https://127.0.0.1/a','https://localhost/a','https://user:secret@example.org/a']:
        assert client.post('/api/image-links',json={**payload,'external_url':url}).status_code==400
    assert client.post('/api/image-links',json={**payload,'privacy_reviewed':False}).status_code==400
