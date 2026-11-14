"""Transactional DW3 -> existing DW2 slot replacement (PAK / overlay API 2)."""
import hashlib
import io
import json
from pathlib import Path
from .pak_workspace import PakSession
from .core.native_model import NativeModel
from .core.native_anim import parse_anim_file
from .core.dw3_native import encode_model, encode_animation, fit_scale, hd_name


from .core.dw3_native import limits_report


def prepare(api, source_id, target_id):
    session = api._need_session()
    if not isinstance(session, PakSession):
        raise ValueError('Für den vollständigen DW3-Import bitte dw2.pak öffnen. Ein Disc-Image bleibt im bisherigen Importmodus.')
    info = api.prepare_dw3(source_id)
    folder = Path(info['path']).parent
    source_path = folder/'native_source.json'
    if not source_path.is_file():
        raise ValueError('DW3-Modell mit dem Konverter ab 0.15b erneut öffnen.')
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
    slot_scale = fit_scale(source, session.current(model), session.current(first))
    # Size (1.0): the Digimon keeps its own size class instead of the replaced Digimon's height.
    # Same species in DW2 (same model code, e.g. AGUM): exactly that height; otherwise the DW2 size
    # curve (dw3_native.natural_scale). A Rookie stays small, a Mega stays large.
    from .core.dw3_native import natural_scale, model_height
    code = info['name'][4:8] if len(info['name']) >= 8 else ''
    twin = next((c for c in api.S.catalog if c.code == code), None) if code else None
    size_source = 'Größenkurve DW3 → DW2'
    dw2_height = None
    if twin is not None:
        try:
            tfam, _, tmeta = api._model_family(twin)
            tmodel = next(e for e in tfam if Path(e.path).name.startswith('M'))
            tanim = next(e for e in tfam if Path(e.path).name[0] == 'A')
            dw2_height = model_height(session.current(tmodel), session.current(tanim))
            size_source = f'Höhe von {twin.name} (#{twin.id:03}) in DW2'
        except (StopIteration, ValueError, KeyError, IndexError):
            dw2_height = None
    scale = natural_scale(source, dw2_height)
    scale_dw3 = natural_scale(source, None, 'dw3')
    from .core.dw3_native import source_height
    h3 = source_height(source)
    # Defaults from the DW3 battle scripts (dw3_motion_map); every row says where it comes from.
    from .dw3_fighters import script_motions
    from .dw3_motion_map import apply_defaults
    try:
        scripts = script_motions(api.DW3.path, api.DW3.entries[source_id], api.DW3.cache / 'scripts')
    except (OSError, ValueError):
        scripts = None
    apply_defaults(descriptors, scripts['scripts'] if scripts else [], {m['id'] for m in source['motions']})
    from .dw3_fighters import face_for
    try:
        face = face_for(api.DW3.path, api.DW3.entries[source_id])
    except (OSError, ValueError):
        face = None
    from .core.dw3_native import face_plan
    face_parts, face_notes = face_plan(source, face)
    return {'source': source,'folder':folder,'model':model,'animations':animations,'face':face,
            'info':{'name':info['name'],'target':candidate.name,'scale':scale,'slot_scale':slot_scale,
                    'size_source':size_source,'scale_dw3':scale_dw3,
                    'heights':{'dw2':round(h3*scale),'dw3':round(h3*scale_dw3),'slot':round(h3*slot_scale)},
                    'motions':[{'id':m['id'],'frames':len(m['frames'])} for m in source['motions']],
                    'assignments':descriptors,'source_bones':len(source['bones'])-1,'target_bones':n,
                    'limits':limits_report(source),
                    'face':{'parts':len(face_parts),'eyes':sum(f['slot'] < 2 for f in face_parts),'notes':face_notes}}}


def apply(api, source_id, target_id, assignments, scale_factor=1., hd_scale=0, camera=None, size_mode='dw2'):
    """CAMERA: None = automatic (battle_camera.suggest), or {'field_1E': int, 'hit_fx_y': int}."""
    prepared = prepare(api, source_id, target_id)
    source,session = prepared['source'],api._need_session()
    if size_mode not in ('dw2','dw3'):
        raise ValueError('Größenmaßstab: dw2 oder dw3.')
    scale = prepared['info']['scale' if size_mode=='dw2' else 'scale_dw3']*float(scale_factor)
    native,hd,report = encode_model(source,prepared['folder'],scale,int(hd_scale),prepared.get('face'))
    expected = {(d['slot'],d['clip']) for d in prepared['info']['assignments']}
    if not isinstance(assignments,list) or len(assignments)!=len(expected):
        raise ValueError('Alle DW2-Animationsplätze müssen genau einmal zugeordnet werden.')
    seen=set();groups={};loops={}
    motion_index={m['id']:i for i,m in enumerate(source['motions'])}
    for row in assignments:
        key=(row.get('slot'),row.get('clip'))
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
    cam=_camera_plan(api,prepared,target_id,native,changes,camera)
    before=session.edits.copy()
    try:
        for entry,payload,label in changes:
            session.stage(entry,payload,label)
        if cam['repo'].set(target_id,cam['field_1E'],cam['hit_fx_y'],f'Kamera / Treffereffekt #{target_id:03} (DW3-Import)'):
            report['camera_changed']=True
    except Exception:
        session.edits=before
        raise
    report['camera']={k:v for k,v in cam.items() if k!='repo'}
    # Attack / target / close-up shots (Mods/battle_camera.json, PC port 1.0): the smallest change
    # that keeps the new Digimon whole on screen in every battle position (battle_shots.auto)
    from .core import battle_shots
    order='AFGH'
    new_anims=sorted(((Path(e.path).name[0],pl) for e,pl,_ in changes[1:] if Path(e.path).name[0] in order),
                     key=lambda t:order.index(t[0]))
    shots_cam={}
    if new_anims and new_anims[0][0]=='A':
        box=battle_shots.model_box(native,[pl for _,pl in new_anims],points=True)
        auto=battle_shots.auto(box)
        close=battle_shots.auto_closeup(box,cam['field_1E'])
        shots_cam=dict(auto or {})
        if close:
            shots_cam['closeup']=close
        report['battle_camera']={'setting':shots_cam,'box':[round(v) for v in box[:3]]}
    if hasattr(api,'S'):
        if shots_cam:
            api.S.battle_camera[target_id]=battle_shots.validate(shots_cam)
        else:
            api.S.battle_camera.pop(target_id,None)
    if hasattr(api,'S') and hasattr(api.S,'dw3_imports'):
        api.S.dw3_imports[target_id]={'source_name':prepared['info']['name'],'assignments':assignments,
                                      'scale':float(scale_factor),'hd':int(hd_scale),'size':round(scale,4),
                                      'size_mode':size_mode}
    session.hd_files[sha]={f'Textures/DW2Studio_015/{hd_name(native)}':buffer.getvalue()}
    report.update(files=len(changes),hd_size=list(hd.size),requires_mod_api=2)
    return report


def _camera_plan(api, prepared, target_id, native, changes, camera):
    """Close-up camera for the new model: from the slot's own values plus the height change."""
    from .core.battle_camera import CameraRepository, measure, suggest, bucket
    session = api._need_session()
    repo = CameraRepository(session, api.S.entries)
    slot = repo.values(target_id, original=True)
    anims = {slot_: entry for slot_, (entry, _) in prepared['animations'].items()}
    new_payload = {entry.path: payload for entry, payload, _ in changes}
    def heights(model, read):
        attacks = [read(anims[s]) for s in 'FGH' if s in anims]
        return measure(model, read(anims['A']), attacks)
    if 'A' not in anims:
        raise ValueError('Ziel ohne Standby-Animation (A); Kamera kann nicht angepasst werden.')
    old_h = heights(session.original(prepared['model']), session.original)
    new_h = heights(native, lambda e: new_payload.get(e.path, session.current(e)))
    auto = suggest(slot['field_1E'], slot['hit_fx_y'], old_h, new_h)
    if camera:
        field, hit = int(camera['field_1E']), int(camera['hit_fx_y'])
    else:
        field, hit = auto
    return {'repo': repo, 'field_1E': field, 'hit_fx_y': hit, 'bucket': bucket(field),
            'auto': {'field_1E': auto[0], 'hit_fx_y': auto[1], 'bucket': bucket(auto[0])},
            'slot': slot, 'heights': {'slot': [round(v) for v in old_h], 'new': [round(v) for v in new_h]},
            'manual': bool(camera)}
