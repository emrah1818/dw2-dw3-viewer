"""Rebuild a bootable DW2 (USA) 2352-byte BIN from dw2.pak + dw2.pak.slus for emulator tests.
Every game file sits at its original LBA (the game reads by Cd_FileLba). ISO9660 holds
SYSTEM.CNF and SLUS_011.93 only. Local test aid; the output stays in the workspace."""
import struct, sys, hashlib
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from dw2studio.core.psx_patch import regenerate_form1
pak, slus, out = sys.argv[1:4]
f = open(pak, 'rb'); h = f.read(0x50)
n, ioff = struct.unpack_from('<II', h, 0x10)
f.seek(ioff)
rows = [struct.unpack_from('<IIIIQQ', f.read(0x40), 0) for _ in range(n)]
exe = open(slus, 'rb').read()
end = max(r[1] + r[2] for r in rows if r[2])
used = sorted((r[1], r[1] + r[2]) for r in rows if r[2])
print('files', n, 'first lba', used[0][0], 'end', end, 'exe bytes', len(exe))
def bcd(v): return (v // 10) << 4 | v % 10
def header(lba, mode=2):
    a = lba + 150
    return bytes([0] + [0xFF] * 10 + [0]) + bytes([bcd(a // 4500), bcd(a // 75 % 60), bcd(a % 75), mode])
def form1(lba, data, sub=0x08):
    raw = bytearray(header(lba)) + bytes([0, 0, sub, 0] * 2) + data.ljust(2048, b'\0') + bytes(280)
    return regenerate_form1(raw)
exe_sectors = (len(exe) + 2047) // 2048
cnf = b'BOOT = cdrom:\\SLUS_011.93;1\r\nTCB = 4\r\nEVENT = 10\r\nSTACK = 801FFF00\r\n'
# ISO tree: root (SYSTEM.CNF, SLUS_011.93, PAK/), PAK/ lists every game file by its Studio name
import json
names = json.loads(open('/home/claude/viewer-main/data/native_file_ids_us.json').read())
from dw2studio.core.digimon_names import FILE_INDEX
from dw2studio.core.battle_skills import FILE_INDEX as B
names.update(FILE_INDEX); names.update(B)
by_id = {v: k for k, v in names.items()}
root_lba, cnf_lba, pak_lba = 22, 23, 24
files = sorted((by_id.get(r[0], f'INDEX_{r[0]:04X}.BIN'), r) for r in rows if r[2])
exe_lba = end
end = exe_lba + exe_sectors
img = bytearray(end * 2352)
def put(lba, sector): img[lba * 2352:(lba + 1) * 2352] = sector
for lba in range(end): put(lba, form1(lba, b''))
def dt(): return bytes([99, 1, 1, 0, 0, 0, 0])
def rec(name, lba, size, flags):
    name = name.encode()
    r = struct.pack('<BBII', 0, 0, lba, 0)[:2] + struct.pack('<I', lba) + struct.pack('>I', lba) + struct.pack('<I', size) + struct.pack('>I', size) + dt() + bytes([flags, 0, 0]) + struct.pack('<H', 1) + struct.pack('>H', 1) + bytes([len(name)]) + name
    if len(r) % 2: r += b'\0'
    return bytes([len(r)]) + r[1:]
# PAK directory sectors (records never cross a sector)
recs = [rec('\0', pak_lba, 0, 2), rec('\1', root_lba, 2048, 2)] + [rec(n + ';1', r[1], r[2] * 2048, 0) for n, r in files]
secs, cur = [], b''
for r_ in recs:
    if len(cur) + len(r_) > 2048:
        secs.append(cur); cur = b''
    cur += r_
secs.append(cur)
pak_size = len(secs) * 2048
assert pak_lba + len(secs) <= used[0][0], 'PAK directory does not fit before the first file'
recs[0] = rec('\0', pak_lba, pak_size, 2)
secs, cur = [], b''
for r_ in recs:
    if len(cur) + len(r_) > 2048:
        secs.append(cur); cur = b''
    cur += r_
secs.append(cur)
root = rec('\0', root_lba, 2048, 2) + rec('\1', root_lba, 2048, 2) + rec('PAK', pak_lba, pak_size, 2) + rec('SLUS_011.93;1', exe_lba, len(exe), 0) + rec('SYSTEM.CNF;1', cnf_lba, len(cnf), 0)
pvd = bytearray(2048)
pvd[0:8] = b'\x01CD001\x01'
pvd[8:40] = b' ' * 32; pvd[40:72] = b'SLUS_01193'.ljust(32)
struct.pack_into('<I', pvd, 80, end); struct.pack_into('>I', pvd, 84, end)
struct.pack_into('<H', pvd, 120, 1); struct.pack_into('>H', pvd, 122, 1)
struct.pack_into('<H', pvd, 124, 1); struct.pack_into('>H', pvd, 126, 1)
struct.pack_into('<H', pvd, 128, 2048); struct.pack_into('>H', pvd, 130, 2048)
struct.pack_into('<I', pvd, 132, 10); struct.pack_into('>I', pvd, 136, 10)
struct.pack_into('<I', pvd, 140, 18); struct.pack_into('>I', pvd, 148, 19)
pvd[156:156 + 34] = rec('\0', root_lba, 2048, 2)
pvd[881] = 1
put(16, form1(16, bytes(pvd), 0x89))
put(17, form1(17, b'\xffCD001\x01', 0x89))
pt = bytes([1, 0]) + struct.pack('<I', root_lba) + struct.pack('<H', 1) + b'\0\0' + bytes([3, 0]) + struct.pack('<I', pak_lba) + struct.pack('<H', 1) + b'PAK\0'
put(18, form1(18, pt)); put(19, form1(19, bytes([1, 0]) + struct.pack('>I', root_lba) + struct.pack('>H', 1) + b'\0\0' + bytes([3, 0]) + struct.pack('>I', pak_lba) + struct.pack('>H', 1) + b'PAK\0'))
struct.pack_into('<I', pvd, 132, 20); struct.pack_into('>I', pvd, 136, 20)
put(16, form1(16, bytes(pvd), 0x89))
put(root_lba, form1(root_lba, root, 0x89)); put(cnf_lba, form1(cnf_lba, cnf, 0x89))
for k, sec in enumerate(secs):
    put(pak_lba + k, form1(pak_lba + k, sec, 0x89 if k == len(secs) - 1 else 0x08))
for k in range(exe_sectors):
    put(exe_lba + k, form1(exe_lba + k, exe[k * 2048:(k + 1) * 2048], 0x89 if k == exe_sectors - 1 else 0x08))
for fid, lba, sec, fmt, off, size in rows:
    if not sec: continue
    f.seek(off); data = f.read(size)
    for k in range(sec):
        if fmt == 0:
            chunk = data[k * 2048:(k + 1) * 2048]
            put(lba + k, form1(lba + k, chunk, 0x89 if k == sec - 1 else 0x08))
        else:
            body = data[k * 2336:(k + 1) * 2336]
            put(lba + k, header(lba + k) + body)
open(out, 'wb').write(img)
open(out[:-4] + '.cue', 'w').write(f'FILE "{out.split("/")[-1]}" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n')
print('written', len(img))
