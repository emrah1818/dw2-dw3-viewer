"""Mednafen PS1 save state: show game mode and party, optionally set the next game mode
(like the port's dev edit warp=). Addresses from the decompilation (configs/USA/sym.main.txt):
Sys_State 0x8005F770 (+0x18 gameMode, +0x1C nextGameMode, +0x24 modeArg), Save_GameState
0x8005E620 (+0xE4 roster, 0x5C per Digimon). Test set-up only, like --cheats in the port.

    stpatch.py STATE.mc0 [NEXT_MODE]     e.g. 0x32F Digi-Lab, 0x32D city map"""
import gzip, struct, sys
p = sys.argv[1]
d = bytearray(gzip.decompress(open(p, 'rb').read()))
i = d.find(b'MainRAM')
ram = i + d[i - 1] + 4
S, gs = ram + 0x5F770, ram + 0x5E620 + 0xE4
print('mode', [hex(v) for v in struct.unpack_from('<4i', d, S + 0x18)],
      'roster', [(d[gs + k * 0x5C], d[gs + k * 0x5C + 1], d[gs + k * 0x5C + 0xD]) for k in range(4)])
if len(sys.argv) > 2:
    struct.pack_into('<i', d, S + 0x1C, int(sys.argv[2], 0))
    struct.pack_into('<i', d, S + 0x24, 0)
    open(p, 'wb').write(gzip.compress(bytes(d)))
    print('next mode', sys.argv[2])
