#!/usr/bin/env python3
"""Hilfsskript für den News-Agenten (siehe _build/agent/news-agent.md).

Aufruf aus dem Wurzelverzeichnis des Repositorys:
  python3 _build/news_agent.py carry           offene Vorschläge aus origin/news-agent übernehmen
  python3 _build/news_agent.py known           bereits bekannte Links und Titel ausgeben
  python3 _build/news_agent.py add NEU.json    neue Beiträge prüfen, eintragen und Seiten bauen
  python3 _build/news_agent.py pr BODY.md      Pull Request von news-agent nach main öffnen oder finden
"""
import datetime
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
NEWS = ROOT / "_build" / "news.json"
REPO = "waetjen89/Abschlusswerkstatt.de"
BRANCH = "news-agent"
FIELDS = {"title", "source", "url", "type", "lang", "published", "summary"}
DROP_PARAMS = re.compile(r"^(utm_|fbclid|gclid|mc_|ref$|si$|feature$)")


def norm(url):
    """Vergleichbare Form eines Links: ohne Tracking-Parameter, Fragment und Schrägstrich am Ende."""
    p = urllib.parse.urlsplit(url.strip())
    host = p.netloc.lower().removeprefix("www.").removeprefix("m.")
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query) if not DROP_PARAMS.match(k)]
    if host in ("youtube.com", "youtu.be"):
        vid = dict(q).get("v") or p.path.strip("/").split("/")[-1]
        return f"youtube:{vid}"
    return f"{host}{p.path.rstrip('/')}" + (f"?{urllib.parse.urlencode(sorted(q))}" if q else "")


def load(text=None):
    data = json.loads(text) if text is not None else json.loads(NEWS.read_text(encoding="utf-8"))
    data.setdefault("entries", [])
    return data


def save(data):
    NEWS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def branch_data():
    """news.json im offenen Vorschlagszweig, falls vorhanden."""
    r = subprocess.run(["git", "show", f"origin/{BRANCH}:_build/news.json"], cwd=ROOT,
                       capture_output=True, text=True)
    return load(r.stdout) if r.returncode == 0 else {"entries": []}


def open_pr():
    r = subprocess.run(["gh", "api", f"repos/{REPO}/pulls?state=open&head=waetjen89:{BRANCH}"],
                       capture_output=True, text=True, check=True)
    prs = json.loads(r.stdout)
    return prs[0] if prs else None


def cmd_carry():
    """Noch nicht freigegebene Beiträge aus einem offenen Pull Request übernehmen."""
    if not open_pr():
        print("Kein offener Vorschlag, nichts zu übernehmen.")
        return
    data = load()
    have = {norm(e["url"]) for e in data["entries"]}
    pending = [e for e in branch_data()["entries"] if norm(e["url"]) not in have]
    data["entries"].extend(pending)
    save(data)
    print(f"{len(pending)} offene Beiträge übernommen.")


def cmd_known():
    data = load()
    rows = [{"title": e["title"], "url": e["url"], "added": e["added"]} for e in data["entries"]]
    print(json.dumps({"anzahl": len(rows), "bekannt": rows}, ensure_ascii=False, indent=1))


def validate(e, have):
    errs = []
    missing = FIELDS - e.keys()
    extra = e.keys() - FIELDS
    if missing:
        errs.append(f"fehlende Felder: {sorted(missing)}")
    if extra:
        errs.append(f"unbekannte Felder: {sorted(extra)}")
    if errs:
        return errs
    if not re.match(r"^https://", e["url"]):
        errs.append("url muss mit https:// beginnen")
    if norm(e["url"]) in have:
        errs.append("Link ist bereits veröffentlicht oder vorgeschlagen")
    if e["type"] not in ("artikel", "video"):
        errs.append("type muss artikel oder video sein")
    if e["lang"] not in ("de", "en"):
        errs.append("lang muss de oder en sein")
    if not (5 <= len(e["title"]) <= 180):
        errs.append("title muss 5 bis 180 Zeichen lang sein")
    if not (2 <= len(e["source"]) <= 80):
        errs.append("source muss 2 bis 80 Zeichen lang sein")
    if not (180 <= len(e["summary"]) <= 650):
        errs.append(f"summary muss 180 bis 650 Zeichen lang sein (ist {len(e['summary'])})")
    if e["published"] is not None:
        try:
            d = datetime.date.fromisoformat(e["published"])
            if d > datetime.date.today():
                errs.append("published liegt in der Zukunft")
        except ValueError:
            errs.append("published muss JJJJ-MM-TT oder null sein")
    return errs


def cmd_add(path):
    new = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if isinstance(new, dict):
        new = new.get("entries", [])
    data = load()
    have = {norm(e["url"]) for e in data["entries"]}
    today = datetime.date.today().isoformat()
    problems = []
    for i, e in enumerate(new, 1):
        errs = validate(e, have)
        if errs:
            problems.append(f"Beitrag {i} ({e.get('title', '?')}): " + "; ".join(errs))
            continue
        have.add(norm(e["url"]))
    if problems:
        print("Nicht eingetragen, bitte korrigieren:\n" + "\n".join(problems))
        sys.exit(1)
    for e in new:
        e = {k: (v.strip() if isinstance(v, str) else v) for k, v in e.items()}
        e["added"] = today
        e["id"] = f"{today}-{re.sub(r'[^a-z0-9]+', '-', e['title'].lower()).strip('-')[:48]}"
        data["entries"].append(e)
    save(data)
    subprocess.run([sys.executable, str(ROOT / "_build" / "build.py")], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL)
    print(f"{len(new)} Beiträge eingetragen, Seiten neu gebaut.")


def cmd_pr(body_path):
    pr = open_pr()
    if pr:
        print(f"Offener Pull Request aktualisiert: {pr['html_url']}")
        return
    today = datetime.date.today()
    title = f"News: Vorschläge vom {today.day}.{today.month}.{today.year}"
    r = subprocess.run(["gh", "api", f"repos/{REPO}/pulls", "-f", f"title={title}", "-f", f"head={BRANCH}",
                        "-f", "base=main", "-F", f"body=@{body_path}"],
                       capture_output=True, text=True, check=True)
    print(f"Neuer Pull Request: {json.loads(r.stdout)['html_url']}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("carry", "known", "add", "pr"):
        print(__doc__)
        sys.exit(2)
    cmd = sys.argv[1]
    if cmd in ("add", "pr") and len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    {"carry": lambda: cmd_carry(), "known": lambda: cmd_known(),
     "add": lambda: cmd_add(sys.argv[2]), "pr": lambda: cmd_pr(sys.argv[2])}[cmd]()
