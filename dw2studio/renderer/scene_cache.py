"""Lightweight scene dependency fingerprints for bounded VTK scene reuse."""
from pathlib import Path
import json
from functools import lru_cache
from urllib.parse import unquote

@lru_cache(maxsize=64)
def _references(path,size,mtime):
    file=Path(path)
    if file.suffix.lower()!='.gltf':return ()
    doc=json.loads(file.read_text(encoding='utf-8'))
    refs=[]
    for item in doc.get('images',[])+doc.get('buffers',[]):
        uri=item.get('uri','')
        if not uri or uri.startswith('data:') or '://' in uri:continue
        dependency=(file.parent/unquote(uri)).resolve()
        if dependency.is_relative_to(file.parent):refs.append(str(dependency))
    return tuple(refs)


def scene_key(path):
    path=Path(path).resolve();st=path.stat();dependencies=[]
    for ref in _references(str(path),st.st_size,st.st_mtime_ns):
        try:
            stamp=Path(ref).stat();dependencies.append((ref,stamp.st_size,stamp.st_mtime_ns))
        except OSError:dependencies.append((ref,None,None))
    return str(path),st.st_size,st.st_mtime_ns,tuple(dependencies)
