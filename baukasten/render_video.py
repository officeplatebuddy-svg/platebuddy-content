# Aufruf: python3 render_video.py <html> <frames-ordner> <dauer> [fps]
import sys, os, pathlib
from playwright.sync_api import sync_playwright
html, out, dur = sys.argv[1], sys.argv[2], float(sys.argv[3]); fps = int(sys.argv[4]) if len(sys.argv) > 4 else 30
os.makedirs(out, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None)
    pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    pg.goto(pathlib.Path(html).resolve().as_uri()); pg.wait_for_function('window.READY===true'); pg.wait_for_timeout(400)
    n = int(round(dur * fps))
    for i in range(n):
        pg.evaluate('t=>window.renderAt(t)', i / fps)
        pg.screenshot(path=f'{out}/f{i:04d}.jpg', type='jpeg', quality=93)
    b.close()
print(n, 'Bilder')
