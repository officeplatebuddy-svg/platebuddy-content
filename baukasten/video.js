/* PlateBuddy Video-Baukasten: Zeitleiste ohne eigenes JavaScript im Post.
   Szenen: <section class="szene" data-von="SEK" data-ein="schnitt|wisch|blende|zoom|hoch">  (Ende = Beginn der nächsten Szene)
   Elemente: data-a="pop|slam|rise|drop|fade|links|rechts|wackel|zoom|tippen|durch|puls|scroll|zaehl" (mehrere mit Leerzeichen)
             data-t = Start in Sekunden ab Szenenbeginn, data-d = Dauer, data-weg = ausblenden ab (Sekunden ab Szenenbeginn)
             zoom: data-z (Stärke, 0.08), data-zd (Dauer, 4) · scroll: data-y0/data-y1 (px) · zaehl: data-von-zahl/data-bis-zahl
   Chat: .chat > .verlauf > .msg / .tippt / .zeit mit data-t (und .tippt mit data-weg); scrollt automatisch mit.
   Wichtig: Animierte Elemente nicht mit transform positionieren (wird überschrieben) – dafür ein Eltern-Element nehmen. */
(function () {
  const cl = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const p = (t, a, d) => (d <= 0 ? (t >= a ? 1 : 0) : cl((t - a) / d));
  const oc = x => 1 - Math.pow(1 - x, 3);
  const ob = x => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
  const esc = s => s.replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
  const stage = document.getElementById('stage');
  const DAUER = +stage.dataset.dauer;
  const szenen = [...stage.querySelectorAll('.szene')];
  stage.querySelectorAll('[data-a~="tippen"]').forEach(el => { el.dataset.voll = el.textContent; });

  function anim(el, lt) {
    const arten = (el.dataset.a || '').split(/\s+/).filter(Boolean);
    const t0 = +el.dataset.t || 0, d = el.dataset.d != null ? +el.dataset.d : null;
    if (el.matches('.msg,.tippt,.zeit')) {
      const weg = el.dataset.weg != null ? +el.dataset.weg : Infinity;
      el.style.display = lt >= t0 && lt < weg ? '' : 'none';
    }
    let o = 1, tx = 0, ty = 0, s = 1, r = 0;
    for (const a of arten) {
      if (a === 'pop') { const k = p(lt, t0, d ?? 0.32); o *= cl(k * 4); s *= k <= 0 ? 0.001 : ob(k); }
      else if (a === 'slam') { const k = p(lt, t0, d ?? 0.22); o *= cl(k * 3); s *= 1.25 - 0.25 * oc(k); }
      else if (a === 'rise') { const k = oc(p(lt, t0, d ?? 0.3)); o *= k; ty += (1 - k) * 70; }
      else if (a === 'drop') { const k = oc(p(lt, t0, d ?? 0.3)); o *= k; ty -= (1 - k) * 80; }
      else if (a === 'fade') { o *= p(lt, t0, d ?? 0.3); }
      else if (a === 'links') { const k = oc(p(lt, t0, d ?? 0.35)); o *= cl(k * 2); tx -= (1 - k) * 320; }
      else if (a === 'rechts') { const k = oc(p(lt, t0, d ?? 0.35)); o *= cl(k * 2); tx += (1 - k) * 320; }
      else if (a === 'wackel') { const k = p(lt, t0, d ?? 0.5); r += k > 0 && k < 1 ? Math.sin(k * Math.PI * 6) * 5 * (1 - k) : 0; }
      else if (a === 'zoom') { s *= 1 + (+el.dataset.z || 0.08) * cl((lt - t0) / (+el.dataset.zd || 4)); }
      else if (a === 'tippen') {
        const voll = el.dataset.voll, dur = d ?? voll.length * 0.045;
        const n = Math.round(voll.length * p(lt, t0, dur));
        el.innerHTML = esc(voll.slice(0, n)) + '<span style="opacity:0">' + esc(voll.slice(n)) + '</span>';
        o *= lt >= t0 ? 1 : 0;
      }
      else if (a === 'durch') { el.style.setProperty('--durch', (oc(p(lt, t0, d ?? 0.3)) * 100) + '%'); }
      else if (a === 'puls') { const k = p(lt, t0, d ?? 0.7); o *= k > 0 && k < 1 ? 1 - k * k : 0; s *= 0.5 + 0.9 * oc(k); }
      else if (a === 'scroll') { const k = (1 - Math.cos(Math.PI * p(lt, t0, d ?? 1.5))) / 2; const y0 = +el.dataset.y0 || 0, y1 = +el.dataset.y1 || 0; ty += y0 + (y1 - y0) * k; }
      else if (a === 'zaehl') { const a0 = +el.dataset.vonZahl || 0, a1 = +el.dataset.bisZahl || 0; el.textContent = Math.round(a0 + (a1 - a0) * oc(p(lt, t0, d ?? 0.8))) + (el.dataset.einheit || ''); }
    }
    if (el.dataset.weg != null && !el.matches('.msg,.tippt,.zeit')) o *= 1 - p(lt, +el.dataset.weg, 0.2);
    el.style.opacity = o;
    el.style.transform = tx || ty || s !== 1 || r ? `translate(${tx}px,${ty}px) scale(${s}) rotate(${r}deg)` : '';
  }

  function chat(c, lt) {
    const v = c.querySelector('.verlauf'); if (!v) return;
    v.style.transform = '';
    const H = c.clientHeight; let sc = 0;
    v.querySelectorAll('.msg,.tippt,.zeit').forEach(m => {
      if (m.style.display === 'none') return;
      const over = Math.max(0, m.offsetTop + m.offsetHeight + 24 - H);
      sc = Math.max(sc, over * oc(p(lt, +m.dataset.t || 0, 0.25)));
    });
    v.style.transform = `translateY(${-sc}px)`;
  }

  function szene(sz, i, t) {
    const von = +sz.dataset.von || 0;
    const nae = szenen[i + 1];
    const bis = nae ? +nae.dataset.von : DAUER + 1;
    const ue = e => (e && e !== 'schnitt' ? 0.3 : 0);
    const vis = t >= von && t < bis + ue(nae && nae.dataset.ein);
    sz.style.display = vis ? 'block' : 'none';
    if (!vis) return;
    sz.style.zIndex = i + 1;
    const ein = sz.dataset.ein || 'schnitt', k = oc(p(t, von, ue(ein) || 0.0001));
    let tr = '', o = 1;
    if (ein === 'wisch') tr = `translateX(${(1 - k) * 1080}px)`;
    else if (ein === 'blende') o = k;
    else if (ein === 'zoom') { o = k; tr = `scale(${1.15 - 0.15 * k})`; }
    else if (ein === 'hoch') tr = `translateY(${(1 - k) * 1920}px)`;
    sz.style.opacity = o; sz.style.transform = tr;
    const lt = t - von;
    sz.querySelectorAll('[data-a],.msg,.tippt,.zeit').forEach(el => anim(el, lt));
    sz.querySelectorAll('.chat').forEach(c => chat(c, lt));
  }

  window.DAUER = DAUER;
  window.renderAt = t => szenen.forEach((s, i) => szene(s, i, t));
  const urls = new Set();
  stage.querySelectorAll('*').forEach(el => { const m = /url\(["']?([^"')]+)/.exec(getComputedStyle(el).backgroundImage); if (m) urls.add(m[1]); });
  const bilder = [...document.images].map(im => im.decode().catch(() => {}))
    .concat([...urls].map(u => { const im = new Image(); im.src = u; return im.decode().catch(() => {}); }));
  Promise.all([document.fonts.ready, ...bilder]).then(() => { window.renderAt(0); window.READY = true; });
})();
