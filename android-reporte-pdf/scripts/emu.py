#!/usr/bin/env python3
"""Control del emulador por resource-id (sin coordenadas a mano).
  emu.py dump                 lista los elementos visibles: id | clase | texto
  emu.py tap <id>             toca el elemento con ese resource-id (sin el prefijo paquete:id/)
  emu.py taptext <texto>      toca el elemento cuyo texto coincide
  emu.py type <id> <texto>    toca el campo y escribe
  emu.py hidekb               oculta el teclado
  emu.py back                 botón atrás
  emu.py shot <archivo.png>   captura de pantalla
  emu.py wait <segundos>
Se pueden encadenar con '+':  emu.py type edt1 25 + type edt2 17 + hidekb + tap btnCalcular + shot 01.png
"""
import os, re, subprocess, sys, time
ADB = os.path.join(os.environ.get('ANDROID_HOME', os.path.expanduser('~/Android/Sdk')), 'platform-tools', 'adb')

def sh(*a):
    return subprocess.run([ADB, 'shell', *a], capture_output=True, text=True).stdout

def nodes():
    for _ in range(6):
        x = subprocess.run([ADB, 'exec-out', 'uiautomator', 'dump', '/dev/tty'], capture_output=True, text=True).stdout
        if '<node' in x:
            out = []
            for n in re.findall(r'<node [^>]*>', x):
                g = lambda k: (re.search(k + r'="([^"]*)"', n) or [None, ''])[1]
                b = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', n)
                if b:
                    a, c, d, e = map(int, b.groups())
                    out.append(dict(id=g('resource-id').split('/')[-1], cls=g('class').split('.')[-1], text=g(' text'), xy=((a + d) // 2, (c + e) // 2)))
            return out
        time.sleep(1)
    sys.exit('No se pudo leer la pantalla (uiautomator dump)')

def find(key, val):
    for n in nodes():
        if n[key] == val:
            return n['xy']
    sys.exit(f'No encontrado {key}={val}. Usa "emu.py dump" para ver los ids.')

def tap(xy):
    sh('input', 'tap', str(xy[0]), str(xy[1])); time.sleep(0.8)

def run(cmd, args):
    if cmd == 'dump':
        for n in nodes():
            if n['id'] or n['text']:
                print(f"{n['id'] or '-':28} {n['cls']:18} {n['text']}")
    elif cmd == 'tap': tap(find('id', args[0]))
    elif cmd == 'taptext': tap(find('text', args[0]))
    elif cmd == 'type':
        tap(find('id', args[0]))
        sh('input', 'text', args[1].replace(' ', '%s')); time.sleep(0.4)
    elif cmd == 'hidekb': sh('input', 'keyevent', '111'); time.sleep(0.8)
    elif cmd == 'back': sh('input', 'keyevent', '4'); time.sleep(0.8)
    elif cmd == 'wait': time.sleep(float(args[0]))
    elif cmd == 'shot':
        time.sleep(0.6)
        data = subprocess.run([ADB, 'exec-out', 'screencap', '-p'], capture_output=True).stdout
        os.makedirs(os.path.dirname(os.path.abspath(args[0])), exist_ok=True)
        open(args[0], 'wb').write(data)
    else:
        sys.exit(__doc__)

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    step = []
    for a in sys.argv[1:] + ['+']:
        if a == '+':
            if step: run(step[0], step[1:])
            step = []
        else:
            step.append(a)
