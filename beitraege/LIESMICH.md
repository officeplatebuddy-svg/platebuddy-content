# Beiträge für TikTok und Instagram

Claude legt hier fertige Beiträge ab. n8n schaut alle 15 Minuten nach, schickt neue Beiträge zur Freigabe nach Telegram (Go / Neu / Verwerfen) und lädt sie nach dem Go zum Termin hoch.

Ein Ordner pro Beitrag: `beitraege/<kennung>/` (Kennung: nur Buchstaben, Zahlen, `-`, `_`; z. B. `2026-10-16-12-kuehlschrank`).

## `beitrag.json`

```json
{
  "titel": "Kühlschrank-Foto → Rezept",
  "art": "fotos",
  "termin": "2026-10-16T12:00",
  "beschreibung": "Text für TikTok/Instagram inkl. Hashtags",
  "plattformen": ["tiktok", "instagram"],
  "bilder": ["bild-01.jpg", "bild-02.jpg"],
  "video": "video.mp4",
  "vorschau": "vorschau.mp4",
  "sound": "Vorschlag für den TikTok-Sound (optional)",
  "status": "bereit"
}
```

- `art`: `fotos` (Slideshow, braucht `bilder`, JPG) oder `video` (braucht `video`, MP4).
- `termin`: Wiener Ortszeit, Format `JJJJ-MM-TTTHH:MM`. Leer = direkt nach dem Go.
- `vorschau`: MP4 für Telegram (bei Videos reicht das Video selbst).
- `status`: `entwurf` wird ignoriert, alles andere wird abgeholt.
- Alle Dateien werden über GitHub Pages ausgeliefert: `https://officeplatebuddy-svg.github.io/platebuddy-content/beitraege/<kennung>/<datei>`.

Ein Ordner wird nur einmal abgeholt. Für eine neue Version einen neuen Ordner mit neuer Kennung anlegen.
