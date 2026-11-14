"""Encode DW3 skeletons, rigid geometry and sampled motions as native DW2 files.

Source coordinates/matrices are emitted by the bundled DW3 motion player.
The DW2 matrix stream is written row-major, matching Anim_StepModelAnim.
This encoder needs the variable-size PC-port loader; it is not a PS1 disc writer.
"""
from pathlib import Path
import math
import struct
import numpy as np
from PIL import Image
from .native_model import NativeModel
from .native_anim import parse_anim_file


def triangles(bone):
    return [(face, (0, fan, fan+1)) for face in bone['faces']
            for fan in range(1, len(face['indices'])-1)]


MAX_DEPTH = 7          # depth field 0..7: eight DW2 hierarchy levels
MAX_PART = 256         # vertex / normal / triangle indices are one byte per part
MAX_PARTS = 64


def bone_chunks(bone):
    """Triangles of one DW3 bone in parts of at most 256 triangles and 256 vertices.

    A native vertex index is one byte, so a bone with more vertices is split into sibling parts
    that share the bone's transform; every part keeps only the vertices it uses."""
    tris = triangles(bone)
    if not tris:
        return [[]]
    chunks, cur, used = [], [], set()
    for tri in tris:
        face, corners = tri
        ids = {face['indices'][k] for k in corners}
        if cur and (len(cur) >= MAX_PART or len(used | ids) > MAX_PART):
            chunks.append(cur)
            cur, used = [], set()
        cur.append(tri)
        used |= ids
    chunks.append(cur)
    return chunks


def plan(source):
    """Native part list: [{'src', 'depth', 'chain', 'chunk'}].

    Bones deeper than the eight DW2 levels are attached to their ancestor on level 7 (depth 6),
    and their animation matrix becomes the product of the skipped local matrices ('chain'), so
    the pose stays exact. Large bones become several sibling parts (bone_chunks)."""
    bones = source['bones']
    if not 2 <= len(bones) <= 65 or bones[0]['parent'] != -1:
        raise ValueError('DW3-Skelett benötigt 1–64 Körperknochen und eine Wurzel.')
    children = [[] for _ in bones]
    for i, b in enumerate(bones[1:], 1):
        p = b['parent']
        if type(p) is not int or not 0 <= p < i:
            raise ValueError('Ungültige DW3-Knochenhierarchie.')
        children[p].append(i)
    nodes = []

    def visit(i, depth, chain):
        if depth > MAX_DEPTH:
            depth = MAX_DEPTH          # chain: skipped ancestors below level 7, then this bone
        else:
            chain = [i]
        # The final copy goes immediately before the children: DW2's depth stack then uses the
        # same source transform for their parent.
        for k in range(len(bone_chunks(bones[i]))):
            nodes.append({'src': i, 'depth': depth, 'chain': list(chain), 'chunk': k})
        for child in children[i]:
            if depth >= MAX_DEPTH:
                visit(child, depth + 1, chain + [child])
            else:
                visit(child, depth + 1, [child])
    for child in children[0]:
        visit(child, 0, [child])
    if len(nodes) > MAX_PARTS:
        raise ValueError(f'Das Modell braucht {len(nodes)} DW2-Teile (höchstens {MAX_PARTS}): zu viele Knochen '
                         'oder zu große Teilmeshes.')
    return nodes


def hierarchy(source):
    nodes = plan(source)
    return [n['src'] for n in nodes], [n['depth'] for n in nodes]


def limits_report(source):
    """What the conversion has to do to fit DW2's format limits (shown before export)."""
    nodes = plan(source)
    bones = source['bones']
    deep = sorted({n['src'] for n in nodes if len(n['chain']) > 1})
    split = sorted({n['src'] for n in nodes if len(bone_chunks(bones[n['src']])) > 1})
    return {'parts': len(nodes), 'max_parts': MAX_PARTS, 'flattened_bones': deep, 'split_bones': split,
            'max_depth': max(n['depth'] for n in nodes) + 1}


def source_matrices(source, motion):
    rows = np.asarray(source['motions'][motion]['frames'], dtype=float)
    if rows.ndim != 3 or rows.shape[1:] != (len(source['bones']), 16) or not np.isfinite(rows).all():
        raise ValueError('Ungültige DW3-Motionsdaten.')
    return rows.reshape(len(rows), len(source['bones']), 4, 4).transpose(0, 1, 3, 2)


def fit_scale(source, target, target_animation):
    from .native_gltf import Animation
    from .rig_animation import parents_from_depths, D
    model = NativeModel(target)
    depths = struct.unpack_from(f'<{model.bone_count}I', target, 12+12*model.bone_count)
    local = Animation(target_animation, model.bone_count).local_pose()
    parents = parents_from_depths(list(depths))
    world, points = [], []
    for i, part in enumerate(model.parts):
        world.append(local[i] if parents[i] < 0 else world[parents[i]] @ local[i])
        v = np.asarray([struct.unpack_from('<hhh', target, part.vertices+6+j*6) for j in range(part.vertex_count)]) @ D
        points.extend((np.c_[v, np.ones(len(v))] @ world[i].T)[:, :3])
    src_local = source_matrices(source, 0)[0]
    src_world, src_points = [], []
    for i, b in enumerate(source['bones']):
        src_world.append(src_local[i] if i == 0 else src_world[b['parent']] @ src_local[i])
        if b['vertices']:
            v = np.asarray(b['vertices'], dtype=float)
            src_points.extend((np.c_[v, np.ones(len(v))] @ src_world[i].T)[:, :3])
    # Same standing height as the replaced Digimon (axis 1 is up after D). The largest extent
    # mixed axes: a target long front-to-back (ears, tail) made an upright source far too tall.
    height = np.ptp(np.asarray(points)[:, 1])
    source_height = np.ptp(np.asarray(src_points)[:, 1])
    if height < 1e-6 or source_height < 1e-6:
        size = np.ptp(np.asarray(points), axis=0).max()
        return float(size / max(np.ptp(np.asarray(src_points), axis=0).max(), 1e-9))
    return float(height / source_height)


def atlas(source, folder, hd_scale=4):
    """All source pages in one atlas, with independent native 16-colour CLUTs.

    HD keeps the original RGBA pages; native fallback quantizes each page.
    The native last 32 rows hold 64 palettes, not drawable texture pixels.
    """
    names = source['images']
    if not 1 <= len(names) <= 64 or hd_scale not in (1,2,4,8,16):
        raise ValueError('Nicht unterstützte Anzahl Texturseiten / HD-Skalierung.')
    columns = math.ceil(math.sqrt(len(names)))
    rows = math.ceil(len(names)/columns)
    tw, th = 128//columns, 224//rows
    hd = Image.new('RGBA', (128*hd_scale, 256*hd_scale))
    indices = np.zeros((256,128), dtype=np.uint8)
    palettes, tiles = [], []
    for i, name in enumerate(names):
        path = (Path(folder)/name).resolve()
        if not path.is_relative_to(Path(folder).resolve()):
            raise ValueError('Texturpfad außerhalb des DW3-Modells.')
        with Image.open(path) as image:
            rgba = image.convert('RGBA')
        x, y = i % columns * tw, i//columns * th
        hd.paste(rgba.resize((tw*hd_scale, th*hd_scale), Image.Resampling.LANCZOS), (x*hd_scale,y*hd_scale))
        thumb = rgba.resize((tw,th), Image.Resampling.BOX)
        quant = thumb.convert('RGB').quantize(colors=15, dither=Image.Dither.NONE)
        rgb = (quant.getpalette() or []) + [0]*45
        pal = [0]
        for c in range(15):
            r,g,b = rgb[c*3:c*3+3]
            word = (r>>3) | ((g>>3)<<5) | ((b>>3)<<10)
            alpha=np.asarray(thumb)[:,:,3][np.asarray(quant)==c]
            if np.any((alpha>=128)&(alpha<255)):word|=0x8000
            pal.append(word or 0x8000)  # opaque black must not become transparent
        pixels = np.asarray(quant).astype(np.uint8)+1
        pixels[np.asarray(thumb)[:,:,3] < 128] = 0
        indices[y:y+th,x:x+tw] = pixels
        palettes.append(pal)
        tiles.append((x,y,tw,th,rgba.width,rgba.height))
    raw = bytearray((indices[:,0::2] | (indices[:,1::2]<<4)).tobytes())
    for i,pal in enumerate(palettes):
        struct.pack_into('<16H', raw, (224+i//2)*64 + (i%2)*32, *pal)
    tim = struct.pack('<II I4H', 16, 0, 12+len(raw), 0, 0, 32, 256) + raw
    return tim, hd, tiles


def encode_model(source, folder, scale=1., hd_scale=4):
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError('Ungültige Skalierung.')
    nodes = plan(source)
    order, depths = [x['src'] for x in nodes], [x['depth'] for x in nodes]
    tim, hd, tiles = atlas(source, folder, hd_scale)
    n = len(order)
    out = bytearray(12 + 16*n)
    out += bytes([255])+bytes(9)+bytes([255])+bytes(9)+bytes([255,0,0,0])
    def block(data):
        out.extend(bytes((-len(out))%4));at=len(out);out.extend(data);return at
    pointers = [[],[],[]]
    triangle_count = 0
    for node in nodes:
        bone = node['src']
        b = source['bones'][bone]
        part = bone_chunks(b)[node['chunk']]
        all_vertices = np.rint(np.asarray(b['vertices'], dtype=float)*scale).astype(np.int64)
        used = sorted({f['indices'][k] for f, c in part for k in c})
        if any(type(v) is not int or not 0 <= v < len(all_vertices) for v in used):
            raise ValueError('Ungültiger Vertexindex.')
        remap = {v: i for i, v in enumerate(used)}
        vertices = all_vertices[used] if used else all_vertices[:0]
        if len(vertices) > 256 or not len(vertices) or np.abs(vertices).max() > 32767:
            raise ValueError(f'DW3-Knochen {bone}: 1–256 Vertices im 16-Bit-Bereich erforderlich.')
        normals, normal_ids, prims = [], {}, [[],[]]
        for face, corners in part:
            img = face['image']
            if type(img) is not int or not 0 <= img < len(tiles):
                raise ValueError('Ungültige Materialzuordnung.')
            tx,ty,tw,th,iw,ih = tiles[img]
            ids = [remap[face['indices'][k]] for k in corners]
            v = vertices[ids]
            normal = np.cross(v[1]-v[0],v[2]-v[0]).astype(float)
            normal /= max(np.linalg.norm(normal),1e-9)
            normal = tuple(np.rint(normal*4096).astype(int))
            if normal not in normal_ids:
                normal_ids[normal] = len(normals);normals.append(normal)
            if len(normals) > 256:
                raise ValueError('Mehr als 256 Normalen in einem Knochen.')
            uv=[]
            for k in corners:
                u,v=face['uv'][k]
                if not 0 <= u < iw or not 0 <= v < ih:
                    raise ValueError('Wiederholende DW3-UVs müssen vor dem Import aufgeteilt werden.')
                uv.append((tx+round(u/max(iw-1,1)*(tw-1)),ty+round(v/max(ih-1,1)*(th-1))))
            clut = ((224+img//2)<<6) | (img%2)
            abr = face['abr']
            if type(abr) is not int or not 0 <= abr <= 4:
                raise ValueError('Ungültiger PS1-Mischmodus.')
            # Input faces are CCW in the exported GLB; DW2 stores reversed triangles.
            rev=(2,1,0)
            payload=bytes(ids[k] for k in rev)+bytes([normal_ids[normal]]*3)+bytes(c for k in rev for c in uv[k])+struct.pack('<HH',clut,((abr-1)<<5) if abr else 0)
            prims[0 if abr else 1].append(payload)
            triangle_count+=1
        if not normals or not any(prims):
            raise ValueError('DW3-Teilmodell ohne Geometrie.')
        pointers[0].append(block(struct.pack('<IH',len(vertices),0)+vertices.astype('<i2').tobytes()))
        pointers[1].append(block(struct.pack('<IH',len(normals),0)+np.asarray(normals,dtype='<i2').tobytes()))
        pointers[2].append(block(struct.pack('<3I',0,0,len(prims[0]))+b''.join(prims[0])+struct.pack('<I',len(prims[1]))+b''.join(prims[1])))
    for i,table in enumerate(pointers):
        struct.pack_into(f'<{n}I',out,12+i*n*4,*table)
    struct.pack_into(f'<{n}I',out,12+12*n,*depths)
    out.extend(bytes((-len(out))%4));tim_start=len(out);out.extend(tim)
    struct.pack_into('<III',out,0,tim_start,0,n)
    NativeModel(out)
    return bytes(out),hd,{'bones':n,'triangles':triangle_count,'scale':scale,'textures':len(tiles)}


def encode_animation(source, mapping, scale=1., loops=()):
    """mapping: native clip index -> DW3 motion index; no semantic labels inferred."""
    nodes=plan(source);order=[x['src'] for x in nodes];n=len(order)
    if not mapping or any(type(i)is not int or not 0<=i<10 for i in mapping):
        raise ValueError('DW2-Datei benötigt Clip-Indizes 0–9.')
    keys=[[] for _ in order];lookup=[{} for _ in order];clips={}
    for index,motion in sorted(mapping.items()):
        if type(motion)is not int or not 0<=motion<len(source['motions']):
            raise ValueError('Unbekannte DW3-Motion.')
        frames=source_matrices(source,motion)
        rows=[]
        for frame in frames:
            row=[]
            for b,src in enumerate(order):
                matrix=frame[nodes[b]['chain'][0]]
                for c in nodes[b]['chain'][1:]:
                    matrix=matrix@frame[c]
                values=np.rint(np.r_[matrix[:3,:3].ravel()*4096,matrix[:3,3]*scale]).astype(np.int64)
                if np.any(values < -32768) or np.any(values > 32767):
                    raise ValueError('Animationsmatrix außerhalb des 16-Bit-Bereichs.')
                raw=struct.pack('<12h',*values)
                if raw not in lookup[b]:
                    if len(keys[b])>=254:
                        raise ValueError(f'Knochen {src}: mehr als 254 unterschiedliche Posen in einer DW2-Datei. Weniger Motions zuweisen.')
                    lookup[b][raw]=len(keys[b]);keys[b].append(raw)
                row.append(lookup[b][raw])
            rows.append(bytes(row))
        clips[index]=b''.join(rows)+(b'\xfe\0\0' if index in loops else b'\xff\0\0')
    slots=max(mapping)+1
    out=bytearray(4+4*n+4*(slots+1))
    struct.pack_into('<I',out,4+4*n+4*slots,1)
    for b in range(n):
        struct.pack_into('<I',out,4+4*b,len(out));out.extend(b''.join(keys[b]))
    for index,data in clips.items():
        struct.pack_into('<I',out,4+4*n+4*index,len(out));out.extend(data)
    parse_anim_file(out,n)
    return bytes(out)


def fnv(data):
    value=0xcbf29ce484222325
    for b in data:
        value=((value^b)*0x100000001b3)&0xffffffffffffffff
    return value


def hd_name(model):
    m=NativeModel(model)
    # Gfx_LoadTexSlotImage uploads the complete 32x256-word TIM pixel block.
    flags=struct.unpack_from('<I',model,m.tim_start+4)[0]
    if flags&7:raise ValueError('HD-Modelltextur muss 4-Bit-TIM sein.')
    start=m.tim_start+8
    if flags&8:start+=struct.unpack_from('<I',model,start)[0]
    w,h=struct.unpack_from('<HH',model,start+8)
    if (w,h)!=(32,256):raise ValueError('HD-Modelltextur benötigt einen vollständigen 128×256-Slot.')
    raw=model[start+12:start+12+w*h*2]
    if len(raw)!=w*h*2:raise ValueError('TIM-Pixelblock abgeschnitten.')
    return f'{fnv(struct.pack("<2i",w,h)+raw):016x}_{w}x{h}_m0.png'
