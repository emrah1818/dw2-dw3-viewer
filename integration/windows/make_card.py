import sys, os
sys.path.insert(0, '/home/claude/dw2-pc-port/tools/autoplay')
from to_city import to_city
from save_test import save_menu
W = '/home/claude/work/win'
g, _ = to_city(W + '/port/dw2', W + '/port/dw2.pak', W + '/card', extra=('--cheats',))
for d in (84, 131, 48):
    g.devedit('adddigi=%d,30,99,900,900,300,300,300' % d); g.run(10)
ro = lambda i: g.peek('Save_GameState', 0xE4 + i * 0x5C, 2)
pos = {84: 3, 131: 4, 48: 5}
for i in range(0x24):
    r = ro(i)
    if r[0]:
        g.poke('Save_GameState', 0xE4 + i * 0x5C, bytes([pos.get(r[1], 1)]))
for i in range(3):
    raw = g.peek('Save_GameState', 0xE4 + i * 0x5C, 0x5C)
    print('skills before', i, raw[1], list(raw[0x40:0x4C]) if len(raw) > 0x4C else raw.hex())
    g.devedit('skill=%d,1,18' % i); g.run(6)
g.run(30)
print('roster', [ro(i).hex() for i in range(6)])
save_menu(g)
g.close()
print(os.path.getsize(W + '/card/saves/card1.mcd'))
