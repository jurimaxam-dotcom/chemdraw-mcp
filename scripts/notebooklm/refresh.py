"""Tauscht die drei Code-Quellen im NotebookLM-Notebook gegen den Stand von HEAD.

Aufruf (aus dem Repo): python3 -I scripts/notebooklm/refresh.py [--dry-run]

Reihenfolge je Paket: erst die neue Quelle hochladen und auf „ready“ warten, dann die
alte löschen. Ist das Notebook voll (50 Quellen im Gratis-Konto), fliegt die alte Fassung
zuerst — bricht der Upload dann ab, fehlt dieses Paket bis zum nächsten Lauf.
Gelöscht werden nur Quellen, deren Titel genau einem Paketnamen entspricht
(1-server-code.md usw.); Webquellen, Bericht und Notizen bleiben unberührt.
Braucht die notebooklm-CLI (notebooklm-py) mit angemeldetem Profil.
"""
import datetime
import json
import os
import subprocess
import sys
import tempfile

NOTEBOOK = "06bc06da-c40c-46d3-9b2d-409eb935b37d"
PAKETE = ("1-server-code.md", "2-tests.md", "3-skripte-evals-build.md")
HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HIER))
DRY = "--dry-run" in sys.argv


def nlm(*args):
    out = subprocess.run(["notebooklm", "--quiet", *args, "-n", NOTEBOOK, "--json"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"notebooklm {' '.join(args)} fehlgeschlagen:\n{out.stderr or out.stdout}")
    return json.loads(out.stdout) if out.stdout.strip() else {}


def quellen():
    data = nlm("source", "list")
    return data.get("sources", data) if isinstance(data, dict) else data


commit = subprocess.check_output(["git", "-C", REPO, "log", "-1", "--format=%h"], text=True).strip()
alt = [s for s in quellen() if s.get("title") in PAKETE]
print(f"HEAD {commit}; alte Code-Quellen: {len(alt)}")

# realpath: auf macOS ist /var ein Symlink, die CLI verweigert Symlink-Pfade
ziel = os.path.realpath(tempfile.mkdtemp(prefix="nlm-bundle-"))
subprocess.run([sys.executable, "-I", os.path.join(HIER, "bundle.py"), REPO, ziel], check=True)
if DRY:
    sys.exit(f"--dry-run: Pakete in {ziel}, nichts hochgeladen")

neu = []
for p in PAKETE:
    vorher = [s for s in alt if s["title"] == p]
    try:
        r = nlm("source", "add", os.path.join(ziel, p), "--type", "file", "--title", p)
    except SystemExit:
        # Notebook voll (50 Quellen im Gratis-Konto): alte Fassung zuerst raus, dann erneut
        if not vorher:
            raise
        for s in vorher:
            nlm("source", "delete", s["id"], "-y")
            print("gelöscht (Platz)", p, s["id"])
        alt = [s for s in alt if s not in vorher]
        r = nlm("source", "add", os.path.join(ziel, p), "--type", "file", "--title", p)
    sid = (r.get("source") or r).get("id")
    if not sid:
        sys.exit(f"keine Quell-ID für {p}: {r}")
    neu.append(sid)
    print("hochgeladen", p, sid)
    nlm("source", "wait", sid, "--timeout", "600")
    for s in [s for s in alt if s["title"] == p and s["id"] != sid]:
        nlm("source", "delete", s["id"], "-y")
        print("gelöscht", p, s["id"])
    alt = [s for s in alt if s["title"] != p]
print("alle neuen Quellen ready")

datum = datetime.date.today().strftime("%d.%m.%Y")
nlm("rename", f"chemdraw-mcp — nur Code, Stand {datum} ({commit})")
print(f"Notebook umbenannt: Stand {datum} ({commit})")
