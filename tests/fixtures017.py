"""Self-made test data in the game's table formats (no game data). Used by the 0.17b tests.

Each builder follows the layout documented in the module it tests (domains.py, battle_skills.py,
digimon_names.py, evolution.py). Values and texts are invented.
"""
import hashlib
import struct
from pathlib import Path

from dw2studio.pak import MAGIC
from dw2studio.core.digimon_names import ENCODE

WAZADATA, DIGIMNDT, ENEMYSET, MODELDT0, DOMAINS = 603, 3180, 3183, 3257, 0xE20
DUNGEON = 0xCE1
DIGIMON = {3: 'Testmon', 5: 'Bigmon', 6: 'Hugemon', 84: 'Smallmon', 131: 'Ratmon'}


def text(s):
    return bytes(ENCODE[c] for c in s) + b'\xff'


def wazadata(techniques=((1, 'Spark', 5, 30), (2, 'Bubble', 3, 20), (4, 'Flame Ball', 6, 30))):
    texts = bytearray()
    pointers = []
    base = 8
    for _, name, _, _ in techniques:
        pointers.append((base + len(texts), base + len(texts) + len(text(name))))
        texts += text(name) + text('Desc ' + name)
    texts += bytes(-(len(texts) + base) % 4)
    start = base + len(texts)
    out = bytearray(struct.pack('<II', start, 0)) + texts
    for (ident, _, mp, power), (name_at, desc_at) in zip(techniques, pointers):
        row = bytearray(68)
        struct.pack_into('<I', row, 0, ident | (1 << 16) | (2 << 24))   # cast 1 (G), element 2
        row[4] = mp
        struct.pack_into('<h', row, 8, power)
        struct.pack_into('<II', row, 0x24, name_at, desc_at)
        struct.pack_into('<6h', row, 0x2C, 7, 8, 9, 10, 11, 12)          # effect file ids, copied verbatim
        out += row
    out += bytes(68)
    return bytes(out)


def digimndt(rows=((3, 1, 0, [(0, 5), (10, 6)]), (5, 2, 1, []), (6, 4, 2, []), (84, 1, 0, []), (131, 2, 0, []))):
    out = bytearray()
    for ident, skill, rank, evo in rows:
        r = bytearray(18)
        struct.pack_into('<h', r, 0, ident)
        r[2] = skill
        r[4] = (rank << 4) | 1
        for i, (dp, target) in enumerate(evo):
            r[8 + i], r[13 + i] = dp, target
        r[17] = 0xA5                                                   # unknown byte, must survive
        out += r
    return bytes(out + bytes(18))


def enemyset(groups=((31, 131, [(131, 3, [1, 0, 0])]), (32, 84, [(84, 4, [2, 0, 0]), (131, 5, [1, 2, 0])]))):
    out = bytearray()
    for set_id, map_digimon, members in groups:
        g = bytearray(100)
        struct.pack_into('<I', g, 0, set_id | (6 << 8) | (1 << 12))
        struct.pack_into('<h', g, 2, map_digimon)
        struct.pack_into('<I', g, 4, 3 | (1 << 8))
        struct.pack_into('<h', g, 6, 10)
        for slot, (digimon, level, skills) in enumerate(members):
            row = 8 + 30 * slot
            struct.pack_into('<HHH', g, row, digimon, 40 + level, 20)
            g[row + 10], g[row + 11] = level, 30
            struct.pack_into('<H', g, row + 12, 25)
            g[row + 14] = 12
            g[row + 15:row + 18] = bytes(skills)
            g[row + 18:row + 21] = bytes([0, 1, 7])                   # rule: always use slot 1
            g[row + 6:row + 10] = b'\x11\x22\x33\x44'                  # unknown bytes, must survive
        out += g
    return bytes(out + bytes(100))


def modeldt(digimon=DIGIMON, cameras=None):
    cameras = cameras or {}
    pool = bytearray()
    pointers = {}
    for ident, name in digimon.items():
        pointers[ident] = 8 + len(pool)
        pool += text(name)
        pool += bytes(-len(pool) % 4)
    pool_end = 8 + len(pool)
    records_start = pool_end
    out = bytearray(struct.pack('<II', records_start, pool_end)) + pool
    for ident in digimon:
        r = bytearray(40)
        struct.pack_into('<IH', r, 0, pointers[ident], ident << 1)
        struct.pack_into('<h', r, 6, 2000 + ident)                    # model file id (not resolved here)
        field, hit = cameras.get(ident, (1190, 601))
        struct.pack_into('<hh', r, 0x1E, field, hit)
        out += r
    return bytes(out + bytes(40))


def domains_archive(rows=(DUNGEON,)):
    count = 11
    offsets = [4 * count + 4 * i for i in range(count)]
    table = bytearray()
    for fid in rows:
        r = bytearray(0x14)
        struct.pack_into('<h', r, 0, fid)
        table += r
    table += bytes(0x14)
    out = bytearray(4 * count + 4 * count)
    offsets[0xA] = len(out)
    out += table
    for i, o in enumerate(offsets):
        struct.pack_into('<I', out, 4 * i, o)
    return bytes(out)


def dungeon(floors=(('Test Domain1F', [0, 31, 31, 32, 0]), ('Test Domain2F', [0, 32, 0, 0, 0]))):
    head = 4 * (len(floors) + 1)
    out = bytearray(head)
    for k, (name, sets) in enumerate(floors):
        at = len(out)
        struct.pack_into('<I', out, 4 * k, at)
        floor = bytearray(0x84)
        floor[0x2F:0x34] = bytes(sets)
        out += floor
        name_at = len(out)
        out += text(name)
        out += bytes(-len(out) % 4)
        struct.pack_into('<I', out, at, name_at)
    return bytes(out)


def make_pak(folder, files=None):
    """A DW2PAK v1 with the given {file id: bytes}; every other id is absent."""
    files = files or {WAZADATA: wazadata(), DIGIMNDT: digimndt(), ENEMYSET: enemyset(),
                      MODELDT0: modeldt(), DOMAINS: domains_archive(), DUNGEON: dungeon()}
    ids = sorted(files)
    header_size, entry_size = 80, 64
    offset = header_size + entry_size * len(ids)
    offset += -offset % 2048
    blobs, index, lba = [], [], 1000
    for fid in ids:
        data = files[fid] + bytes(-len(files[fid]) % 2048)
        sectors = len(data) // 2048
        index.append(struct.pack('<4I2Q', fid, lba, sectors, 0, offset, len(data)) + hashlib.sha256(data).digest())
        blobs.append((offset, data))
        offset += len(data)
        lba += sectors
    out = bytearray(offset)
    struct.pack_into('<8s6I', out, 0, MAGIC, 1, header_size, len(ids), header_size, entry_size, 0)
    for i, row in enumerate(index):
        out[header_size + i * entry_size:header_size + (i + 1) * entry_size] = row
    for at, data in blobs:
        out[at:at + len(data)] = data
    path = Path(folder) / 'dw2.pak'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(out)
    return path


def open_session(folder, files=None):
    from dw2studio.pak_workspace import PakSession
    path = make_pak(folder, files)
    session = PakSession(path)
    return session, list(session.disc.entries), path
