"""PC transport, publication and sidecar import regression checks."""
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError
import json
import pytest
import android_api as api
from desktop import AssetServer, Worker, copy_export


def test_asset_server_scopes_paths_and_serves_es_modules(tmp_path):
    www=tmp_path/'www';cache=tmp_path/'cache';www.mkdir();cache.mkdir()
    (www/'app.js').write_text('export const ready=true;')
    (cache/'model.gltf').write_text('{}')
    (tmp_path/'secret.txt').write_text('private')
    server=AssetServer(www,cache)
    try:
        with urlopen(server.base+'www/app.js') as r:
            assert r.headers.get_content_type()=='text/javascript'
            assert b'ready=true' in r.read()
        with urlopen(server.base+'viewer/model.gltf') as r:
            assert r.read()==b'{}'
        for path in ('www/%2e%2e/secret.txt','viewer/%2e%2e/secret.txt'):
            with pytest.raises(HTTPError):urlopen(server.base+path)
        with pytest.raises(HTTPError):urlopen(server.origin+'/www/app.js')
    finally:server.close()


def test_export_publication_and_source_guard(tmp_path,monkeypatch):
    source=tmp_path/'source.bin';source.write_bytes(b'export')
    dest=tmp_path/'new.bin'
    monkeypatch.setattr(api.S,'image_path',source)
    assert copy_export(source,dest)
    assert dest.read_bytes()==source.read_bytes()
    dest.write_bytes(b'previous')
    assert copy_export(source,dest)
    with pytest.raises(ValueError):copy_export(dest,source)
    assert source.read_bytes()==b'export'


def test_bridge_worker_returns_backend_errors():
    worker=Worker();answers=[]
    worker.resolved.connect(lambda ident,response:answers.append((ident,json.loads(response))))
    worker.run('test','method_that_does_not_exist','[]')
    assert answers[0][0]=='test' and answers[0][1]['ok'] is False


def test_desktop_import_keeps_obj_material_and_texture(tmp_path,monkeypatch):
    import android_edit as edit
    cache=tmp_path/'cache';cache.mkdir();monkeypatch.setattr(api,'CACHE',cache)
    model=tmp_path/'body.obj';model.write_text('mtllib body.mtl\nv 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n')
    (tmp_path/'body.mtl').write_text('newmtl body\nmap_Kd body.png\n')
    (tmp_path/'body.png').write_bytes(b'png-fixture')
    info=edit.inspect_3d(str(model));job=edit.PENDING.pop(info['token'])
    assert (job['folder']/'body.mtl').is_file()
    assert (job['folder']/'body.png').read_bytes()==b'png-fixture'
    assert job['path'].name=='body.obj'
