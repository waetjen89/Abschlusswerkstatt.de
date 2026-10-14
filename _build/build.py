#!/usr/bin/env python3
"""Erzeugt die statischen Seiten der Abschlusswerkstatt.

Inhalte liegen in _build/pages/ (eine Datei je Seite mit Kopfangaben im ersten Kommentar).
Menüzeile, Bereichsleiste, Fußzeile und wiederverwendbare Bausteine kommen aus diesem Skript.

Aufruf aus dem Wurzelverzeichnis des Repositorys:  python3 _build/build.py
"""
import datetime
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ROOT / "_build" / "pages"
SITE = "Abschlusswerkstatt"
MAIL = "oliver.waetjen@abschlusswerkstatt.de"

# Menüstruktur: Oberkategorien mit Unterseiten
NAV = [
    {"key": "info", "label": "Info", "href": "/info"},
    {"key": "news", "label": "News", "href": "/news"},
    {
        "key": "agenten", "label": "Agenten", "href": "/agenten/",
        "explore": "Agenten entdecken",
        "blurb": "Agenten erledigen wiederkehrende Vorarbeit im Abschluss: Postfächer, Standardsetzer und "
                 "Unternehmensmeldungen. Die Entscheidungen bleiben bei Ihnen.",
        "children": [
            ("Übersicht", "/agenten/"),
            ("Email Agent", "/agenten/email-agent"),
            ("IFRS Updates", "/agenten/ifrs-updates"),
            ("Unternehmens Updates", "/agenten/unternehmens-updates"),
        ],
    },
    {
        "key": "analysen", "label": "Analysen", "href": "/analysen/",
        "explore": "Analysen entdecken",
        "blurb": "Fachliche Analysen zu Bilanzierungsfragen mit Gewicht, zuerst zu Unternehmenserwerben.",
        "children": [("Übersicht", "/analysen/"), ("M&A", "/analysen/m-und-a")],
    },
    {
        "key": "tools", "label": "Tools", "href": "/tools/",
        "explore": "Tools entdecken",
        "blurb": "Werkzeuge, die nachvollziehbar rechnen. Alle Berechnungen laufen in Ihrem Browser.",
        "children": [("Übersicht", "/tools/"), ("Leasingrechner", "/tools/leasingrechner")],
    },
    {"key": "ueber-mich", "label": "Über mich", "href": "/ueber-mich"},
]

MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember"]

ICON_MAIL = ('<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true">'
             '<rect x="2.5" y="4.5" width="15" height="11" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.3"/>'
             '<path d="M3 5.5l7 5.2 7-5.2" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/></svg>')
ICON_CHEVRON = ('<svg viewBox="0 0 12 12" width="12" height="12" aria-hidden="true">'
                '<path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.4" '
                'stroke-linecap="round" stroke-linejoin="round"/></svg>')
ICON_TICK = ('<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M3.5 10.8l4.2 4.2L16.8 4.6" fill="none" '
             'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def esc(s):
    return html.escape(s, quote=True)


# ---------- Beispielvertrag für die Vorschau des Leasingrechners ----------

def lease_example():
    """Gleiche Rechnung wie im Leasingrechner: 60 Monate, 4.500 EUR vorschüssig, 4,5 % p. a. konform."""
    term, pay, rate = 60, 4500.0, 4.5
    j = (1 + rate / 100) ** (1 / 12) - 1
    l0 = sum(pay / (1 + j) ** t for t in range(term))
    balances, bal = [l0], l0
    for _ in range(term):
        bal -= pay
        bal += bal * j
        balances.append(max(bal, 0.0))
    balances[-1] = 0.0
    return l0, balances


def de_money(v):
    s = f"{v:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def lease_svg(balances):
    w, h, top, bottom = 460, 132, 8, 104
    n = len(balances) - 1
    peak = balances[0]
    pts = [(i * w / n, bottom - (b / peak) * (bottom - top)) for i, b in enumerate(balances)]
    line = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    area = line + f" L{w} {bottom} L0 {bottom} Z"
    ex, ey = pts[-1]
    label = ("Verlauf der Leasingverbindlichkeit im Beispielvertrag: von "
             f"{de_money(peak)} € im Juli 2026 auf 0 € im Juni 2031")
    return (f'<svg class="lease-chart" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">'
            f'<path class="area" d="{area}"/>'
            f'<line class="base" x1="0" y1="{bottom}" x2="{w}" y2="{bottom}"/>'
            f'<path class="line" d="{line}"/>'
            f'<circle class="end" cx="{ex:.1f}" cy="{ey:.1f}" r="3"/>'
            f'<text x="0" y="{h - 4}">Juli 2026</text>'
            f'<text x="{w}" y="{h - 4}" text-anchor="end">Juni 2031</text></svg>')


# ---------- Wiederverwendbare Bausteine ----------

def components(today):
    l0, balances = lease_example()
    shift_items = [
        ("05:30", "Email Agent", "/agenten/email-agent",
         "Posteingang sortiert, Rückfragen von Tochtergesellschaften und Prüfern markiert, Antworten vorbereitet."),
        ("06:00", "IFRS Updates", "/agenten/ifrs-updates",
         "IASB, IFRS Interpretations Committee und EFRAG gesichtet, Neuerungen kurz eingeordnet."),
        ("06:30", "Unternehmens Updates", "/agenten/unternehmens-updates",
         "Neue Berichte und Meldungen der beobachteten Unternehmen ausgewertet."),
    ]
    shift = ['<ol class="shift" aria-label="Beispielhafter Morgen mit drei Agenten">']
    for time, name, href, text in shift_items:
        shift.append(
            f'<li class="shift-item"><time class="shift-time" datetime="{time}">{time}</time>'
            f'<span class="shift-dot" aria-hidden="true"></span>'
            f'<h3 class="shift-name"><a href="{href}">{esc(name)}</a></h3>'
            f'<p class="shift-text">{esc(text)}</p></li>')
    shift.append(
        '<li class="shift-item is-you"><time class="shift-time" datetime="08:00">08:00</time>'
        '<span class="shift-dot" aria-hidden="true"></span><h3 class="shift-name">Sie</h3>'
        '<p class="shift-text">Alles liegt bereit. Die Entscheidungen treffen Sie.</p></li>')
    shift.append('</ol><p class="shift-note">Beispielhafter Ablauf. Die Agenten befinden sich im Aufbau.</p>')

    ppa_rows = [
        ("Vermögenswerte", "ppa-assets", 0, 78),
        ("Schulden", "ppa-debt", 56, 22),
        ("Goodwill", "ppa-gw", 56, 44),
    ]
    ppa = ['<figure class="ppa"><div class="ppa-body">',
           '<span class="ppa-guide" style="--at:56" aria-hidden="true"></span>',
           '<span class="ppa-guide" style="--at:78" aria-hidden="true"></span>']
    for lab, cls, start, length in ppa_rows:
        ppa.append(f'<div class="ppa-row"><span class="ppa-lab">{lab}</span><span class="ppa-track">'
                   f'<span class="ppa-bar {cls}" style="--from:{start};--len:{length}"></span></span></div>')
    ppa.append('<div class="ppa-row ppa-total"><span class="ppa-lab">Kaufpreis</span><span class="ppa-track">'
               '<span class="ppa-bar" style="--from:0;--len:100"></span></span></div>')
    ppa.append('</div><figcaption class="ppa-cap">Schema einer Kaufpreisallokation nach IFRS 3</figcaption></figure>')

    lease = ('<div class="lease"><p class="lease-cap">Leasingverbindlichkeit bei Zugang</p>'
             f'<p class="lease-num">{de_money(l0)} €</p>{lease_svg(balances)}'
             '<p class="lease-meta">Beispielvertrag über 60 Monate mit 4.500 € Monatsrate und 4,50 % Zins</p></div>')

    checks_items = [
        ("Nachvollziehbar", "Jede Zahl mit Rechenweg und Quelle."),
        ("Abgestimmt", "Ergebnisse gegen Testfälle geprüft."),
        ("Datensparsam", "Werkzeuge rechnen in Ihrem Browser."),
    ]
    checks = '<ul class="checks">' + "".join(
        f'<li>{ICON_TICK}<div><strong>{a}</strong><span>{b}</span></div></li>' for a, b in checks_items) + '</ul>'

    sig = (f'<div class="sig"><p class="sig-place">Langwedel, im {MONTHS[today.month - 1]} {today.year}</p>'
           '<p class="sig-name">Oliver Wätjen</p></div>')

    return {
        "SHIFT": "".join(shift),
        "PPA": "".join(ppa),
        "LEASE": lease,
        "CHECKS": checks,
        "SIG": sig,
        "SOON": '<p class="status status-soon">In Vorbereitung</p>',
        "LIVE": '<p class="status status-live">Verfügbar</p>',
        "SOON_INLINE": '<span class="status status-soon">In Vorbereitung</span>',
        "LIVE_INLINE": '<span class="status status-live">Verfügbar</span>',
        "MAIL": MAIL,
    }


# ---------- Rahmen: Menüzeile, Bereichsleiste, Fußzeile ----------

def page_attr(href, url):
    return ' aria-current="page"' if href == url else ""


def current_attr(href, url, section_key, item_key):
    if href == url:
        return ' aria-current="page"'
    if section_key and section_key == item_key:
        return ' aria-current="true"'
    return ""


def global_nav(url, section):
    items = []
    for it in NAV:
        cur = current_attr(it["href"], url, section, it["key"])
        if "children" not in it:
            items.append(f'<li class="gn-item"><a class="gn-link" href="{it["href"]}"{cur}>{esc(it["label"])}</a></li>')
            continue
        fid = f'fly-{it["key"]}'
        links = "".join(
            f'<li><a href="{href}"{page_attr(href, url)}>{esc(label)}</a></li>'
            for label, href in it["children"])
        items.append(
            f'<li class="gn-item gn-has"><a class="gn-link" href="{it["href"]}"{cur}>{esc(it["label"])}</a>'
            f'<button class="gn-open" type="button" aria-expanded="false" aria-controls="{fid}">'
            f'<span class="sr">Untermenü {esc(it["label"])}</span>{ICON_CHEVRON}</button>'
            f'<div class="gn-fly" id="{fid}"><div class="gn-fly-in">'
            f'<div><p class="gn-fly-h">{esc(it["explore"])}</p><ul class="gn-fly-big">{links}</ul></div>'
            f'<div class="gn-fly-note"><p class="gn-fly-h">Kurz erklärt</p><p class="gn-fly-text">{esc(it["blurb"])}</p></div>'
            f'</div></div></li>')

    mobile = []
    for it in NAV:
        cur = current_attr(it["href"], url, section, it["key"])
        if "children" not in it:
            mobile.append(f'<li><a class="gm-link" href="{it["href"]}"{cur}>{esc(it["label"])}</a></li>')
            continue
        sid = f'gm-{it["key"]}'
        subs = "".join(
            f'<li><a href="{href}"{page_attr(href, url)}>{esc(label)}</a></li>'
            for label, href in it["children"] if href != it["href"])
        mobile.append(
            f'<li><div class="gm-row"><a class="gm-link" href="{it["href"]}"{cur}>{esc(it["label"])}</a>'
            f'<button class="gm-toggle" type="button" aria-expanded="false" aria-controls="{sid}">'
            f'<span class="sr">Unterseiten von {esc(it["label"])}</span>{ICON_CHEVRON}</button></div>'
            f'<ul class="gm-sub" id="{sid}" hidden>{subs}</ul></li>')

    home_cur = ' aria-current="page"' if url == "/" else ""
    return (
        '<header class="gn" id="gn"><nav class="gn-bar" aria-label="Hauptmenü">'
        f'<a class="gn-brand" href="/"{home_cur}><img class="gn-logo" src="/assets/logo.svg" alt="{SITE}" width="170" height="17"></a>'
        f'<ul class="gn-list">{"".join(items)}</ul>'
        f'<a class="gn-mail" href="mailto:{MAIL}"><span class="sr">E-Mail schreiben</span>{ICON_MAIL}</a>'
        '<button class="gn-burger" type="button" aria-expanded="false" aria-controls="gn-mobile" '
        'aria-label="Menü öffnen"><span></span><span></span></button></nav>'
        f'<div class="gm" id="gn-mobile" hidden><ul class="gm-list">{"".join(mobile)}</ul>'
        f'<p class="gm-foot"><a href="mailto:{MAIL}">{MAIL}</a></p></div></header>'
        '<div class="gn-curtain" id="gn-curtain" aria-hidden="true"></div>')


def local_nav(url, section):
    item = next((it for it in NAV if it["key"] == section and "children" in it), None)
    if not item:
        return ""
    links = "".join(
        f'<li><a href="{href}"{page_attr(href, url)}>{esc(label)}</a></li>'
        for label, href in item["children"])
    return (f'<nav class="ln" aria-label="{esc(item["label"])}"><div class="ln-in">'
            f'<a class="ln-title" href="{item["href"]}">{esc(item["label"])}</a>'
            f'<button class="ln-toggle" type="button" aria-expanded="false" aria-controls="ln-list">'
            f'<span class="sr">Seiten in {esc(item["label"])}</span>{ICON_CHEVRON}</button>'
            f'<ul class="ln-list" id="ln-list">{links}</ul></div></nav>')


def footer(today):
    cols = [("Info", [("Worum es hier geht", "/info")]), ("News", [("Aktuelles", "/news")])]
    for it in NAV:
        if "children" in it:
            cols.append((it["label"], it["children"]))
    cols.append(("Über mich", [("Oliver Wätjen", "/ueber-mich"), ("E-Mail schreiben", f"mailto:{MAIL}")]))
    cols.append(("Rechtliches", [("Impressum", "/rechtliches#impressum"), ("Datenschutz", "/rechtliches#datenschutz")]))
    colhtml = "".join(
        f'<div class="gf-col"><p class="gf-h">{esc(h)}</p><ul>'
        + "".join(f'<li><a href="{href}">{esc(label)}</a></li>' for label, href in links)
        + '</ul></div>' for h, links in cols)
    return (
        '<footer class="gf"><div class="gf-in">'
        '<p class="gf-note">Die Inhalte dieser Website dienen der Information und ersetzen keine Bilanzierungs-, '
        'Steuer- oder Rechtsberatung. Berechnungen ohne Gewähr.</p>'
        f'<nav class="gf-map" aria-label="Seitenübersicht">{colhtml}</nav>'
        f'<div class="gf-legal"><p>© {today.year} Oliver Wätjen. {SITE}</p>'
        '<ul><li><a href="/rechtliches#impressum">Impressum</a></li>'
        '<li><a href="/rechtliches#datenschutz">Datenschutz</a></li></ul></div>'
        '</div></footer>')


def page_html(meta, head_extra, body, today):
    url = meta["url"]
    section = meta.get("section", "")
    title = SITE if url == "/" else f'{meta["title"]} – {SITE}'
    return (
        '<!doctype html>\n<html lang="de">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        f'<title>{esc(title)}</title>\n'
        f'<meta name="description" content="{esc(meta.get("description", ""))}">\n'
        '<meta name="robots" content="noindex">\n'
        '<meta name="theme-color" content="#000000">\n'
        '<meta name="color-scheme" content="dark">\n'
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
        '<link rel="preload" href="/fonts/host-grotesk-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>\n'
        '<link rel="stylesheet" href="/assets/site.css">\n'
        f'{head_extra}'
        '</head>\n'
        f'<body class="page-{meta.get("slug", "x")}">\n'
        '<a class="skip" href="#main">Zum Inhalt springen</a>\n'
        f'{global_nav(url, section)}\n{local_nav(url, section)}\n'
        f'<main id="main">\n{body}\n</main>\n'
        f'{footer(today)}\n'
        '<script src="/assets/site.js" defer></script>\n'
        '</body>\n</html>\n')


def parse(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"\s*<!--(.*?)-->\s*", text, re.S)
    if not m:
        raise SystemExit(f"Kopfangaben fehlen in {path}")
    meta = {}
    for line in m.group(1).strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    rest = text[m.end():]
    head_extra = ""
    hm = re.search(r"<!--HEAD-->(.*?)<!--/HEAD-->", rest, re.S)
    if hm:
        head_extra = hm.group(1).strip() + "\n"
        rest = rest[:hm.start()] + rest[hm.end():]
    return meta, head_extra, rest.strip()


def main():
    today = datetime.date.today()
    comps = components(today)
    written = []
    for src in sorted(PAGES.rglob("*.html")):
        rel = src.relative_to(PAGES)
        meta, head_extra, body = parse(src)
        url = "/" + rel.as_posix()
        url = url[: -len("index.html")] if url.endswith("index.html") else url[: -len(".html")]
        meta["url"] = url
        meta.setdefault("slug", rel.as_posix().replace("/", "-").replace(".html", ""))
        body = re.sub(r"\{\{(\w+)\}\}", lambda m: comps[m.group(1)], body)
        out = ROOT / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page_html(meta, head_extra, body, today), encoding="utf-8")
        written.append(f"{rel.as_posix():40s} {url}")
    print("\n".join(written))


if __name__ == "__main__":
    main()
