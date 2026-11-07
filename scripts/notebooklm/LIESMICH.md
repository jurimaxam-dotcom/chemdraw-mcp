# NotebookLM-Quellpakete aus dem Repo

`python3 -I scripts/notebooklm/bundle.py . <zielordner>` baut aus HEAD drei Markdown-Quellen (Server-Code, Tests, Skripte/Evals/Build), jede Datei unverändert im Codeblock (sonst plättet NotebookLM die Einrückung). Ohne README, Doku, Pläne, Bilder, Lockfiles.

Notebook: https://notebooklm.google.com/notebook/06bc06da-c40c-46d3-9b2d-409eb935b37d — nach einem Release die drei Quellen per notebooklm-MCP (`source_delete` + `source_add`, `source_type=file`) austauschen.

Faktencheck-Regel: Keine NotebookLM-Aussage über den Code wandert in Plan oder README ohne grep/Test im Repo (Befund 07.11.: etwa ein Drittel der Code-Urteile falsch; Aussagen aus Webquellen meist richtig).
