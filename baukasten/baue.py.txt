# Baut einen Slideshow-Beitrag.  Aufruf:  python3 baue.py posts/<id>
# Erwartet posts/<id>/post.html (jede Folie ist ein <section class="slide">, 1080x1920).
# Schreibt nach posts/<id>/out/: bild-01.jpg ..., vorschau.mp4 (2,5 s je Bild, ohne Ton), _bogen.jpg (Übersicht).
# Meldet Elemente in .safe, die den sicheren Bereich verlassen (x 68-932, y 198-1500).
import sys, os, pathlib, subprocess
from playwright.sync_api import sync_playwright
from PIL import Image
d = pathlib.Path(sys.argv[1]).resolve(); out = d / 'out'; out.mkdir(exist_ok=True)
for f in out.glob('bild-*.jpg'): f.unlink()
exe = '/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe)
    pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    fehl = []
    pg.on('requestfailed', lambda r: fehl.append(r.url))
    pg.goto((d / 'post.html').as_uri()); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(500)
    n = pg.locator('.slide').count(); warn = []
    for i in range(n):
        s = pg.locator('.slide').nth(i); s.scroll_into_view_if_needed()
        s.screenshot(path=str(out / f'_s{i+1:02d}.png'))
        Image.open(out / f'_s{i+1:02d}.png').convert('RGB').save(out / f'bild-{i+1:02d}.jpg', quality=93, subsampling=0)
        os.remove(out / f'_s{i+1:02d}.png')
        bad = s.evaluate('''el=>{const r0=el.getBoundingClientRect();const o=[];el.querySelectorAll('.safe *').forEach(e=>{const r=e.getBoundingClientRect();if(!r.width||!r.height)return;const x0=r.left-r0.left,x1=r.right-r0.left,y0=r.top-r0.top,y1=r.bottom-r0.top;if(x0<68||x1>932||y0<198||y1>1500)o.push((e.className||e.tagName)+'')});return [...new Set(o)].slice(0,6)}''')
        if bad: warn.append(f'{i+1}: ' + ', '.join(bad))
    b.close()
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '1/2.5', '-i', str(out / 'bild-%02d.jpg'), '-vf', 'fps=30,format=yuv420p', '-c:v', 'libx264', '-crf', '18', '-movflags', '+faststart', str(out / 'vorschau.mp4')], check=True)
ims = [Image.open(out / f'bild-{i+1:02d}.jpg').resize((378, 672)) for i in range(n)]
sh = Image.new('RGB', (min(n, 4) * 384, ((n + 3) // 4) * 678), '#222')
for i, im in enumerate(ims): sh.paste(im, ((i % 4) * 384, (i // 4) * 678))
sh.save(out / '_bogen.jpg', quality=86)
print(n, 'Bilder |', 'fehlende Dateien:', fehl or 'keine', '| ausserhalb des sicheren Bereichs:', warn or 'nichts')
