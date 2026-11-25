# Remote MCP Connector (Pilot)

`chempane.remote` is a standalone, stateless **Streamable HTTP** entrypoint for hosting
chempane as a remote MCP connector (for example behind a reverse proxy for the Claude
Connectors Directory).

It is deliberately separate from the local `chempane` stdio server (`chempane.server`):

- Exposes **only** `generate_molecule` (marked `readOnlyHint: true`) and the embedded
  panel resource `ui://chem-app/index.html`.
- Writes **no files** to disk, exposes no local paths, and disables local-only actions
  (`save_png`, `load_panel_part`, `export_anki_deck`, `lookup_molecule_data`, `generate_3d`).
- Runs stateless HTTP (`stateless_http=True`) with no shared cross-user result cache.

## Local start

```bash
uv run python -m chempane.remote
# Health check: http://127.0.0.1:8792/healthz
# MCP endpoint: http://127.0.0.1:8792/mcp
```

## Container start (provider-agnostic)

Build and run the included `Dockerfile` on any container host (Hetzner VPS, Fly.io,
Railway, Render, Azure Container Apps):

```bash
docker build -t chempane-remote .
docker run --rm -p 8080:8080 \
  -e CHEMPANE_REMOTE_ALLOWED_HOSTS="mcp.example.com,127.0.0.1:8080" \
  -e CHEMPANE_REMOTE_TRUST_PROXY=1 \
  chempane-remote
```

## Configuration (environment variables)

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `CHEMPANE_REMOTE_HOST` | `127.0.0.1` (`0.0.0.0` in Docker) | Bind address |
| `CHEMPANE_REMOTE_PORT` / `PORT` | `8792` (`8080` in Docker) | Listen port |
| `CHEMPANE_REMOTE_ALLOWED_HOSTS` | `127.0.0.1:*,localhost:*,[::1]:*` | Allowed `Host` headers (DNS-rebinding protection) |
| `CHEMPANE_REMOTE_ALLOWED_ORIGINS` | *(empty)* | Optional allowed `Origin` headers |
| `CHEMPANE_REMOTE_RATE_LIMIT` | `30` | Max requests per client IP per window (outside the shared networks) |
| `CHEMPANE_REMOTE_RATE_WINDOW` | `60` | Rate-limit window in seconds |
| `CHEMPANE_REMOTE_SHARED_RANGES` | `160.79.104.0/21` | Networks that many users share (Claude proxies tool calls through Anthropic's published egress range); counted as one client |
| `CHEMPANE_REMOTE_SHARED_RATE_LIMIT` | `600` | Max requests per window for the shared networks together |
| `CHEMPANE_REMOTE_DAILY_LIMIT` | `50000` | Max requests of all clients together per 24 hours; a cost ceiling for hosts without a spending limit (`429 daily_limit_reached`) |
| `CHEMPANE_REMOTE_MAX_CONCURRENT` | `4` | Max concurrent render requests (`503` when full) |
| `CHEMPANE_REMOTE_MAX_BODY_BYTES` | `65536` | Max HTTP request body size (64 KB) |
| `CHEMPANE_REMOTE_TRUST_PROXY` | `0` | Set to `1` only behind a trusted reverse proxy (`X-Forwarded-For`) |
| `CHEMPANE_REMOTE_OPERATOR` / `CHEMPANE_REMOTE_CONTACT` | *(empty)* | Operator name and contact shown on `/privacy`. Set them on the host (for example as secrets), not in the repository; without both the page returns 404 |

Hard input limits: max 500 characters for `name_or_smiles`, max 120 characters for `label`,
and max 200 heavy atoms per structure.

## Data flow (privacy summary)

1. **Client → Remote server (`POST /mcp`):** Receives only the tool arguments
   (`name_or_smiles`, optional display/view flags). The server never reads chat history
   or host files.
2. **Typed SMILES:** Parsed, laid out, analysed for functional groups and rendered to SVG
   entirely in-memory with RDKit inside the container. **No outbound network call** is made.
3. **Compound names:** Resolved first offline via OPSIN (if Java is available in the image);
   otherwise only the compound name string is sent to public chemistry lookup services
   (PubChem, NCI CIR) to obtain a SMILES string.
4. **Storage & logs:** Stateless request handling — no molecule inputs, structures or user
   profiles are written to disk or persisted across requests. Logs go to stderr at `INFO`
   level without logging molecule inputs.

## Verification

```bash
uv run pytest tests/test_remote_server.py
npm --prefix chempane/ui run test:remote
```
