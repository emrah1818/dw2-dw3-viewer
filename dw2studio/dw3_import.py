"""Transactional DW3 -> existing DW2 slot replacement (PAK / overlay API 2)."""
import hashlib
import io
import json
from pathlib import Path
from .pak_workspace import PakSession
from .core.native_model import NativeModel
from .core.native_anim import parse_anim_file
from .core.dw3_native import encode_model, encode_animation, fit_scale, hd_name


def prepare(api, source_id, target_id):
    session = api._need_session()
    if not isinstance(session, PakSession):
        raise ValueError('Für den vollständigen DW3-Import bitte dw2.pak öffnen. Ein Disc-Image bleibt im bisherigen Importmodus.')
    info = api.prepare_dw3(source_id)
    folder = Path(info['path']).parent
    source_path = folder/'native_source.json'
    if not source_path.is_file():
        raise ValueError('DW3-Modell mit dem 0.15b-Konverter erneut öffnen.')
    source = json.loads(source_path.read_text())
    candidate = api._find(target_id)
    family, _, meta = api._model_family(candidate)
    table=meta.get('table',{})
    if meta.get('source')!='MODELDT' or not table.get('model_file_match') or table.get('unknown_ids'):
        raise ValueError('Modell-/Animationszuordnung des Ziel-Slots ist nicht vollständig verifiziert.')
    if any(s['origin'] not in ('MODELDT','unassigned') for s in meta['slots'].values()):
        raise ValueError('Ein zugeordneter Animationsplatz fehlt oder passt nicht zum Zielmodell.')
    if any(s['shared'] for s in meta['slots'].values()):
        raise ValueError('Das Ziel verwendet geteilte Animationsdateien. Einen Slot mit eigenen A–K-Dateien wählen; fremde Digimon werden nicht mitverändert.')
    model = next(e for e in family if Path(e.path).name.startswith('M'))
    n = NativeModel(session.current(model)).bone_count
    animations = {}
    descriptors = []
    for entry in family:
        slot = Path(entry.path).name[0]
        if slot not in 'ABCDEFGHIJK':
            continue
        if meta['slots'].get(slot,{}).get('origin')!='MODELDT':
            continue
        parsed = parse_anim_file(session.current(entry), n)
        animations[slot] = (entry, parsed)
        for c in parsed.clips:
            descriptors.append({'slot':slot,'clip':c.index,'motion':1,'loop':c.terminator==0xFE})
    if not animations:
        raise ValueError('Kein verifiziertes A–K-Ziel für diesen Slot.')
    first = next(iter(animations.values()))[0]
    scale = fit_scale(source, session.current(model), session.current(first))
    return {'source': source,'folder':folder,'model':model,'animations':animations,
            'info':{'name':info['name'],'target':candidate.name,'scale':scale,
                    'motions':[{'id':m['id'],'frames':len(m['frames'])} for m in source['motions']],
                    'assignments':descriptors,'source_bones':len(source['bones'])-1,'target_bones':n}}


def apply(api, source_id, target_id, assignments, scale_factor=1., hd_scale=4):
    prepared = prepare(api, source_id, target_id)
    source,session = prepared['source'],api._need_session()
    scale = prepared['info']['scale']*float(scale_factor)
    native,hd,report = encode_model(source,prepared['folder'],scale,int(hd_scale))
    expected = {(d['slot'],d['clip']) for d in prepared['info']['assignments']}
    if not isinstance(assignments,list) or len(assignments)!=len(expected):
        raise ValueError('Alle DW2-Animationsplätze müssen genau einmal zugeordnet werden.')
    seen=set();groups={};loops={}
    motion_index={m['id']:i for i,m in enumerate(source['motions'])}
    for row in assignments:
        key=(row['slot'],row['clip'])
        if key not in expected or key in seen or type(row['motion'])is not int or row['motion'] not in motion_index or type(row['loop'])is not bool:
            raise ValueError('Ungültige oder doppelte Animationszuordnung.')
        seen.add(key);groups.setdefault(key[0],{})[key[1]]=motion_index[row['motion']]
        if row['loop']:loops.setdefault(key[0],[]).append(key[1])
    changes=[(prepared['model'],native,'DW3-Modell mit eigenem Skelett')]
    for slot,mapping in groups.items():
        entry,_=prepared['animations'][slot]
        changes.append((entry,encode_animation(source,mapping,scale,loops.get(slot,[])),f'DW3-Bewegungen → {slot}'))
    buffer=io.BytesIO();hd.save(buffer,format='PNG')
    sha=hashlib.sha256(native).hexdigest()
    before=session.edits.copy()
    try:
        for entry,payload,label in changes:
            session.stage(entry,payload,label)
    except Exception:
        session.edits=before
        raise
    session.hd_files[sha]={f'Textures/DW2Studio_015/{hd_name(native)}':buffer.getvalue()}
    report.update(files=len(changes),hd_size=list(hd.size),requires_mod_api=2)
    return report
