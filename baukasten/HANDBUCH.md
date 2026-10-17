# PlateBuddy Content-Handbuch (ab 17.10.2026)

Grundlage: Recherche vom 17.10.2026 (Metricool TikTok-Studie 2026, Instagram/Mosseri, TikTok Next 2026, Food-App-Fallbeispiele). Pascal: „Mach die Videos jetzt immer so nach Plan, dass es funktioniert.“

## Die Kurzfassung

1. **Video vor Slideshow.** Auf TikTok holen Videos laut Metricool 2026 etwa 5× mehr Reichweite als Foto-Posts. Mindestens 70 % der Posts sind 9:16-Kurzvideos (7–20 s), gebaut mit `baue_video.py`. Slideshows (3:4, `baue.py`) höchstens 4 pro Woche, vor allem für Listen zum Speichern.
2. **App als Pointe, nicht als Werbung.** Erst ein Alltagsproblem, dann die App als Auflösung. App-Szenen 15–30 % der Laufzeit, „PlateBuddy“ höchstens einmal pro Video, am liebsten im letzten Drittel.
3. **Hook in Bild 1, sichtbar ab Frame 0, mit Bewegung.** Höchstens 8–10 Wörter. Thema nach 3 s klar. Alle 1–2 s passiert etwas.
4. **Ein Grund zum Weiterschicken** (Instagram rankt Nicht-Follower nach Sends): „schick das deiner WG / deinem Schatz / deiner Mama“, „markier die Person, die …“.
5. **Ein Suchwort** im Bild und als Anfang der Caption: „Was koche ich heute“, „Was essen wir heute“, „Reste verwerten“, „günstig kochen Studenten“, „Meal Prep Woche“, „Kühlschrank leer Rezept“, „Wochenplan“, „Einkaufsliste“.
6. **Eine konkrete Frage** in der Caption (+26 % Kommentare auf TikTok, +37 % auf Instagram laut Metricool).
7. **3–5 Hashtags**, immer #platebuddy (Instagram erlaubt höchstens 5; die Pipeline kürzt sonst).
8. **Ende mit Loop oder Cliffhanger** („egal 🙂“ → zurück zum Anfang; „Tag 2 morgen“).
9. **Echt statt KI-Look:** nur echte Screenshots aus `screens/` und Gerichtfotos aus `food/`. Keine KI-Bilder von Essen oder Personen.

## Ansprache

- Du (eine Person) bzw. ihr (WG, Paar). Nie „Sie“, nie Werbesprech („Entdecke jetzt“, „Revolution“, „Hey Foodies“).
- PlateBuddy klingt wie ein ehrlicher, leicht chaotischer Mitbewohner: frech, selbstironisch, nie von oben herab.
- Hooks klein geschrieben wie ein echter Post, einzelne Wörter in CAPS („wer hat MEINEN topfen gegessen“).
- Standarddeutsch als Basis, Wienerisch als Würze und Kommentar-Köder: Paradeiser/Tomate, Topfen/Quark, Erdäpfel/Kartoffeln, Karfiol/Blumenkohl, Fisolen, Marille, Schlagobers, Faschiertes, Palatschinken, Sackerl, Jänner. Liebevoll, nie „die Deutschen sind dumm“.
- Jugendsprache nur sparsam und ironisch. 1–3 Emojis in der Caption, im Video wenige.
- Kalorien nur als neutrale Nebeninfo. Kein Diät- oder Körperdruck.
- Bis zum Launch: „Schreib ‚ich‘, wir sagen dir, wenn PlateBuddy im App Store ist.“ statt „Jetzt laden“.

## Content-Säulen

| Säule | Anteil | Formate | Ziel |
|---|---|---|---|
| 1 Küchen-Alltag & Humor (WG, Paar, Studi, Mama) | 30 % | Chat-Video, POV, „Niemand redet darüber …“, Geständnis | Sends, Reichweite |
| 2 Kühlschrank-Rettung (App in Aktion) | 25 % | Kühlschrank → Gericht, App-Demo, Kommentar-Antwort, 7-Tage-Challenge | Produkt verstehen, „ich“-Kommentare |
| 3 Budget & Planung | 20 % | Monatsende, Wochenplan, Einkaufsliste vs. Realität (Notizen-Stil), Vorrat | Saves, Suche |
| 4 Food-Visual & Rezepte | 15 % | Gerichtfotos mit Zoom, Listen „5 Gerichte unter 2 €“, Saison | Saves, Suche |
| 5 Debatte & Community | 10 % | Paradeiser vs. Tomate, Rankings/Tier-List, Umfragen | Kommentare |

Zwei Posts pro Tag, 12:00 und 19:30 (Abendessen-Entscheidung). Die beiden Posts eines Tages haben verschiedene Säulen und Formate.

| Tag | 12:00 | 19:30 |
|---|---|---|
| Mo | Wochenplan-Demo (3) | WG-Chat-Video (1) |
| Di | Kühlschrank → Gericht (2) | POV-Video (1) |
| Mi | Rezept-Visual/Liste (4) | Wortstreit/Ranking (5) |
| Do | Budget-Liste „unter 2 €“ (3, Slideshow ok) | Paar-Chat/POV (1) |
| Fr | Kühlschrank → Gericht (2) | „Niemand redet darüber …“ (1) |
| Sa | Food-Visual-Liste (4, Slideshow ok) | Geständnis/Meme (1) |
| So | „Sonntag planen“-Demo (3) | Challenge-Folge oder Kommentar-Antwort (2) |

## Video-Typen (Aufbau Sekunde für Sekunde)

- **Chat-Video (iMessage dunkel), 12–16 s:** Hook-Box oben ab Frame 0 → Nachrichten ploppen alle 0,5–0,7 s auf (Eskalation, „tippt …“) → Wisch zur App-Lösung (Screenshot im Handy, 2–3 s) → zurück in den Chat mit Pointe → „schick das …“ + kleiner Abspann. Muster: `posts/2026-10-17-20-egal`.
- **Kühlschrank → Gericht, 8–15 s:** „was ich hatte:“ (Zutaten-Labels poppen) → Scan-Screenshot (41) mit Tap-Puls → Gerichtfoto groß mit Zoom, „was ich gegessen hab:“ → „15 min · 0 € extra“ → „und du?“ (Loop).
- **POV, 6–10 s:** „pov: es ist der 28. und du hast 11 €“ über unscharfem Foto → Pointe-Zeile → App-Screen → Ergebnis → Loop.
- **App-Demo, 12–20 s:** Ergebnis zuerst + Hook („meine ganze woche. 40 sekunden.“) → 3 nummerierte Schritte mit Screenshots, Handy wischt/scrollt, Tap-Puls → Ergebnis-Zoom → Frage.
- **Liste/Ranking, 10–16 s:** Titel mit Zahl → je Punkt 1,5–2,5 s, Platz 1 als Überraschung mit App-Moment → „welches zuerst?“.
- **Notizen-Stil, 6–12 s:** gelbe Notiz tippt sich („einkaufsliste: milch, brot“) → „was ich gekauft hab:“ → Durchstreichen → PlateBuddy-Liste als Pointe → „ertappt?“.
- **Wortstreit, 6–12 s:** „sag mir, wie du DAS nennst“ → Optionen ploppen → Pointe („PlateBuddy versteht beides. deine oma nicht.“) → Frage.
- **Kommentar-Antwort:** wird automatisch gebaut, Pascal lädt es in TikTok über „Mit Video antworten“ hoch (sonst fehlt der Kommentar-Sticker).
- **Serien:** „Tag X/7: die App entscheidet“, „Ihr schickt 3 Zutaten, wir machen das Rezept“, „Countdown bis zum Launch“. Immer „Teil X“ in Hook und Titel.
- Sprechende KI-Lebensmittel höchstens 1× im Monat als gekennzeichneter Test.

## Hook-Vorlagen (Auswahl)

Relatability: „ich, 19:47, kühlschrank offen, als würde sich was ändern“ · „jede WG hat diese eine person, die nie einkauft“ · „wenn du ‚nur kurz‘ einkaufen gehst und mit 47 € rauskommst“ · „monatsende-ich vs. monatsanfang-ich beim einkaufen“ · „der zucchini, den ich vor 2 wochen ‚für was gesundes‘ gekauft hab:“
Neugier: „ich hab meinen leeren kühlschrank fotografiert. das kam raus:“ · „3 zutaten, 0 plan, 15 minuten“ · „was 11 € am 28. wirklich hergeben“ · „ich hab meine ganze woche in 40 sekunden geplant“
Kontroverse: „paradeiser oder tomate. falsche antworten werden gelöscht.“ · „topfen und quark sind NICHT dasselbe“ · „meal prep ist überbewertet. sorry.“
Zahl/Liste: „5 gerichte unter 2 € pro portion, die nicht nach armut schmecken“ · „4 dinge, die du mit übrigem reis machen kannst (nr. 3 ist illegal gut)“ · „7 abendessen, 1 einkauf, 0 diskussionen“
POV: „pov: dein mitbewohner kocht zum ersten mal ‚was richtiges‘“ · „pov: du hast 3 eier, einen halben karfiol und hoffnung“ · „pov: deine mama fragt, ob du g'scheit isst“ · „pov: prüfungswoche und dein essensplan ist toast“
Niemand redet darüber: „… dass ‚was essen wir heute?‘ die anstrengendste frage jeder beziehung ist“ · „… wie viel geld in einer WG-küche verschimmelt“ · „… dass einkaufslisten in whatsapp-gruppen sterben“
Geständnis: „geständnis: ich hab 3 gläser pesto gekauft, weil ich vergessen hab, dass ich 2 hab“ · „ich war der mitbewohner, der den topfen gegessen hat. es tut mir leid.“

## Saisonkalender

bis 31.10. Kürbis, Halloween („gruseligster WG-Kühlschrank“) · ~25.–31. jedes Monats Monatsende-Budget · 1.11. Allerheiligen (Vorrat) · 11.11. Martini · Nov. Zwischenprüfungen, Lernessen · 27.11. Black Friday („-100 % auf Essen, das schon in deinem Kühlschrank liegt“) · ab 29.11. Advent, Kekse (Vanillekipferl: Mandeln oder Nüsse?) · ~18.–23.12. Kühlschrank leeren vor dem Heimfahren · 24.–26.12. Reste · 31.12./1.1. Raclette-Reste, Katerfrühstück · Jänner: Vorsätze („öfter selber kochen“), Veganuary, Dry January · Ende Jänner Prüfungszeit (AT).

## Checkliste für jeden Post (Pipeline)

- Video: 1080×1920, 30 fps, H.264 + AAC, 7–20 s, Bewegung ab Frame 0, kein Wasserzeichen. `baue_video.py` meldet „ausserhalb des sicheren Bereichs: nichts“.
- Text nur in `.safe` (x 60–920, y 150–1420). Höchstens 2 Zeilen pro Einblendung, ca. 1 s Standzeit pro 3 Wörter.
- Problem vor Produkt, App-Anteil ≤ 30 % (außer Demos), mindestens ein echter Screenshot oder ein echtes Gerichtfoto.
- Keine erfundenen Zahlen, Testimonials, Preise, „Jetzt laden“, „Link in Bio“, „kostenlos“, Pro, fremde Marken oder echte Personen.
- Caption: erster Satz mit Suchwort, genau eine Frage, ein Schick-/Speicher-Anlass, 3–5 Hashtags inkl. #platebuddy.
- `_bogen.jpg` ansehen und mindestens zwei Einzelbilder in voller Größe prüfen.
- Abwechslung: kein Screenshot/Gericht zweimal hintereinander; 38/39 (Hähnchen-Pfanne) und 11 nie.
