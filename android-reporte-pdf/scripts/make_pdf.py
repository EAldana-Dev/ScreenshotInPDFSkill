#!/usr/bin/env python3
"""Genera el PDF de reporte: portada + capturas del código + capturas de ejecución.
Uso:
  make_pdf.py --project <ruta> --shots <dir> --out <archivo.pdf> --author "Valdez Aldana" [--title T] [--subtitle S]
<dir>/captions.json: [{"file":"01_suma.png","caption":"Suma: 25 + 17 = 42","group":"Pruebas de ejecución"}, ...]
(el orden de la lista es el orden en el PDF; cada 'group' distinto abre una sección nueva).
Solo necesita Pillow y Pygments."""
import argparse, glob, io, json, os
from PIL import Image, ImageDraw, ImageFont
from pygments import highlight
from pygments.lexers import get_lexer_for_filename
from pygments.formatters import ImageFormatter

ap = argparse.ArgumentParser()
ap.add_argument('--project', required=True); ap.add_argument('--shots', required=True)
ap.add_argument('--out', required=True); ap.add_argument('--author', required=True)
ap.add_argument('--title'); ap.add_argument('--subtitle', default='')
a = ap.parse_args()
PROJ = os.path.abspath(os.path.expanduser(a.project)); MAIN = os.path.join(PROJ, 'app/src/main')
title = a.title or os.path.basename(PROJ)
W, H, M = 1654, 2339, 80   # A4 a 200 dpi
F = '/usr/share/fonts/truetype/dejavu/'
font = lambda sz, b=False: ImageFont.truetype(F + ('DejaVuSans-Bold.ttf' if b else 'DejaVuSans.ttf'), sz)
pages = []; cur = None; y = 0

def newpage():
    global cur, y
    cur = Image.new('RGB', (W, H), 'white'); pages.append(cur); y = M

def text(t, sz, b=False, color='#111', gap=20, center=False):
    global y
    d = ImageDraw.Draw(cur); f = font(sz, b)
    x = M if not center else (W - d.textlength(t, font=f)) // 2
    d.text((x, y), t, font=f, fill=color); y += int(sz * 1.3) + gap

def code_img(path):
    src = open(path, encoding='utf-8').read().rstrip('\n') + '\n'
    png = highlight(src, get_lexer_for_filename(path), ImageFormatter(
        font_name='DejaVu Sans Mono', font_size=24, style='monokai', line_numbers=True,
        line_number_bg='#272822', line_number_fg='#75715e', line_number_separator=False, image_pad=24, line_pad=6))
    im = Image.open(io.BytesIO(png)).convert('RGB')
    bar = 56; out = Image.new('RGB', (max(im.width, 700), im.height + bar), '#272822')
    d = ImageDraw.Draw(out); d.rectangle([0, 0, out.width, bar], fill='#1e1f1c')
    for i, c in enumerate(['#ff5f56', '#ffbd2e', '#27c93f']): d.ellipse([20 + i * 34, 18, 40 + i * 34, 38], fill=c)
    d.text((140, 14), os.path.basename(path), font=ImageFont.truetype(F + 'DejaVuSansMono.ttf', 22), fill='#ccc')
    out.paste(im, (0, bar)); return out

def place(im, label):
    global y
    maxh = H - 2 * M - 70
    while im.height * min(1, (W - 2 * M) / im.width) > maxh * 1.6:   # archivo muy largo: partir en trozos
        cut = int(maxh * 1.3 / min(1, (W - 2 * M) / im.width))
        place(im.crop((0, 0, im.width, cut)), label); im = im.crop((0, cut, im.width, im.height)); label += ' (cont.)'
    s = min(1, (W - 2 * M) / im.width)
    if y + int(im.height * s) + 70 > H - M:
        newpage(); s = min(s, maxh / im.height)
    text(label, 26, True, gap=10)
    if s < 1: im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    cur.paste(im, (M, y)); y += im.height + 50

# fuentes: MainActivity primero, luego el resto; después layouts y manifest
srcs = sorted(glob.glob(MAIN + '/java/**/*.kt', recursive=True) + glob.glob(MAIN + '/java/**/*.java', recursive=True) +
              glob.glob(MAIN + '/kotlin/**/*.kt', recursive=True),
              key=lambda p: (0 if 'MainActivity' in p else 1, -os.path.getsize(p)))
xmls = sorted(glob.glob(MAIN + '/res/layout*/*.xml')) + sorted(glob.glob(MAIN + '/res/menu/*.xml')) + \
       sorted(glob.glob(MAIN + '/res/navigation/*.xml')) + [MAIN + '/AndroidManifest.xml']
langs = {'.kt': 'Kotlin', '.java': 'Java'}
lang = ' y '.join(sorted({langs[os.path.splitext(p)[1]] for p in srcs})) or 'código'

newpage(); y = 700
text(title, 90, True, center=True, gap=30)
if a.subtitle: text(a.subtitle, 40, center=True, color='#444', gap=20)
y += 100
text(a.author, 44, True, center=True, gap=20)
text(f'Código fuente ({lang} y XML) y pruebas de ejecución', 30, center=True, color='#555')

sec = 1
newpage(); text(f'{sec}. Código fuente ({lang})', 44, True, gap=30)
for p in srcs: place(code_img(p), os.path.basename(p))
sec += 1; newpage(); text(f'{sec}. Layouts y manifest (XML)', 44, True, gap=30)
for p in xmls: place(code_img(p), os.path.relpath(p, MAIN))

caps = json.load(open(os.path.join(a.shots, 'captions.json'), encoding='utf-8'))
groups = []
for c in caps:
    g = c.get('group', 'Pruebas de ejecución en el emulador')
    if not groups or groups[-1][0] != g: groups.append((g, []))
    groups[-1][1].append(c)
sw, sh = 450, 1000; gapx = (W - 2 * M - 3 * sw) // 2
for g, items in groups:
    sec += 1
    for i, c in enumerate(items):
        if i % 6 == 0:
            newpage(); text(f'{sec}. {g}' + (' (cont.)' if i else ''), 44, True, gap=30); top = y
        col, row = i % 3, (i % 6) // 3
        x, yy = M + col * (sw + gapx), top + row * (sh + 90)
        im = Image.open(os.path.join(a.shots, c['file'])).convert('RGB')
        im.thumbnail((sw, sh), Image.LANCZOS)
        cur.paste(im, (x + (sw - im.width) // 2, yy)); d = ImageDraw.Draw(cur)
        d.rectangle([x + (sw - im.width) // 2, yy, x + (sw + im.width) // 2, yy + im.height], outline='#888', width=2)
        f = font(22); cap = c.get('caption', '')
        d.text((x + (sw - d.textlength(cap, font=f)) // 2, yy + sh + 12), cap, font=f, fill='#222')

out = os.path.abspath(os.path.expanduser(a.out))
pages[0].save(out, save_all=True, append_images=pages[1:], resolution=200)
prev = os.path.join(a.shots, '_preview.png')
sheet = Image.new('RGB', (300 * len(pages), 424), 'gray')
for i, p in enumerate(pages): sheet.paste(p.resize((296, 420)), (300 * i + 2, 2))
sheet.save(prev)
print(f'{len(pages)} páginas -> {out}\nVista previa: {prev}\nLenguaje detectado: {lang}')
