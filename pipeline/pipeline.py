#!/usr/bin/env python3
"""PlateBuddy-Pipeline (GitHub Actions).

Läuft alle 5 Minuten:
  1. Telegram lesen (Knöpfe Go / Neu / Verwerfen / Insta, Nachrichten, /tiktok <code>)
  2. Neue Ordner in beitraege/ zur Freigabe nach Telegram schicken
  3. Freigegebene Beiträge als Entwurf ins TikTok-Postfach laden
  4. Zum Termin ans Posten erinnern
  5. Für Instagram vorgemerkte Beiträge um 19:00 als Reel veröffentlichen

Zustand liegt verschlüsselt im Branch „state“ (state.enc). Geheimnisse kommen nur
aus Umgebungsvariablen (GitHub Secrets) und werden nie ausgegeben.

Aufruf:  python3 pipeline.py run | connect-start | connect <code>
"""
import base64, datetime as dt, hashlib, html, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

from cryptography.fernet import Fernet, InvalidToken

WIEN = ZoneInfo('Europe/Vienna')
ROOT = Path(__file__).resolve().parent.parent          # Repo-Wurzel (Branch main)
STATE_DIR = Path(os.environ.get('PB_STATE_DIR', ROOT / '_state'))
SEITE = 'https://officeplatebuddy-svg.github.io/platebuddy-content/'
CALLBACK = SEITE + 'tiktok-verbinden.html'
IG_ID = '17841416945473197'
IG_API = 'https://graph.instagram.com/v23.0/'
TT_API = 'https://open.tiktokapis.com/v2/'
CHAT = os.environ.get('PB_CHAT_ID', '-5374518764')

TG_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
TT_KEY = os.environ.get('TIKTOK_CLIENT_KEY', '').strip()
TT_SECRET = os.environ.get('TIKTOK_CLIENT_SECRET', '').strip()
IG_TOKEN_SECRET = os.environ.get('INSTAGRAM_TOKEN', '').strip()
STATE_KEY = os.environ.get('STATE_KEY', '')

for _s in (TG_TOKEN, TT_SECRET, IG_TOKEN_SECRET, STATE_KEY):   # in GitHub-Logs verbergen
    if _s and os.environ.get('GITHUB_ACTIONS'):
        print(f'::add-mask::{_s}')


def mask(v):
    if v and os.environ.get('GITHUB_ACTIONS'):
        print(f'::add-mask::{v}')


def log(*a):
    print(*a, flush=True)


def jetzt():
    return dt.datetime.now(WIEN).strftime('%Y-%m-%dT%H:%M')


def iso():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def esc(s):
    return html.escape(str(s or ''), quote=False)


# ---------------------------------------------------------------- HTTP

def http(method, url, data=None, form=None, headers=None, timeout=60):
    """Gibt (status, json|text) zurück, wirft nie."""
    h = dict(headers or {})
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        h.setdefault('Content-Type', 'application/json; charset=UTF-8')
    elif form is not None:
        body = urllib.parse.urlencode(form).encode()
        h.setdefault('Content-Type', 'application/x-www-form-urlencoded')
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode('utf-8', 'replace')
            st = r.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8', 'replace'); st = e.code
    except Exception as e:  # Netzfehler
        return 0, {'error': {'message': f'{type(e).__name__}: {e}'}}
    try:
        return st, json.loads(raw)
    except Exception:
        return st, raw


def erreichbar(url):
    st, _ = http('GET', url + ('&' if '?' in url else '?') + 't=' + str(int(time.time())), timeout=30)
    return st == 200


# ---------------------------------------------------------------- Zustand

def fernet():
    if not STATE_KEY:
        raise SystemExit('STATE_KEY fehlt (GitHub Secret).')
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(STATE_KEY.encode()).digest()))


def lade_zustand():
    f = STATE_DIR / 'state.enc'
    neu_wegen_schluessel = False
    if f.exists():
        try:
            return json.loads(fernet().decrypt(f.read_bytes()))
        except InvalidToken:
            log('state.enc lässt sich nicht entschlüsseln (STATE_KEY geändert?) – starte mit neuem Zustand.')
            neu_wegen_schluessel = True
    z = {'beitraege': {}, 'tg_offset': 0, 'notizen': [], 'tiktok': {}, 'instagram': {}, 'hinweise': {}}
    imp = ROOT / 'pipeline' / 'import.json'
    if imp.exists() and not neu_wegen_schluessel:
        z['beitraege'].update(json.loads(imp.read_text()))
        log('Zustand aus import.json übernommen:', len(z['beitraege']))
    # alles, was schon im Repo liegt, gilt als bekannt → nichts wird doppelt verschickt
    for d in (ROOT / 'beitraege').glob('*/beitrag.json'):
        z['beitraege'].setdefault(d.parent.name, {'id': d.parent.name, 'titel': d.parent.name, 'status': 'alt', 'quelle': 'github', 'geliefert': iso()})
    if neu_wegen_schluessel:
        z['hinweise']['neustart'] = True
    return z


def speichere_zustand(z):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / 'state.enc').write_bytes(fernet().encrypt(json.dumps(z, ensure_ascii=False).encode()))
    # öffentliche Kurzliste für die Claude-Aufgabe (ohne Inhalte aus dem Chat)
    offen = [{'id': e['id'], 'titel': e.get('titel', ''), 'status': e.get('status'), 'zeit': e.get('zeit', ''),
              'tiktok': e.get('tiktok', ''), 'insta': e.get('insta', ''),
              'tiktok_fehler': e.get('tiktok_fehler', ''), 'insta_fehler': e.get('insta_fehler', '')}
             for e in sorted(z['beitraege'].values(), key=lambda x: x.get('geliefert', ''), reverse=True)[:30]]
    (STATE_DIR / 'beitraege-status.json').write_text(json.dumps(offen, ensure_ascii=False, indent=1))
    wuensche = [{'id': e['id'], 'titel': e.get('titel', ''), 'zeit': e.get('zeit', ''), 'wunsch': e.get('wunsch', ''),
                 'von': e.get('wunsch_von', ''), 'seit': e.get('wunsch_zeit') or e.get('entschieden', '')}
                for e in z['beitraege'].values() if e.get('status') == 'neu']
    (STATE_DIR / 'wuensche.json').write_text(json.dumps(wuensche, ensure_ascii=False, indent=1))


def merke(z, wer, text):
    c = z.setdefault('chat', [])
    c.append({'wer': wer, 'text': str(text)[:300], 'zeit': iso()})
    del c[:-12]


def einmal_am_tag(z, key):
    """True, wenn diese Meldung heute noch nicht kam."""
    heute = jetzt()[:10]
    if z['hinweise'].get(key) == heute:
        return False
    z['hinweise'][key] = heute
    return True


# ---------------------------------------------------------------- Telegram

DIAG = {'telegram': {}, 'fehler': []}


def tg(method, **params):
    if not TG_TOKEN:
        DIAG['fehler'].append('TELEGRAM_BOT_TOKEN fehlt')
        return 0, {'ok': False, 'description': 'TELEGRAM_BOT_TOKEN fehlt'}
    st, j = http('POST', f'https://api.telegram.org/bot{TG_TOKEN}/{method}', data=params)
    ok = isinstance(j, dict) and j.get('ok')
    DIAG['telegram'][method] = 'ok' if ok else f'{st} ' + str((j.get('description') if isinstance(j, dict) else str(j)[:120]))[:160]
    if not ok:
        log('Telegram', method, 'fehlgeschlagen:', DIAG['telegram'][method])
    return st, j


def senden(text, **extra):
    return tg('sendMessage', chat_id=CHAT, text=text[:4000], parse_mode='HTML', disable_web_page_preview=True, **extra)


def telegram_lesen(z):
    st, info = tg('getWebhookInfo')
    if isinstance(info, dict) and info.get('ok') and info['result'].get('url'):
        log('Telegram-Webhook (n8n) wird entfernt, ab jetzt liest GitHub.')
        tg('deleteWebhook', drop_pending_updates=False)
    st, j = tg('getUpdates', offset=z['tg_offset'] + 1, timeout=0, allowed_updates=['callback_query', 'message'])
    if not (isinstance(j, dict) and j.get('ok')):
        return
    for u in j['result']:
        z['tg_offset'] = max(z['tg_offset'], u['update_id'])
        try:
            if 'callback_query' in u:
                knopf(z, u['callback_query'])
            elif 'message' in u:
                nachricht(z, u['message'])
        except Exception as e:  # ein kaputtes Update darf den Lauf nicht stoppen
            log('Update übersprungen:', type(e).__name__, e)


def insta_knopf(pid):
    return {'inline_keyboard': [[{'text': '📸 Auch auf Insta posten (19:00)', 'callback_data': f'insta|{pid}'}]]}


def knopf(z, cq):
    msg = cq.get('message') or {}
    chat = str((msg.get('chat') or {}).get('id', ''))
    wer = (cq.get('from') or {}).get('first_name') or 'Jemand'
    aktion, _, pid = str(cq.get('data', '')).partition('|')
    e = z['beitraege'].get(pid)
    hinweis, neu_text = '', ''
    if chat != CHAT:
        hinweis = 'Hier nicht erlaubt.'
    elif not e:
        hinweis = 'Diesen Beitrag kenne ich nicht mehr.'
    elif aktion == 'instajetzt':
        e['insta'] = 'geplant'; e['insta_zeit'] = jetzt(); e.pop('insta_versuche', None)
        hinweis = 'Wird jetzt nochmal versucht.'
        senden(f'📸 Neuer Versuch für <b>{esc(e["titel"])}</b> läuft – Meldung kommt in ein paar Minuten.')
    elif aktion == 'insta':
        if e.get('insta') == 'online':
            hinweis = 'Ist schon auf Instagram.'
        elif e.get('insta') == 'geplant':
            hinweis = f'Ist schon für Insta um 19:00 vorgemerkt.'
        else:
            e['insta'] = 'geplant'; e['insta_von'] = wer
            e['insta_zeit'] = ((e.get('zeit') or '')[:10] or jetzt()[:10]) + 'T19:00'
            if e['insta_zeit'] < jetzt():   # 19 Uhr schon vorbei → morgen
                morgen = (dt.datetime.now(WIEN) + dt.timedelta(days=1)).strftime('%Y-%m-%d')
                e['insta_zeit'] = morgen + 'T19:00'
            hinweis = 'Insta vorgemerkt.'
            senden(f'📸 {esc(wer)}: <b>{esc(e["titel"])}</b> geht am {e["insta_zeit"][8:10]}.{e["insta_zeit"][5:7]}. um 19:00 als Reel auf Instagram.')
            merke(z, wer, f'Insta vorgemerkt: {e["titel"]}')
    elif e.get('status') in ('gepostet', 'geplant') and aktion != 'weg':
        hinweis = 'Ist schon bei TikTok.'
    elif aktion in ('go', 'neu', 'weg'):
        e['status'] = {'go': 'go', 'neu': 'neu', 'weg': 'verworfen'}[aktion]
        e['von'] = wer; e['entschieden'] = iso()
        uhr = dt.datetime.now(WIEN).strftime('%H:%M')
        if aktion == 'go':
            hinweis = 'Go gespeichert.'
            neu_text = (f'✅ Go von {wer} um {uhr} Uhr.\n„{e["titel"]}“ ist freigegeben. Kommt in ein paar Minuten '
                        'als Entwurf in dein TikTok-Postfach.' + (f' Um {e["zeit"][11:]} Uhr erinnere ich dich ans Posten.' if e.get('zeit') else ''))
        elif aktion == 'neu':
            hinweis = 'Neue Version angefordert.'
            neu_text = f'🔁 {wer} möchte eine neue Version von „{e["titel"]}“ ({uhr} Uhr). Claude baut sie und schickt sie hier wieder zur Freigabe.'
        else:
            hinweis = 'Verworfen.'
            neu_text = f'❌ „{e["titel"]}“ wurde von {wer} verworfen ({uhr} Uhr). Es wird nichts gepostet.'
        merke(z, wer, f'Knopf {aktion} bei „{e["titel"]}“')
    else:
        hinweis = 'Unbekannter Knopf.'
    tg('answerCallbackQuery', callback_query_id=cq.get('id', ''), text=hinweis)
    if neu_text and msg.get('message_id'):
        extra = {}
        if aktion == 'go' and e.get('insta') not in ('geplant', 'online'):
            extra['reply_markup'] = insta_knopf(e['id'])
        tg('editMessageText', chat_id=CHAT, message_id=msg['message_id'], text=neu_text, **extra)
    elif aktion == 'insta' and e and e.get('insta') == 'geplant' and msg.get('message_id'):
        tg('editMessageReplyMarkup', chat_id=CHAT, message_id=msg['message_id'], reply_markup={'inline_keyboard': []})
    if aktion == 'neu' and e and e.get('status') == 'neu':
        st, j = senden(f'🔁 Was soll an <b>{esc(e["titel"])}</b> anders sein? Antworte direkt auf diese Nachricht '
                       '(z. B. „Hook frecher“, „anderes Gericht“, „kürzer“).',
                       reply_markup={'force_reply': True, 'selective': False, 'input_field_placeholder': 'Was soll anders sein?'})
        if isinstance(j, dict) and j.get('ok'):
            e['neu_frage_mid'] = j['result']['message_id']


def nachricht(z, m):
    if str((m.get('chat') or {}).get('id', '')) != CHAT:
        return
    text = (m.get('text') or '').strip()
    wer = (m.get('from') or {}).get('first_name') or 'Jemand'
    if text.lower().startswith(('/plan', '/heute')):
        heute = jetzt()[:10]
        morgen = (dt.datetime.now(WIEN) + dt.timedelta(days=1)).strftime('%Y-%m-%d')
        zeilen = []
        for e in sorted(z['beitraege'].values(), key=lambda x: (x.get('zeit') or '9', x.get('id'))):
            if e.get('status') in ('alt', 'ersetzt', 'verworfen') or not e.get('art'):
                continue
            tag_ = (e.get('zeit') or e.get('insta_zeit') or '')[:10]
            if tag_ and tag_ not in (heute, morgen):
                continue
            tt = {'entwurf': '📥 im TikTok-Postfach', 'fehler': '⚠️ TikTok-Fehler'}.get(e.get('tiktok'), '⏳ wartet auf Go' if e.get('status') == 'wartet' else ('🔁 neue Version kommt' if e.get('status') == 'neu' else '…'))
            ig = {'geplant': f'📸 Insta {e.get("insta_zeit", "")[8:10]}.{e.get("insta_zeit", "")[5:7]}. 19:00', 'online': '📸 auf Insta online', 'fehler': '⚠️ Insta-Fehler'}.get(e.get('insta'), '— kein Insta')
            wann = f'{e["zeit"][8:10]}.{e["zeit"][5:7]}. {e["zeit"][11:]}' if e.get('zeit') else 'ohne Termin'
            zeilen.append(f'<b>{esc(e["titel"])}</b>\n{wann} · {tt} · {ig}')
        senden('🗓 <b>Plan heute und morgen</b>\n\n' + ('\n\n'.join(zeilen) if zeilen else 'Noch nichts geplant.'), reply_to_message_id=m.get('message_id'))
        return
    if text.lower().startswith('/tiktok'):
        teile = text.split()
        if len(teile) >= 2:
            tiktok_verbinden(z, teile[-1])
        else:
            tiktok_link(z)
        return
    rb = m.get('reply_to_message') or {}
    an_bot = bool((rb.get('from') or {}).get('is_bot'))
    ziel = next((e for e in z['beitraege'].values() if rb.get('message_id') and e.get('neu_frage_mid') == rb.get('message_id')), None)
    if ziel and text:                                   # Antwort auf „Was soll anders sein?“
        ziel['wunsch'] = (ziel.get('wunsch', '') + ('\n' if ziel.get('wunsch') else '') + text)[:1500]
        ziel['wunsch_von'] = wer; ziel['wunsch_zeit'] = iso(); ziel['status'] = 'neu'
        merke(z, wer, f'Wunsch zu {ziel["titel"]}: {text}')
        senden(f'📝 Danke, {esc(wer)}! Claude baut eine neue Version von <b>{esc(ziel["titel"])}</b> mit: „{esc(text[:300])}“. '
               'Sie kommt hier wieder mit Video zur Freigabe.', reply_to_message_id=m.get('message_id'))
        return
    if text.lower().startswith(('/claude', '/jarvis')) or (an_bot and text):
        auftrag = text.split(None, 1)[1] if text.startswith('/') and ' ' in text else ('' if text.startswith('/') else text)
        if not auftrag:
            senden('Schreib nach /claude, was ich tun soll. Zum Beispiel: /claude mach ein Video über den Wochenplan', reply_to_message_id=m.get('message_id'))
            return
        nr = max([n.get('nr', 0) for n in z['notizen']] + [0]) + 1
        z['notizen'].append({'nr': nr, 'von': wer, 'text': auftrag[:1500], 'bezug': (rb.get('text') or rb.get('caption') or '')[:300],
                             'zeit': iso(), 'status': 'offen'})
        del z['notizen'][:-60]
        merke(z, wer, auftrag)
        senden(f'📝 Notiert, {esc(wer)}. Claude kümmert sich beim nächsten Morgenlauf darum.', reply_to_message_id=m.get('message_id'))


# ---------------------------------------------------------------- neue Beiträge

def freigabe_senden(z, e):
    """Schickt Vorschau-Video + Freigabe-Nachricht mit allen Knöpfen. True bei Erfolg."""
    pid, termin, bilder, art = e['id'], e.get('zeit', ''), e.get('bilder') or [], e.get('art')
    mid = None
    if art == 'fotos' and bilder:                # Slideshow als Album zum selbst Durchwischen
        media = [{'type': 'photo', 'media': u} for u in bilder[:10]]
        media[0]['caption'] = e['titel'][:1000]
        st, j = tg('sendMediaGroup', chat_id=CHAT, media=media)
        res = j.get('result') if isinstance(j, dict) and j.get('ok') else None
        if isinstance(res, list) and res:
            mid = res[0].get('message_id')
    if mid is None:
        st, j = tg('sendVideo', chat_id=CHAT, video=e.get('vorschau') or e.get('video'), caption=e['titel'][:1000])
        mid = (j.get('result') or {}).get('message_id') if isinstance(j, dict) else None
    wann = (f'\n\n🗓 Geplant für {termin[8:10]}.{termin[5:7]}. um {termin[11:]} Uhr' if termin else '\n\n🗓 Ohne Termin')
    was = f'Slideshow zum Wischen ({len(bilder)} Bilder, oben als Album)' if art == 'fotos' else 'Video'
    text = (f'<b>{esc(e["titel"])}</b>\n{was}{wann}' + (f'\n🎵 Sound-Idee: {esc(e.get("sound"))}' if e.get('sound') else '') +
            f'\n\n<b>Beschreibung:</b>\n{esc(e.get("caption"))}\n\n✅ Go: kommt gleich als Entwurf in dein TikTok-Postfach, zum Termin erinnere ich dich.'
            '\n🔁 Neu: Claude baut eine andere Version.\n❌ Verwerfen: wird nicht gepostet.\n📸 Insta 19:00: geht zusätzlich als Reel auf Instagram.')
    kb = {'inline_keyboard': [[{'text': '✅ Go', 'callback_data': f'go|{pid}'}, {'text': '🔁 Neu', 'callback_data': f'neu|{pid}'},
                               {'text': '❌ Verwerfen', 'callback_data': f'weg|{pid}'}],
                              [{'text': '📸 Insta 19:00', 'callback_data': f'insta|{pid}'}]]}
    st, j = senden(text, reply_markup=kb, **({'reply_to_message_id': mid} if mid else {}))
    if isinstance(j, dict) and j.get('ok'):
        merke(z, 'Claude', f'Beitrag zur Freigabe geschickt: {e["titel"]}')
        log('Zur Freigabe geschickt:', pid)
        return True
    return False


def offene_neu_senden(z):
    for e in sorted(z['beitraege'].values(), key=lambda x: x.get('zeit') or ''):
        if e.get('status') == 'wartet' and e.get('art'):
            e.pop('insta_knopf_nachreichen', None)
            freigabe_senden(z, e)


def neue_beitraege(z):
    L = z['beitraege']
    grenze = time.time() - 21 * 86400
    for k, e in L.items():                     # alte Einträge verkleinern, aber merken (sonst käme der Ordner erneut)
        if e.get('geliefert') and dt.datetime.fromisoformat(e['geliefert']).timestamp() < grenze and len(e) > 5:
            L[k] = {x: e.get(x) for x in ('id', 'titel', 'status', 'quelle', 'geliefert')}
    for e in L.values():                       # aus n8n übernommene Beiträge bekommen den Insta-Knopf nachgereicht
        if e.pop('insta_knopf_nachreichen', False) and e.get('status') not in ('verworfen',) and e.get('insta') not in ('geplant', 'online'):
            senden(f'📸 Soll <b>{esc(e["titel"])}</b> auch auf Instagram? Dann hier drücken (geht um 19:00 als Reel raus).',
                   reply_markup={'inline_keyboard': [[{'text': '📸 Insta 19:00', 'callback_data': f'insta|{e["id"]}'}]]})
    for d in sorted((ROOT / 'beitraege').glob('*/beitrag.json')):
        pid = d.parent.name
        if pid in L:
            continue
        try:
            b = json.loads(d.read_text())
        except Exception as e:
            log('beitrag.json kaputt:', pid, e); continue
        if b.get('status') == 'entwurf':
            continue
        basis = SEITE + 'beitraege/' + pid + '/'
        art = 'fotos' if b.get('art') == 'fotos' else 'video'
        bilder = [basis + f for f in (b.get('bilder') or [])][:35]
        video = basis + b['video'] if b.get('video') else ''
        vorschau = basis + (b.get('vorschau') or ('vorschau.mp4' if art == 'fotos' else b.get('video', '')))
        if (art == 'fotos' and not bilder) or (art == 'video' and not video):
            log('Beitrag ohne Medien:', pid); continue
        if not erreichbar(vorschau):            # GitHub Pages noch nicht fertig → nächster Lauf
            log('Noch nicht auf GitHub Pages:', pid); continue
        termin = b.get('termin') or ''
        if not (len(termin) == 16 and termin[10] == 'T'):
            termin = ''
        e = {'id': pid, 'titel': str(b.get('titel') or 'Neuer Beitrag')[:120], 'caption': str(b.get('beschreibung') or '')[:2200],
             'zeit': termin, 'art': art, 'bilder': bilder, 'video': video, 'vorschau': vorschau,
             'plattformen': b.get('plattformen') or ['tiktok'], 'sound': str(b.get('sound') or '')[:200],
             'quelle': 'github', 'status': 'wartet', 'geliefert': iso()}
        if freigabe_senden(z, e):
            L[pid] = e
            import re
            m_v = re.match(r'(.+)-v\d+$', pid)
            if m_v:
                for k, alt in L.items():
                    if k != pid and (k == m_v.group(1) or k.startswith(m_v.group(1) + '-v')) and alt.get('status') in ('neu', 'wartet'):
                        alt['status'] = 'ersetzt'


# ---------------------------------------------------------------- TikTok

def tiktok_link(z):
    if not TT_KEY:
        senden('⚠️ TikTok-Zugang fehlt (TIKTOK_CLIENT_KEY in GitHub).'); return
    q = urllib.parse.urlencode({'client_key': TT_KEY, 'scope': 'user.info.basic,video.upload,video.publish',
                                'response_type': 'code', 'redirect_uri': CALLBACK, 'state': 'platebuddy'})
    senden('🔗 TikTok verbinden: Öffne diesen Link am Handy, melde dich mit @plate.buddy an und bestätige. '
           'Danach zeigt die Seite einen Code – schick ihn hier als <code>/tiktok CODE</code>.\n\n'
           f'<a href="https://www.tiktok.com/v2/auth/authorize/?{q}">TikTok jetzt verbinden</a>')


def tiktok_token_speichern(z, j):
    d = j if 'access_token' in j else (j.get('data') or {})
    if not d.get('access_token'):
        return False
    mask(d['access_token']); mask(d.get('refresh_token', ''))
    z['tiktok'] = {'access_token': d['access_token'], 'refresh_token': d.get('refresh_token', z['tiktok'].get('refresh_token', '')),
                   'expires_at': time.time() + int(d.get('expires_in', 86400)) - 300,
                   'refresh_expires_at': time.time() + int(d.get('refresh_expires_in', 31536000)),
                   'open_id': d.get('open_id', z['tiktok'].get('open_id', ''))}
    return True


def tiktok_verbinden(z, code):
    code = urllib.parse.unquote(code.strip())
    mask(code)
    st, j = http('POST', TT_API + 'oauth/token/', form={'client_key': TT_KEY, 'client_secret': TT_SECRET, 'code': code,
                                                         'grant_type': 'authorization_code', 'redirect_uri': CALLBACK})
    if isinstance(j, dict) and tiktok_token_speichern(z, j):
        senden('✅ TikTok ist verbunden. Freigegebene Beiträge kommen ab jetzt automatisch als Entwurf in dein Postfach.')
        log('TikTok verbunden.')
    else:
        grund = (j.get('error_description') or j.get('error') or j.get('message')) if isinstance(j, dict) else str(j)[:200]
        senden(f'⚠️ TikTok-Verbindung hat nicht geklappt: {esc(str(grund)[:200])}\nSchreib <code>/tiktok</code>, dann schicke ich einen neuen Link.')


def tiktok_zugang(z):
    t = z.get('tiktok') or {}
    if t.get('access_token') and t.get('expires_at', 0) > time.time():
        return t['access_token']
    if not t.get('refresh_token'):
        return ''
    st, j = http('POST', TT_API + 'oauth/token/', form={'client_key': TT_KEY, 'client_secret': TT_SECRET,
                                                         'grant_type': 'refresh_token', 'refresh_token': t['refresh_token']})
    if isinstance(j, dict) and tiktok_token_speichern(z, j):
        return z['tiktok']['access_token']
    log('TikTok-Token-Erneuerung fehlgeschlagen:', (j.get('error') if isinstance(j, dict) else str(j)[:100]))
    z['tiktok'] = {}
    return ''


def tiktok_hochladen(z):
    faellig = [e for e in z['beitraege'].values() if e.get('quelle') == 'github' and e.get('status') == 'go' and e.get('art')
               and not e.get('tiktok') and 'tiktok' in (e.get('plattformen') or ['tiktok'])]
    if not faellig:
        return
    tok = tiktok_zugang(z)
    if not tok:
        if einmal_am_tag(z, 'tiktok_fehlt'):
            senden('⚠️ TikTok ist noch nicht mit GitHub verbunden, deshalb liegen freigegebene Beiträge noch nicht im Postfach.\n'
                   'Schreib hier <code>/tiktok</code>, dann schicke ich dir den Verbinden-Link.')
        return
    for e in faellig:
        if e['art'] == 'fotos':
            url = TT_API + 'post/publish/content/init/'
            body = {'post_info': {'title': e['titel'][:90], 'description': e['caption'][:4000]},
                    'source_info': {'source': 'PULL_FROM_URL', 'photo_cover_index': 0, 'photo_images': e['bilder']},
                    'post_mode': 'MEDIA_UPLOAD', 'media_type': 'PHOTO'}
        else:
            url = TT_API + 'post/publish/inbox/video/init/'
            body = {'source_info': {'source': 'PULL_FROM_URL', 'video_url': e['video']}}
        st, j = http('POST', url, data=body, headers={'Authorization': f'Bearer {tok}'})
        err = (j.get('error') or {}) if isinstance(j, dict) else {}
        pid = ((j.get('data') or {}).get('publish_id')) if isinstance(j, dict) else None
        if pid and err.get('code', 'ok') == 'ok':
            e['tiktok'] = 'entwurf'; e['tiktok_publish_id'] = pid; e['status'] = 'geplant'
            senden(f'📥 <b>{esc(e["titel"])}</b> liegt jetzt in deinem TikTok-Postfach' +
                   (f' (posten um {e["zeit"][11:]} Uhr, ich erinnere dich)' if e.get('zeit') else '') +
                   '.\nTikTok-App öffnen → Postfach/Benachrichtigungen → Entwurf öffnen, Sound wählen, posten.' +
                   (f'\n\n<b>Beschreibung zum Kopieren:</b>\n{esc(e["caption"])}' if e['art'] == 'video' else ''),
                   **({'reply_markup': insta_knopf(e['id'])} if e.get('insta') not in ('geplant', 'online') else {}))
            log('TikTok-Entwurf:', e['id'])
        else:
            grund = err.get('message') or err.get('code') or str(j)[:300]
            e['tiktok'] = 'fehler'; e['tiktok_fehler'] = str(grund)[:500]
            senden(f'⚠️ TikTok-Upload für <b>{esc(e["titel"])}</b> hat nicht geklappt.\nGrund: {esc(str(grund)[:300])}\nClaude schaut es sich an.')
            log('TikTok-Fehler:', e['id'], grund)


def erinnern(z):
    for e in z['beitraege'].values():
        if e.get('tiktok') == 'entwurf' and not e.get('erinnert') and e.get('zeit') and e['zeit'] <= jetzt():
            e['erinnert'] = iso()
            senden(f'⏰ Jetzt posten: <b>{esc(e["titel"])}</b> liegt in deinem TikTok-Postfach. Sound wählen und los! 🚀')


# ---------------------------------------------------------------- Instagram

def ig_token(z):
    ig = z.setdefault('instagram', {})
    tok = ig.get('token') or IG_TOKEN_SECRET
    if not tok:
        return ''
    mask(tok)
    if time.time() - ig.get('erneuert', 0) > 20 * 86400:       # Long-Lived-Token regelmäßig verlängern
        st, j = http('GET', 'https://graph.instagram.com/refresh_access_token?' +
                     urllib.parse.urlencode({'grant_type': 'ig_refresh_token', 'access_token': tok}))
        if isinstance(j, dict) and j.get('access_token'):
            mask(j['access_token'])
            ig['token'] = tok = j['access_token']; ig['erneuert'] = time.time()
            log('Instagram-Token verlängert.')
        else:
            log('Instagram-Token-Verlängerung nicht möglich:', (j.get('error') or {}).get('message') if isinstance(j, dict) else '')
            ig['erneuert'] = time.time() - 19 * 86400   # morgen nochmal versuchen
    return tok


def ig_pruefen(z):
    """Einmal pro Lauf: Ist der Instagram-Token brauchbar? (nur Form und Ergebnis, nie der Token selbst)"""
    if 'ig_check' in DIAG:
        return
    roh = IG_TOKEN_SECRET
    form = f'Länge {len(roh)}, beginnt mit {roh[:2]!r}' if roh else 'leer'
    tok = (z.get('instagram') or {}).get('token') or roh
    st, j = http('GET', IG_API + 'me?' + urllib.parse.urlencode({'fields': 'user_id,username', 'access_token': tok}))
    if isinstance(j, dict) and j.get('username'):
        DIAG['ig_check'] = f'ok: @{j["username"]} (Secret: {form})'
    else:
        DIAG['ig_check'] = f'Fehler: {((j.get("error") or {}).get("message") if isinstance(j, dict) else str(j)[:100])} (Secret: {form})'


def insta_text(c):
    """Instagram erlaubt seit Dez. 2025 höchstens 5 Hashtags – weitere fallen weg."""
    n = [0]
    def f(m):
        n[0] += 1
        return m.group(0) if n[0] <= 5 else ''
    return re.sub(r'\s*#\w+', f, c or '').strip()


def instagram(z):
    faellig = [e for e in z['beitraege'].values() if e.get('insta') == 'geplant' and e.get('vorschau', e.get('video')) and (e.get('insta_zeit') or '') <= jetzt()]
    if not faellig:
        return
    tok = ig_token(z)
    if not tok:
        if einmal_am_tag(z, 'ig_fehlt'):
            senden('⚠️ Instagram-Zugang fehlt (INSTAGRAM_TOKEN in GitHub).')
        return
    for e in faellig[:2]:
        video = e['video'] if e.get('art') == 'video' else e.get('vorschau', '')
        st, j = http('POST', IG_API + IG_ID + '/media', form={'media_type': 'REELS', 'video_url': video,
                                                              'caption': insta_text(e.get('caption', ''))[:2200], 'share_to_feed': 'true', 'access_token': tok,
                                                              **({'thumb_offset': '600'} if e.get('art') == 'video' else {})})
        cid = j.get('id') if isinstance(j, dict) else None
        status, grund = '', ''
        if cid:
            for _ in range(15):                                 # bis zu 5 Minuten warten, bis Instagram das Video verarbeitet hat
                time.sleep(20)
                st2, s = http('GET', IG_API + cid + '?' + urllib.parse.urlencode({'fields': 'status_code,status', 'access_token': tok}))
                status = (s.get('status_code') if isinstance(s, dict) else '') or ''
                if status in ('FINISHED', 'ERROR', 'EXPIRED'):
                    if status != 'FINISHED':
                        grund = (s.get('status') if isinstance(s, dict) else '') or status
                    break
            if status == 'FINISHED':
                st3, p = http('POST', IG_API + IG_ID + '/media_publish', form={'creation_id': cid, 'access_token': tok})
                if isinstance(p, dict) and p.get('id'):
                    e['insta'] = 'online'; e['insta_media_id'] = p['id']; e['insta_online'] = iso()
                    senden(f'📸 Online auf Instagram (Reel): <b>{esc(e["titel"])}</b>')
                    log('Instagram online:', e['id']); continue
                grund = (p.get('error') or {}).get('message') if isinstance(p, dict) else str(p)[:200]
            elif not grund:
                e['insta_versuche'] = e.get('insta_versuche', 0) + 1
                if e['insta_versuche'] < 3:
                    log('Instagram verarbeitet noch, nächster Lauf:', e['id']); continue
                grund = 'Instagram hat das Video nicht rechtzeitig verarbeitet.'
        else:
            grund = (j.get('error') or {}).get('message') if isinstance(j, dict) else str(j)[:200]
        e['insta'] = 'fehler'; e['insta_fehler'] = str(grund)[:500]
        senden(f'⚠️ Instagram-Upload für <b>{esc(e["titel"])}</b> hat nicht geklappt.\nGrund: {esc(str(grund)[:300])}\nClaude schaut es sich an.',
               reply_markup={'inline_keyboard': [[{'text': '📸 Jetzt nochmal versuchen', 'callback_data': f'instajetzt|{e["id"]}'}]]})
        log('Instagram-Fehler:', e['id'], grund)


# ---------------------------------------------------------------- Ablauf

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'run'
    z = lade_zustand()
    vorher = json.dumps(z, sort_keys=True)
    if not z['hinweise'].get('status_v3'):
        z['hinweise']['status_v3'] = True
    if not z['hinweise'].get('insta_knopf_v2'):        # einmalig: Insta-Knopf für schon freigegebene Posts nachreichen
        z['hinweise']['insta_knopf_v2'] = True
        for e in z['beitraege'].values():
            if e.get('tiktok') == 'entwurf' and e.get('insta') not in ('geplant', 'online') and (e.get('zeit') or '')[:10] >= jetzt()[:10]:
                senden(f'📸 <b>{esc(e["titel"])}</b> ist schon im TikTok-Postfach. Auch auf Instagram?', reply_markup=insta_knopf(e['id']))
    if z['hinweise'].pop('neustart', False):
        senden('ℹ️ Die Pipeline hat mit einem neuen Speicher angefangen (STATE_KEY wurde geändert). Bitte TikTok neu verbinden: schreib <code>/tiktok</code>.')
    if cmd == 'connect-start':
        tiktok_link(z)
    elif cmd == 'connect':
        tiktok_verbinden(z, sys.argv[2])
    elif cmd == 'insta-jetzt':                          # einen Beitrag sofort auf Instagram (wie der Knopf „Jetzt nochmal versuchen“)
        bid = (os.environ.get('BEITRAG') or (sys.argv[2] if len(sys.argv) > 2 else '')).strip()
        e = z['beitraege'].get(bid)
        if not e:
            log('Beitrag nicht gefunden:', bid)
        elif e.get('insta') != 'online':
            e['insta'] = 'geplant'; e['insta_zeit'] = jetzt(); e.pop('insta_versuche', None)
        durchlauf(z)
    elif cmd in ('loop', 'resend-offen'):
        if cmd == 'resend-offen':
            offene_neu_senden(z)
            speichere_zustand(z); schreibe_diagnose(z, cmd); sichern()
        # läuft ca. 55 Minuten und prüft jede Minute; GitHub startet alle 30 Minuten einen neuen Lauf (wartet in der Schlange)
        if json.dumps(z, sort_keys=True) != vorher:     # Änderungen vor dem Dauerlauf sofort sichern
            speichere_zustand(z); schreibe_diagnose(z, cmd); sichern()
        ende = time.time() + int(os.environ.get('PB_LOOP_MIN', '55')) * 60
        while True:
            vor = json.dumps(z, sort_keys=True)
            durchlauf(z)
            if json.dumps(z, sort_keys=True) != vor:
                speichere_zustand(z); schreibe_diagnose(z, cmd); sichern()
            if time.time() + 60 > ende:
                break
            time.sleep(60)
    else:
        durchlauf(z)
    if json.dumps(z, sort_keys=True) != vorher or not (STATE_DIR / 'state.enc').exists():
        speichere_zustand(z)
        log('Zustand gespeichert.')
    else:
        log('Nichts geändert.')
    schreibe_diagnose(z, cmd)


def durchlauf(z):
    for schritt in (telegram_lesen, neue_beitraege, tiktok_hochladen, erinnern, instagram, ig_pruefen):
        try:
            schritt(z)
        except Exception as e:
            log('Fehler in', schritt.__name__, type(e).__name__, e)
            DIAG['fehler'].append(f'{schritt.__name__}: {type(e).__name__}')


def schreibe_diagnose(z, cmd):
    STATE_DIR.mkdir(parents=True, exist_ok=True)   # öffentliche Lauf-Diagnose ohne Inhalte
    (STATE_DIR / 'lauf.json').write_text(json.dumps({'zeit': iso(), 'aktion': cmd, 'telegram': DIAG['telegram'], 'fehler': DIAG['fehler'][-10:],
        'secrets': {'telegram': bool(TG_TOKEN), 'tiktok_key': bool(TT_KEY), 'tiktok_secret': bool(TT_SECRET), 'instagram': bool(IG_TOKEN_SECRET)},
        'tiktok_verbunden': bool((z.get('tiktok') or {}).get('refresh_token')), 'offene_notizen': sum(1 for n in z['notizen'] if n.get('status') == 'offen'),
        'instagram_check': DIAG.get('ig_check', '')}, indent=1))


def sichern():
    """Zustand sofort in den Branch state pushen (für den Dauerlauf)."""
    import subprocess
    if not os.environ.get('GITHUB_ACTIONS'):
        return
    r = lambda *a: subprocess.run(['git', '-C', str(STATE_DIR), *a], capture_output=True, text=True)
    r('add', '-A')
    if r('diff', '--cached', '--quiet').returncode == 0:
        return
    r('commit', '-q', '-m', 'Zustand ' + iso())
    p = r('push', '-q', 'origin', 'HEAD:state')
    if p.returncode != 0:
        log('Push des Zustands fehlgeschlagen:', p.stderr[-200:])


if __name__ == '__main__':
    main()
