# Entwürfe für Sichtbarkeit (nur Entwürfe — Jay sendet selbst)

Stand 03.10.2026: 18 Sterne, Release 0.4.8, Discussions an. Keine Zahl und keine Behauptung hier,
die nicht im Repo belegt ist. Vor dem Absenden: Bild oder GIF anhängen (`assets/demo.gif`,
`assets/pk-curve.png`), die Regeln der jeweiligen Plattform lesen (Selbstwerbung, Flair).

## 1. Reddit — r/ClaudeAI (oder r/mcp), Englisch

**Titel:** I built an MCP server that draws chemistry in Claude Desktop (structures, mechanisms, pharmacokinetics) — free, runs locally

Body:

> I'm a student and got tired of clicking hexagons for lab reports, so I built an MCP server for
> Claude Desktop: say "draw ibuprofen and naproxen side by side and mark the differences" and you get
> a print-ready PNG/SVG plus an interactive panel in the chat.
>
> It also does curved-arrow mechanisms, TLC plates, titration curves, and — new this week — the
> pharmacology curves a course keeps asking for (concentration over time up to steady state,
> dose-response with a competitive antagonist) with the working next to the figure.
>
> Rendering is local (RDKit), no API key, no sign-up, Apache-2.0. Install is one double-click
> (.mcpb extension). Wrong chemistry is the thing I care most about, so if you see a wrong
> structure or number, please tell me — there is a bug template that asks for the compound.
>
> https://github.com/jurimaxam-dotcom/chemdraw-mcp
>
> What would you want it to draw or calculate for your course?

## 2. Fachschaft / Lerngruppe (Pharmazie), Deutsch — kurz

> Hey, ich habe ein Werkzeug für Claude Desktop gebaut, das Strukturformeln, Mechanismen und
> Pharmakokinetik-Kurven zeichnet und dazu den Rechenweg zeigt (Halbwertszeit, Steady State,
> Ionisierung bei gegebenem pH). Kostenlos, läuft lokal, kein Account.
> Installieren: Datei laden und doppelklicken → https://github.com/jurimaxam-dotcom/chemdraw-mcp/releases/latest
> Wenn euch etwas fehlt (eine Prüfungsfrage, die ihr von Hand rechnen müsst), schreibt mir die Aufgabe —
> daraus baue ich als Nächstes. Falsche Strukturen bitte melden, die sind mir am wichtigsten.

## 3. Eintrag für eine awesome-mcp-Liste (Pull-Request-Text)

Zeile:

> - [chemdraw-mcp](https://github.com/jurimaxam-dotcom/chemdraw-mcp) - Draw chemistry from chat: names or SMILES to publication-style structures, reaction schemes, curved-arrow mechanisms, lab graphics and pharmacokinetics. Local RDKit rendering, Claude Desktop extension.

PR-Beschreibung:

> Adds chemdraw-mcp (Apache-2.0, on PyPI and the MCP registry, one-click .mcpb install). Listed under Science / Education.
> I'm the author.

## 4. Erster Beitrag in Discussions (Show and tell)

**Titel:** What did you draw or calculate this week?

> Post a screenshot or the prompt you used, and what it got wrong if anything. I read all of them.
> If it saved you time on a lab report or an exam prep, say which subject — that decides what gets built next.

## Reihenfolge, die ich empfehle

1. Nr. 4 zuerst (kostet nichts, Seite sieht belebt aus), 2. Nr. 2 (die Zielgruppe), 3. Nr. 1, 4. Nr. 3.
Zwischen den Posts mindestens einen Tag Abstand, damit Rückmeldungen einsortiert werden können.
