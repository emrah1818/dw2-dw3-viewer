"""Windows test set: Studio mod (3 DW3 imports, HD 2048x4096) + save card with them in the party."""
import os, sys, shutil, json
sys.path.insert(0, '/home/claude/viewer-main')
import android_api as api
W = '/home/claude/work/win'
PAK = '/mnt/user-data/uploads/DW2-PC/dw2.pak'
DW3 = '/home/claude/data/dw3/Digimon World 3 (USA).bin'
port = os.path.join(W, 'port'); shutil.rmtree(port, ignore_errors=True); os.makedirs(port)
shutil.copy2('/home/claude/work/port_v1/dw2', port); shutil.copy2('/home/claude/work/port_v1/dw2_mod_api.json', port)
for n, s in (('dw2.pak', PAK), ('dw2.pak.slus', PAK + '.slus')):
    os.symlink(s, os.path.join(port, n))
api.configure(os.path.join(W, 'studio'), ''); api.open_image(PAK)
m = {x['name']: x['id'] for x in api.open_dw3(DW3)['models']}
jobs = api.dw3_batch_apply([{'source': m['M366GIRU'], 'target': 84, 'name': 'Guilmon', 'hd': 16},
                            {'source': m['M368MGRW'], 'target': 131, 'name': 'MegaloGrowmon', 'hd': 16},
                            {'source': m['M367GRAW'], 'target': 48, 'name': 'Growlmon', 'hd': 16}])['jobs']
print([(j['target'], j.get('hd_size'), j['triangles'], (j.get('battle_camera') or {}).get('setting')) for j in jobs])
c = api.mod_check(port); print('check', c['ok'], c['errors'][:3], len(c['files']))
print('export', api.mod_export(port)['count'])
print(os.listdir(os.path.join(port, 'Mods')))
