# Baut ein 9:16-Kurzvideo.  Aufruf:  python3 baue_video.py posts/<id>
# Erwartet posts/<id>/post.html mit <div id="stage" data-dauer="SEK"> und eingebundenem ../../video.css + ../../video.js.
# Schreibt nach posts/<id>/out/: video.mp4 (1080x1920, 30 fps, H.264 + stille AAC-Tonspur), cover.jpg (Bild bei 0,6 s),
# _bogen.jpg (ein Bild pro Sekunde zum Ansehen). Prüft, ob Text in .safe den sicheren Bereich verlässt
# (x 60–920, y 150–1420; TikTok-/Insta-Knöpfe rechts, Caption unten). Elemente mit class="frei" sind ausgenommen.
import sys, os, pathlib, subprocess, shutil, time
from playwright.sync_api import sync_playwright
from PIL import Image

FPS = 30
d = pathlib.Path(sys.argv[1]).resolve(); out = d / 'out'; out.mkdir(exist_ok=True)
fr = out / '_frames'; shutil.rmtree(fr, ignore_errors=True); fr.mkdir()
exe = '/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None
PRUEF = '''t=>{window.renderAt(t);const S=document.getElementById('stage').getBoundingClientRect();const o=[];
document.querySelectorAll('.szene').forEach(sz=>{if(sz.style.display==='none'||sz.style.transform||+sz.style.opacity<1)return;
 sz.querySelectorAll('.safe *').forEach(e=>{if(e.closest('.frei')||e.closest('.chat .verlauf'))return;
  let op=1,x=e;while(x&&x!==document.body){const cs=getComputedStyle(x);if(cs.display==='none'||cs.visibility==='hidden'){op=0;break}op*=+cs.opacity;x=x.parentElement}
  if(op<0.5)return;const hatText=[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim());if(!hatText&&!e.matches('.chat,img'))return;
  const r=e.getBoundingClientRect();if(!r.width||!r.height)return;
  const x0=r.left-S.left,x1=r.right-S.left,y0=r.top-S.top,y1=r.bottom-S.top;
  if(x0<58||x1>922||y0<148||y1>1422)o.push((e.className||e.tagName)+' "'+(e.textContent||'').trim().slice(0,24)+'" @'+t.toFixed(1)+'s')})});return o}'''
start = time.time()
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=exe)
    pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    fehl = []
    pg.on('requestfailed', lambda r: fehl.append(r.url))
    pg.on('pageerror', lambda e: fehl.append('JS-Fehler: ' + str(e)))
    pg.goto((d / 'post.html').as_uri())
    pg.wait_for_function('window.READY===true', timeout=20000); pg.wait_for_timeout(300)
    dauer = float(pg.evaluate('window.DAUER'))
    n = int(round(dauer * FPS))
    warn = []
    for t in [x / 4 for x in range(int(dauer * 4) + 1)]:
        for w in pg.evaluate(PRUEF, t):
            if w.split(' @')[0] not in [v.split(' @')[0] for v in warn]: warn.append(w)
    stage = pg.locator('#stage')
    for i in range(n):
        pg.evaluate('t=>window.renderAt(t)', i / FPS)
        stage.screenshot(path=str(fr / f'f{i:04d}.jpg'), type='jpeg', quality=92)
    b.close()
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', str(fr / 'f%04d.jpg'),
                '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
                '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', str(FPS),
                '-c:a', 'aac', '-b:a', '96k', '-shortest', '-movflags', '+faststart', str(out / 'video.mp4')], check=True)
Image.open(fr / f'f{min(n - 1, int(0.6 * FPS)):04d}.jpg').save(out / 'cover.jpg', quality=90)
idx = list(range(0, n, FPS)) + [n - 1]
ims = [Image.open(fr / f'f{i:04d}.jpg').resize((216, 384)) for i in idx]
cols = 6; sh = Image.new('RGB', (cols * 222, ((len(ims) + cols - 1) // cols) * 390), '#333')
for k, im in enumerate(ims): sh.paste(im, ((k % cols) * 222, (k // cols) * 390))
sh.save(out / '_bogen.jpg', quality=85)
shutil.rmtree(fr)
print(f'{dauer:.1f} s, {n} Bilder in {time.time() - start:.0f} s |', 'Fehler:', fehl or 'keine', '| ausserhalb des sicheren Bereichs:', warn or 'nichts')
