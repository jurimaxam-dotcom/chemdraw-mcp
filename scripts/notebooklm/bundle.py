import os
import subprocess
import sys

repo, out = sys.argv[1], sys.argv[2]
head = subprocess.check_output(["git","-C",repo,"log","-1","--format=%h %cd"],text=True).strip()
files = subprocess.check_output(["git","-C",repo,"ls-tree","-r","--name-only","HEAD"],text=True).split()
SKIP_EXT = {".json",".lock",".html",".png",".jpg",".svg",".cdxml",".cdx",".mol",".sdf",".ico",".gif",".pdf",".mcpb",".zip"}
SKIP_PATH = ("chemdraw_tool/ui/dist/","docs/","plans/","node_modules/",".github/ISSUE_TEMPLATE/")
SKIP_EXT |= {".md"}
SKIP_FILES = {"LICENSE","glama.json",".gitignore"}
keep_json = {"server.json","glama.json","pyproject.toml","package.json","manifest.json"}
groups = {"1-server-code":[], "2-tests":[], "3-skripte-evals-build":[]}
skipped=[]
for f in files:
    ext = os.path.splitext(f)[1].lower()
    if (ext in SKIP_EXT and os.path.basename(f) not in keep_json) or f.startswith(SKIP_PATH) or f=="uv.lock" or f in SKIP_FILES:
        skipped.append(f)
        continue
    try:
        txt = subprocess.check_output(["git","-C",repo,"show",f"HEAD:{f}"]).decode("utf-8")
    except Exception:
        skipped.append(f)
        continue
    g = ("1-server-code" if f.startswith("chemdraw_tool/") else "2-tests" if f.startswith("tests/")
         else "3-skripte-evals-build")
    groups[g].append((f,txt))
os.makedirs(out,exist_ok=True)
for g,items in groups.items():
    body = [f"# chemdraw-mcp — nur Code, keine Doku/README/Pläne ({g}), Stand Commit {head}\n# Jede Datei steht unverändert im Codeblock unter ihrer Überschrift „DATEI: Pfad“\n\nInhaltsverzeichnis:\n" + "\n".join(f"- {f}" for f,_ in items) + "\n"]
    for f,t in items:
        body.append(f"\n## DATEI: {f}\n\n````````{os.path.splitext(f)[1].lstrip('.') or 'text'}\n{t}\n````````\n\nENDE: {f}\n")
    s="".join(body)
    open(f"{out}/{g}.md","w").write(s)
    print(g, len(items), "Dateien", len(s), "Zeichen", len(s.split()), "Wörter")
open(f"{out}/ausgelassen.txt","w").write("\n".join(skipped))
print("ausgelassen", len(skipped))
