# News-Agent der Abschlusswerkstatt

Dieser Agent läuft einmal pro Woche als geplante Aufgabe. Er sucht im Internet nach neuen Artikeln und
Videos zur Schnittstelle von künstlicher Intelligenz und Accounting, wählt **genau drei** davon aus,
schreibt zu jedem eine kurze Zusammenfassung auf Deutsch und legt sie als Pull Request zur Freigabe an.
Veröffentlicht wird erst, wenn Oliver Wätjen den Pull Request auf GitHub zusammenführt. Der Agent führt
selbst **niemals** etwas mit `main` zusammen und pusht **niemals** direkt auf `main`.

Repository: https://github.com/waetjen89/Abschlusswerkstatt.de (Website abschlusswerkstatt.de)

## 1. Vorbereiten

```bash
cd /home/claude/abschlusswerkstatt.de 2>/dev/null || git clone https://github.com/waetjen89/Abschlusswerkstatt.de.git /home/claude/abschlusswerkstatt.de && cd /home/claude/abschlusswerkstatt.de
git fetch origin --prune
git checkout -B news-agent origin/main
python3 _build/news_agent.py carry     # übernimmt noch nicht freigegebene Vorschläge
python3 _build/news_agent.py known     # Liste aller veröffentlichten und vorgeschlagenen Beiträge
```

Lässt sich das Repository nicht klonen oder später nicht pushen, das Repository mit dem Werkzeug
`add_repo` (owner `waetjen89`, repo `Abschlusswerkstatt.de`, access `push`) zur Sitzung hinzufügen und
erneut versuchen.

## 2. Suchen

Zeitraum: Veröffentlichungen der **letzten 14 Tage** (für Videos bis 30 Tage). Suche auf Deutsch und
Englisch, zum Beispiel nach: KI Rechnungswesen, KI Abschlusserstellung, KI Wirtschaftsprüfung,
generative AI accounting, AI financial reporting, AI audit, AI IFRS, AI financial close, agentic AI
finance, LLM accounting, AI controlling. Für Videos gezielt YouTube und Konferenzaufzeichnungen
durchsuchen.

Gute Quellen sind unter anderem: Fachzeitschriften und Fachportale (zum Beispiel Haufe, NWB, Der Betrieb,
WPg, Journal of Accountancy, ICAEW, ACCA, IFAC), Prüfungs- und Beratungsgesellschaften, die IFRS
Foundation, Standardsetzer und Aufsichtsbehörden, Hochschulen und Forschungseinrichtungen, große
Wirtschaftsmedien sowie bekannte Praktiker mit fachlich fundierten Beiträgen.

## 3. Auswählen

Ein Beitrag kommt nur in Frage, wenn **alle** Punkte erfüllt sind:

- Er behandelt KI konkret im Zusammenhang mit Rechnungslegung, Abschlusserstellung, Konzernrechnungswesen,
  Abschlussprüfung, Controlling oder Finanzberichterstattung.
- Er ist fachlich fundiert und bietet Lesern aus dem Rechnungswesen einen Erkenntnisgewinn.
- Er ist ohne Bezahlschranke und ohne Registrierung zugänglich.
- Er ist **keine Werbung**: keine Produktankündigungen, Pressemitteilungen oder Verkaufsseiten von
  Softwareanbietern, keine Webinar-Anmeldeseiten.
- Er ist nicht bereits veröffentlicht oder vorgeschlagen (Liste aus `known`) und behandelt nicht dieselbe
  Nachricht wie ein Beitrag der letzten vier Wochen.
- Kein Bezug auf den Arbeitgeber von Oliver Wätjen und keine Beiträge über einzelne Personen aus seinem
  Umfeld.

Wähle aus den geeigneten Funden **genau drei** aus. Bevorzuge Vielfalt: unterschiedliche Quellen und
Themen, nach Möglichkeit eine Mischung aus deutsch- und englischsprachigen Beiträgen und, wenn ein gutes
Video dabei ist, ein Video. Finden sich weniger als drei geeignete Beiträge, lieber weniger vorschlagen als
die Kriterien aufweichen, und das im Pull Request vermerken.

## 4. Prüfen

Jeden ausgewählten Link **mit dem Web-Fetch-Werkzeug tatsächlich abrufen** und den Inhalt lesen. Die
Zusammenfassung darf nur wiedergeben, was im abgerufenen Beitrag steht. Lässt sich ein Link nicht
abrufen, ist er weitergeleitet auf eine andere Seite oder hinter einer Bezahlschranke, den Beitrag
verwerfen. Bei Videos genügen Titel, Beschreibung und, falls verfügbar, Kapitel oder Transkript.

## 5. Schreiben

Je Beitrag ein Objekt mit genau diesen Feldern, alle Beiträge zusammen als JSON-Liste in einer Datei im
Scratchpad:

```json
[
  {
    "title": "Originaltitel des Beitrags, unverändert",
    "source": "Name der Quelle, z. B. Journal of Accountancy oder YouTube-Kanalname",
    "url": "https://… (kanonischer Link ohne Tracking-Parameter)",
    "type": "artikel",
    "lang": "en",
    "published": "2026-10-12",
    "summary": "Zwei bis drei Sätze auf Deutsch."
  }
]
```

- `type`: `artikel` oder `video`. `lang`: Sprache der Quelle, `de` oder `en`.
- `published`: Veröffentlichungsdatum laut Quelle im Format JJJJ-MM-TT, oder `null`, wenn keins angegeben ist.
- `summary`: 180 bis 650 Zeichen, zwei bis drei Sätze, sachlich, in eigenen Worten. Kernaussage und
  wichtigste Ergebnisse, keine Wertung, keine Superlative, keine wörtlichen Zitate, keine erfundenen
  Zahlen. Siezen, keine Ich-Form. Englische Fachbegriffe nur, wo sie im Deutschen üblich sind.

Dann eintragen (das Skript prüft die Felder und baut die Seiten neu):

```bash
python3 _build/news_agent.py add <pfad-zur-json-datei>
```

Meldet das Skript Fehler, die Angaben korrigieren und erneut aufrufen.

## 6. Zur Freigabe vorlegen

```bash
git add -A
git -c user.name="waetjen89" -c user.email="waetjen89@users.noreply.github.com" commit -m "News: Vorschläge vom <Datum>"
git push --force https://github.com/waetjen89/Abschlusswerkstatt.de.git news-agent
python3 _build/news_agent.py pr <pfad-zur-pr-beschreibung.md>
```

Die Pull-Request-Beschreibung (Markdown) enthält je vorgeschlagenem Beitrag: Titel, Quelle, Link,
Sprache und die Zusammenfassung, dazu eine Zeile, warum der Beitrag ausgewählt wurde. Am Ende ein Hinweis:
„Zum Veröffentlichen den Pull Request mergen. Einzelne Beiträge entfernen: in `_build/news.json` löschen
und `python3 _build/build.py` ausführen, oder Claude darum bitten.“

Wenn bereits ein offener Pull Request aus `news-agent` existiert, wird er durch den Push aktualisiert
und enthält dann die alten und die neuen Vorschläge. Das ist so gewollt.

## 7. Abschluss

Die letzte Antwort des Laufs ist eine kurze Zusammenfassung auf Deutsch für Oliver: die drei Beiträge mit
Titel und Quelle und der Link zum Pull Request. Sie wird ihm als Benachrichtigung zugestellt. Gab es
Probleme, etwa keine geeigneten Beiträge oder einen fehlgeschlagenen Push, steht das dort ebenfalls.

## Grenzen

- Nur `_build/news.json` und die vom Build-Skript erzeugten Dateien ändern. Keine anderen Inhalte,
  Styles oder Skripte anfassen.
- Keine Vorschaubilder, eingebetteten Videos oder Inhalte Dritter übernehmen, nur verlinken.
- Niemals nach `main` pushen oder Pull Requests mergen.
