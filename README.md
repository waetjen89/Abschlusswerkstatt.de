# Abschlusswerkstatt.de

Statische Website zum Einsatz von KI in der Abschlusserstellung.

## Aufbau

- Inhalte je Seite: `_build/pages/` (Kopfangaben im ersten Kommentar, Bausteine wie `{{SHIFT}}` werden ersetzt)
- Menüzeile, Bereichsleiste, Fußzeile und Bausteine: `_build/build.py`
- Gestaltung und Verhalten: `assets/site.css`, `assets/site.js`
- Schrift: Host Grotesk, lokal in `fonts/` (SIL Open Font License)

Nach jeder Änderung an `_build/` die Seiten neu erzeugen:

    python3 _build/build.py

## Seiten

- `/` Startseite
- `/info`
- `/news` (Einträge aus `_build/news.json`)
- `/agenten/` mit `email-agent`, `ifrs-updates`, `unternehmens-updates`
- `/analysen/` mit `m-und-a`
- `/tools/` mit `leasingrechner` (rechnet vollständig im Browser)
- `/ueber-mich`, `/rechtliches`
- `/rechner` leitet auf `/tools/leasingrechner` weiter

## News-Agent

Ein wöchentlicher Agent schlägt drei Beiträge für `/news` vor. Er arbeitet nach
`_build/agent/news-agent.md`, nutzt `_build/news_agent.py` und legt seine Vorschläge als Pull Request
aus dem Zweig `news-agent` an. Veröffentlicht wird erst durch das Mergen des Pull Requests.

## Veröffentlichung

Cloudflare (Worker `abschlusswerkstatt-de`) übernimmt jeden Push auf `main` automatisch.
Solange die Seite noch nicht freigegeben ist, ist auf allen Seiten `noindex` gesetzt.
