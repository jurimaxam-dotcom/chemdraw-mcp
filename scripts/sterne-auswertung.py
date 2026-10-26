#!/usr/bin/env python3
"""Report public star timestamps alongside rolling traffic deltas; no attribution."""

import argparse
import json
from datetime import datetime
from pathlib import Path


def instant(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def cell(value):
    return str(value if value is not None else "?").replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def delta(previous, current):
    before = {r["referrer"]: r for r in previous["referrers"]}
    after = {r["referrer"]: r for r in current["referrers"]}
    parts = []
    for name in sorted(before.keys() | after.keys()):
        # Abwesend heißt aus Top 10 gefallen, nicht zwingend null.
        a, b = before.get(name), after.get(name)
        if a is None or b is None:
            row = a or b
            change = -row["count"] if a else row["count"]
            parts.append(f"{cell(name)}: {change:+d} (Listen-Delta; {'entfallen' if a else 'neu'}, Bestand unbekannt)")
        else:
            parts.append(f"{cell(name)}: {b['count'] - a['count']:+d} Aufrufe / {b['uniques'] - a['uniques']:+d} Unique-Differenz")
    return "; ".join(parts) or "keine gelisteten Referrer"


def assessment(star):
    hints = []
    login = star["login"].lower()
    if "-bot" in login:
        hints.append("-bot im Login")
    if login.isdecimal():
        hints.append("rein numerisch")
    if star.get("created_at"):
        age = (instant(star["starred_at"]) - instant(star["created_at"])).days
        if age < 30:
            hints.append(f"Konto beim Stern {age} Tage alt (<30)")
    if star.get("public_repos") == 0:
        hints.append("0 Repos (öffentlich)")
    if hints:
        return "auffällig, Echtheit unklar: " + "; ".join(hints)
    if star.get("profile_error") or star.get("created_at") is None:
        return "unbekannt: Profil unvollständig"
    return "unauffällig; Echtheit nicht verifiziert"


def render_report(snapshots):
    snapshots = sorted(snapshots, key=lambda s: s.get("captured_at", s["datum"]))
    latest = snapshots[-1]
    lines = [f"# Sterne und Traffic · {latest['datum']}", "",
             "GitHub kennt keinen Referrer pro Stern. Zeitpunkt × Referrer-Delta × Profil sind nur eine Näherung, keine Zuordnung.",
             "Referrer sind rollierende 14-Tage-Aggregate (Top 10). Differenzen sind Nettoänderungen einschließlich herausfallender Tage, keine Tagesbesucher; auch Unique-Differenzen sind keine neuen Personen. Fehlende Referrer sind unbekannt, nicht null.",
             "Stern-Zeitpunkte und Messintervalle unten sind UTC; Dateinamen verwenden das lokale Snapshot-Datum. Das laufende Intervall ist unvollständig. Historische Sterne ohne passende Messung bleiben ohne zeitliche Abdeckung.",
             "Die Bewertung echt/unecht ist nicht beweisbar: Die Regeln markieren nur Hinweise, keine Bots oder gekauften Sterne. Kontoalter gilt beim Stern; Follower und öffentliche Repos beim Profilabruf. Private Repos sind unbekannt. Keine Bio-Texte im Bericht.", "",
             "Quellen: [GitHub Starring API](https://docs.github.com/en/rest/activity/starring#list-stargazers), [Traffic API](https://docs.github.com/en/rest/metrics/traffic).", "",
             "## Referrer-Snapshot-Differenzen", "",
             "| Messintervall | Nettoänderung |", "|---|---|"]
    pairs = list(zip(snapshots, snapshots[1:]))
    for previous, current in pairs:
        interval = f"{previous.get('captured_at', previous['datum'] + ' (Uhrzeit fehlt)')} → {current.get('captured_at', current['datum'] + ' (Uhrzeit fehlt)')}"
        lines.append(f"| {interval} | {delta(previous, current)} |")
    lines += ["", "## Öffentliche Stargazer der jüngsten Messung", ""]
    if latest.get("stargazers") is None:
        return "\n".join(lines + ["Stargazer-Abruf fehlgeschlagen oder nicht vorhanden; keine aktuelle Stern-Liste verfügbar.", ""])
    stars = sorted(latest["stargazers"], key=lambda s: (s["starred_at"], s["login"]))
    lines += [f"{len(stars)} Sterne erfasst; Profilstand: {latest.get('captured_at', latest['datum'])}.", "",
              "| Stern-Zeitpunkt (UTC) | Login | Passendes Referrer-Intervall / Delta | Profil | Bewertung echt/unecht |",
              "|---|---|---|---|---|"]
    for star in stars:
        matching = "keine zeitliche Abdeckung"
        for previous, current in pairs:
            if previous.get("captured_at") and current.get("captured_at") and instant(previous["captured_at"]) < instant(star["starred_at"]) <= instant(current["captured_at"]):
                matching = f"{previous['captured_at']} → {current['captured_at']}: {delta(previous, current)}"
                break
        profile = f"Konto seit {cell(star.get('created_at'))}; {cell(star.get('followers'))} Follower; {cell(star.get('public_repos'))} öffentliche Repos"
        lines.append(f"| {star['starred_at']} | {cell(star['login'])} | {matching} | {profile} | {assessment(star)} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traffic-dir", type=Path, default=Path.home() / ".local/share/chemdraw-mcp/traffic")
    parser.add_argument("--output", type=Path, help="Local Markdown report path (do not publish profiles).")
    args = parser.parse_args()
    snapshots = [json.loads(p.read_text()) for p in sorted(args.traffic_dir.glob("????-??-??.json"))]
    if not snapshots:
        parser.error("No traffic snapshots found")
    report = render_report(snapshots)
    if args.output:
        args.output.write_text(report)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
