"""Read DW2 converter blink metadata without inventing frame mappings."""
import json
from pathlib import Path

def read_blinking_data(gltf_path):
    path=Path(gltf_path)
    if path.suffix.lower() != '.gltf':
        return None
    # Blinkdaten sind nur ein Zusatz. Fremde oder beschädigte glTF-Dateien
    # dürfen deshalb niemals das Laden des Modells verhindern.
    try:
        document=json.loads(path.read_text(encoding='utf-8'))
        scenes=document.get('scenes',[])
        active=document.get('scene',0)
        if not isinstance(scenes,list) or not isinstance(active,int) or not 0<=active<len(scenes):return None
        extras=scenes[active].get('extras',{})
        values=extras.get('blinking_data') if isinstance(extras,dict) else None
    except (OSError,ValueError,AttributeError,TypeError):
        return None
    if not isinstance(values,list):return None
    if len(values)!=24 or any(type(v) is not int or v<0 or v>255 for v in values):
        return None
    return bytes(values)
