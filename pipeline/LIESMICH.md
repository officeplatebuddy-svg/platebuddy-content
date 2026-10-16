# PlateBuddy-Pipeline (GitHub Actions)

Ersetzt n8n. Läuft alle 5 Minuten (ca. 7–23 Uhr Wiener Zeit) über `.github/workflows/pipeline.yml`:

1. **Telegram lesen**: Knöpfe Go / Neu / Verwerfen / 📸 Insta 19:00, Nachrichten mit `/claude …` oder Antworten auf den Bot (werden als Notizen gespeichert), `/tiktok` (Verbinden-Link) und `/tiktok CODE` (TikTok verbinden).
2. **Neue Beiträge**: jeder neue Ordner in `beitraege/` (Format siehe `beitraege/LIESMICH.md`) geht mit Vorschau und Knöpfen in die Telegram-Gruppe, sobald GitHub Pages ihn ausliefert.
3. **TikTok**: freigegebene Beiträge gehen direkt als Entwurf ins TikTok-Postfach (Content Posting API, PULL_FROM_URL). Zum Termin kommt „⏰ Jetzt posten“.
4. **Instagram**: mit 📸 vorgemerkte Beiträge gehen um 19:00 als Reel auf @platebuddy.app.

**Ein/Aus:** Die Pipeline läuft nur, wenn die Datei `pipeline/AKTIV` existiert.

**Zustand:** verschlüsselt in `state.enc` im Branch `state` (Schlüssel = Secret `STATE_KEY`). Öffentliche Kurzliste ohne Chat-Inhalte: `beitraege-status.json` im Branch `state`.

**Secrets** (Repo → Settings → Secrets and variables → Actions): `TELEGRAM_BOT_TOKEN`, `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `INSTAGRAM_TOKEN`, `STATE_KEY`. Werden nie ausgegeben; GitHub maskiert sie in den Logs.

**TikTok verbinden:** in Telegram `/tiktok` schreiben → Link öffnen, mit @plate.buddy bestätigen → Seite `tiktok-verbinden.html` zeigt `/tiktok CODE` → in Telegram senden. Die Pipeline hält den Zugang danach selbst frisch (Refresh-Token, 1 Jahr gültig).

**Instagram-Token** wird alle 20 Tage automatisch verlängert.
