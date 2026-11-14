"""Drive mednafen (PS1, OpenBIOS) under Xvfb with xdotool: key presses and snapshots.
    emu.py CUE OUTDIR SCRIPT   (SCRIPT: lines 'wait S', 'key K [hold_s]', 'snap', 'ff on|off', 'repeat N' ... 'end')"""
import os, subprocess, sys, time, shutil, glob
cue, out, script = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
snaps = os.path.expanduser('~/.mednafen/snaps')
shutil.rmtree(snaps, ignore_errors=True); os.makedirs(snaps)
env = dict(os.environ, DISPLAY=':99', SDL_AUDIODRIVER='dummy')
xv = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1024x768x24'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)
med = subprocess.Popen(['/usr/games/mednafen', '-force_module', 'psx', '-sound', '0', '-video.driver', 'softfb',
                        '-psx.bios_na', 'scph5501.bin', '-psx.xscale', '2', '-psx.yscale', '2', cue],
                       env=env, stdout=open(os.path.join(out, 'mednafen.log'), 'w'), stderr=subprocess.STDOUT)
time.sleep(4)
win = subprocess.run(['xdotool', 'search', '--name', 'Mednafen|mednafen|Digimon|DIGIMON|.'], env=env, capture_output=True, text=True).stdout.split()
print('windows', win[:3], flush=True)
def x(*a): subprocess.run(['xdotool', *a], env=env)
if win: x('windowactivate', '--sync', win[-1])
KEYS = {'up': 'w', 'down': 's', 'left': 'a', 'right': 'd', 'cross': 'KP_2', 'circle': 'KP_6', 'square': 'KP_4',
        'triangle': 'KP_8', 'start': 'Return', '2up': 'i', '2down': 'k', '2left': 'j', '2right': 'l', '2cross': 'm', '2circle': 'n', '2start': 'p', '2triangle': 'y', '2square': 'u', 'save': 'F5', 'load': 'F7'}
n = 0
def snap(tag):
    global n
    before = set(glob.glob(snaps + '/*.png'))
    x('key', 'F9'); time.sleep(0.6)
    new = sorted(set(glob.glob(snaps + '/*.png')) - before)
    if new:
        shutil.copy(new[-1], os.path.join(out, f'{n:03d}_{tag}.png')); n += 1
lines = [l.split() for l in open(script) if l.strip() and not l.startswith('#')]
def run(block):
    i = 0
    while i < len(block):
        c = block[i]
        if c[0] == 'wait': time.sleep(float(c[1]))
        elif c[0] == 'key':
            k = KEYS.get(c[1], c[1]); hold = float(c[2]) if len(c) > 2 else 0.12
            x('keydown', k); time.sleep(hold); x('keyup', k); time.sleep(0.08)
        elif c[0] == 'snap': snap(c[1] if len(c) > 1 else 's')
        elif c[0] == 'quit':
            x('key', 'Escape')
            try: med.wait(30)
            except Exception: pass
        elif c[0] == 'ff': x('keydown' if c[1] == 'on' else 'keyup', 'grave')
        elif c[0] == 'repeat':
            depth, j = 1, i + 1
            while depth:
                depth += lines_kind(block[j]); j += 1
            for _ in range(int(c[1])): run(block[i + 1:j - 1])
            i = j - 1
        i += 1
def lines_kind(c): return 1 if c[0] == 'repeat' else -1 if c[0] == 'end' else 0
run(lines)
med.terminate(); time.sleep(1); xv.terminate()
print('snaps', n)
