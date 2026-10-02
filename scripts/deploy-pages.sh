#!/bin/sh
# Veröffentlicht den Praktikumsrechner für den KOSTENLOSEN Nutzertest auf GitHub
# Pages (Branch gh-pages). Öffentlich — nur auf Jays Ansage ausführen.
#
# Nicht für den Verkauf: GitHub Pages verbietet kommerzielle Transaktionen
# (docs/produkt/recht-steuer-zahlung-2026-10.md). Dafür Cloudflare Pages.
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/scripts/build-web.sh"
TMP="$(mktemp -d)"
trap 'git -C "$ROOT" worktree remove --force "$TMP" 2>/dev/null || true' EXIT
if git -C "$ROOT" ls-remote --exit-code --heads origin gh-pages >/dev/null 2>&1; then
  git -C "$ROOT" fetch -q origin gh-pages
  git -C "$ROOT" worktree add -q "$TMP" origin/gh-pages
  git -C "$TMP" checkout -q -B gh-pages
else
  git -C "$ROOT" worktree add -q --detach "$TMP"
  git -C "$TMP" checkout -q --orphan gh-pages
  git -C "$TMP" rm -rqf .
fi
mkdir -p "$TMP/rechner"
cp -R "$ROOT/web/dist/." "$TMP/rechner/"
touch "$TMP/.nojekyll"   # sonst ignoriert Pages Ordner mit Unterstrich (python_stdlib …)
git -C "$TMP" add -A
git -C "$TMP" commit -q -m "Praktikumsrechner $(git -C "$ROOT" rev-parse --short HEAD)" || echo "nichts Neues"
git -C "$TMP" push -q origin gh-pages
gh api -X POST "repos/{owner}/{repo}/pages" -f "source[branch]=gh-pages" -f "source[path]=/" >/dev/null 2>&1 || true
echo "Veröffentlicht. In 1–2 Minuten: https://$(gh api user --jq .login).github.io/$(basename "$(git -C "$ROOT" rev-parse --show-toplevel)")/rechner/"
