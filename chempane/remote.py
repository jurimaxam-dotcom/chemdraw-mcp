"""Separat startbarer Remote-MCP-Konnektor über Streamable HTTP (Pilot).

Anwendungsfall: Name oder SMILES → interaktive 2D-Struktur mit funktionellen Gruppen
im MCP-App-Panel. Bewusst getrennt vom lokalen stdio-Server (`chempane.server`):
- schreibt keine Dateien und liest keine lokalen Pfade
- kein Anki, kein save_png, kein geteilter serverseitiger Panel-Cache
- zustandsloses Streamable HTTP (`stateless_http=True`)
- Eingabe-, Größen-, Nebenläufigkeits- und Rate-Limits für den öffentlichen Betrieb

Start lokal:
    uv run python -m chempane.remote
"""

from __future__ import annotations

import asyncio
import html
import ipaddress
import logging
import os
import time
from collections import deque
from dataclasses import dataclass, field
from importlib.metadata import version as _pkg_version

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Route

from chempane.generator import generate_2d
from chempane.payloads import FunctionalGroup, MoleculePayload
from chempane.render_style import condense_groups, get_style
from chempane.resolver import NameResolutionError, resolve
from chempane.server import (
    _RESOURCE_URI,
    _UI_META,
    _UNKNOWN_VIEW,
    _VIEWS,
    _ambiguous_payload,
    _found_as,
    _projection_note,
    _projection_views,
    _shown_name,
    _stereo_fields,
    _stereo_variants_payload,
    _user_facing_errors,
    _view_drawing,
    chem_app_ui,
)
from chempane.settings import PACKAGE, env
from chempane.svg_renderer import (
    extract_atom_data,
    extract_functional_groups,
    render_svg,
)
from chempane.validator import Severity, validate_input

MAX_INPUT_LENGTH = 500
MAX_LABEL_LENGTH = 120
MAX_HEAVY_ATOMS = 200
_MAX_TRACKED_CLIENTS = 10_000
# Claude leitet MCP-Tool-Aufrufe über das eigene Backend; laut Anthropic-Doku (Connector-Authentifizierung,
# „outbound traffic … originates from") kommen sie aus diesem Bereich. Ein Limit je IP wäre dort ein
# gemeinsamer Deckel für alle Nutzer, deshalb zählt der Bereich als ein Schlüssel mit eigenem Limit.
_ANTHROPIC_EGRESS = ("160.79.104.0/21",)
_SHARED_KEY = "shared-egress"

_REMOTE_INSTRUCTIONS = """\
chempane remote chemistry connector (2D structure drawing pilot).
Use generate_molecule whenever the user names a chemical compound, formula or SMILES \
to show an interactive 2D skeletal structure with highlighted functional groups.
Pass English or IUPAC names or SMILES; put localized names in `label`."""


class RemoteMoleculePayload(MoleculePayload):
    """MoleculePayload mit Remote-Flag für das Panel (keine lokalen Aktionen)."""

    remote: bool = True


@dataclass(frozen=True)
class RemoteConfig:
    host: str = "127.0.0.1"
    port: int = 8792
    allowed_hosts: tuple[str, ...] = ("127.0.0.1:*", "localhost:*", "[::1]:*", "testserver")
    allowed_origins: tuple[str, ...] = ()
    rate_limit_requests: int = 30
    rate_limit_window_seconds: float = 60.0
    shared_ranges: tuple[str, ...] = _ANTHROPIC_EGRESS
    shared_rate_limit_requests: int = 600
    # Obergrenze für alle Anfragen eines Tages zusammen: der Host kennt kein Ausgabenlimit.
    daily_limit_requests: int = 50_000
    max_concurrent: int = 4
    max_request_body_bytes: int = 65_536
    trust_proxy: bool = False
    path: str = "/mcp"
    # Betreiber und Kontakt der Datenschutzseite: nur aus der Umgebung des Hosts, nie im Repo.
    operator: str = ""
    contact: str = ""

    @classmethod
    def from_env(cls) -> RemoteConfig:
        host = env("REMOTE_HOST", "127.0.0.1").strip() or "127.0.0.1"
        port = int(env("REMOTE_PORT") or os.environ.get("PORT") or "8792")
        raw_hosts = env("REMOTE_ALLOWED_HOSTS").strip()
        if raw_hosts:
            allowed_hosts = tuple(h.strip() for h in raw_hosts.split(",") if h.strip())
        else:
            allowed_hosts = ("127.0.0.1:*", "localhost:*", "[::1]:*")
        raw_origins = env("REMOTE_ALLOWED_ORIGINS").strip()
        allowed_origins = tuple(o.strip() for o in raw_origins.split(",") if o.strip())
        raw_shared = env("REMOTE_SHARED_RANGES").strip()
        shared_ranges = (
            tuple(r.strip() for r in raw_shared.split(",") if r.strip()) if raw_shared else _ANTHROPIC_EGRESS
        )
        return cls(
            host=host,
            port=port,
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins,
            rate_limit_requests=max(1, int(env("REMOTE_RATE_LIMIT", "30"))),
            rate_limit_window_seconds=max(1.0, float(env("REMOTE_RATE_WINDOW", "60"))),
            shared_ranges=shared_ranges,
            shared_rate_limit_requests=max(1, int(env("REMOTE_SHARED_RATE_LIMIT", "600"))),
            daily_limit_requests=max(1, int(env("REMOTE_DAILY_LIMIT", "50000"))),
            max_concurrent=max(1, int(env("REMOTE_MAX_CONCURRENT", "4"))),
            max_request_body_bytes=max(4096, int(env("REMOTE_MAX_BODY_BYTES", "65536"))),
            trust_proxy=env("REMOTE_TRUST_PROXY").strip().lower() in {"1", "true", "yes"},
            operator=env("REMOTE_OPERATOR").strip(),
            contact=env("REMOTE_CONTACT").strip(),
        )


def _validate_text_input(name_or_smiles: str, label: str) -> tuple[str, str]:
    cleaned = (name_or_smiles or "").strip()
    if not cleaned:
        raise ValueError("Please provide a compound name or SMILES string.")
    if len(cleaned) > MAX_INPUT_LENGTH:
        raise ValueError(f"Input is too long ({len(cleaned)} chars; maximum is {MAX_INPUT_LENGTH}).")
    if any(ord(ch) < 32 for ch in cleaned):
        raise ValueError("Input contains invalid control characters.")
    clean_label = (label or "").strip()
    if len(clean_label) > MAX_LABEL_LENGTH:
        raise ValueError(f"Label is too long ({len(clean_label)} chars; maximum is {MAX_LABEL_LENGTH}).")
    return cleaned, clean_label


def _local_rdkit_properties(mol, smiles: str) -> dict[str, str]:
    from rdkit.Chem import Descriptors, rdMolDescriptors

    return {
        "formula": rdMolDescriptors.CalcMolFormula(mol),
        "mw": f"{Descriptors.MolWt(mol):.2f} g/mol",
        "smiles": smiles,
    }


def remote_generate_molecule(
    name_or_smiles: str,
    label: str = "",
    annotate_stereo: bool = False,
    abbreviate_groups: bool = False,
    render_style: str = "",
    stereo_variants: bool = False,
    view: str = "",
) -> RemoteMoleculePayload:
    """Draw one compound as an interactive 2D chemical structure with functional groups.

    Renders a 2D skeletal formula (or requested projection) on the server with RDKit
    and returns an interactive panel showing the drawing, formula, molar mass and
    highlighted functional groups. Read-only: writes no files.

    Input is an English or IUPAC compound name or a SMILES string; a name in another
    language belongs in `label`.

    Args:
        name_or_smiles: English/IUPAC compound name or SMILES string (max 500 chars).
        label: Optional display name below the structure (may be localized).
        annotate_stereo: True prints CIP stereodescriptors (R/S, E/Z).
        abbreviate_groups: True contracts common substituents (Ph, OAc, Boc).
        render_style: "", "compact", "presentation" or "grayscale".
        stereo_variants: True lists stereoisomers (max 3 open centers) as a pick list.
        view: Optional view ("all_h", "fischer", "haworth", "chair").
    """
    cleaned, clean_label = _validate_text_input(name_or_smiles, label)
    get_style(render_style)

    try:
        resolved = resolve(cleaned)
    except NameResolutionError as exc:
        if exc.kind == "protein":
            raise ValueError(
                f"'{cleaned}' is a protein or antibody. This remote pilot draws small-molecule "
                "2D structures only (up to 200 heavy atoms)."
            ) from exc
        if exc.kind != "ambiguous":
            raise
        ambig = _ambiguous_payload(cleaned, exc.candidates)
        return RemoteMoleculePayload(**ambig.model_dump(), remote=True)

    smiles, mol = resolved
    heavy = mol.GetNumHeavyAtoms()
    if heavy > MAX_HEAVY_ATOMS:
        raise ValueError(
            f"Structure has {heavy} heavy atoms; this remote pilot is limited to {MAX_HEAVY_ATOMS} heavy atoms."
        )

    found_as = _found_as(resolved)
    if stereo_variants:
        variants = _stereo_variants_payload(cleaned, clean_label, smiles, mol)
        return RemoteMoleculePayload(**variants.model_dump(), remote=True)
    if view and view not in _VIEWS:
        raise ValueError(_UNKNOWN_VIEW.format(view=view))

    mol = generate_2d(mol)
    for issue in validate_input(mol):
        if issue.severity == Severity.ERROR:
            raise ValueError(f"Input validation failed: {issue.message}")

    display_name = clean_label or _shown_name(cleaned)
    drawn = condense_groups(mol) if abbreviate_groups else mol

    view_svg, view_atoms = "", []
    if view:
        if view == "all_h" and abbreviate_groups:
            raise ValueError("All H is not available for abbreviated drawings.")
        view_svg, view_atoms = _view_drawing(view, cleaned, mol, annotate_stereo, render_style)

    properties = _local_rdkit_properties(mol, smiles)
    groups = [FunctionalGroup(**g) for g in extract_functional_groups(mol)]
    atoms = [] if abbreviate_groups else extract_atom_data(mol)
    views = [] if abbreviate_groups else ["all_h"]
    views += _projection_views(mol)
    view_request: dict[str, object] = {"name_or_smiles": smiles}
    if annotate_stereo:
        view_request["annotate_stereo"] = True
    if render_style:
        view_request["render_style"] = render_style

    return RemoteMoleculePayload(
        type="molecule",
        remote=True,
        svg=render_svg(
            drawn,
            fill_container=True,
            annotate_stereo=annotate_stereo,
            style=render_style,
        ),
        atoms=atoms,
        views=views,
        viewRequest=view_request,
        projectionNote=_projection_note(mol),
        name=display_name,
        properties=properties,
        functionalGroups=groups,
        **_stereo_fields(mol, atoms),
        foundAs=found_as,
        lipinski=None,
        files={},
        cdxml_path="",
        initialView=view,
        viewSvg=view_svg,
        viewAtoms=view_atoms,
    )


def create_remote_server() -> MCPServer:
    """Build the minimal, read-only remote MCP server (1 tool + UI resource)."""
    instance = MCPServer(
        "chempane",
        instructions=_REMOTE_INSTRUCTIONS,
        version=_pkg_version(PACKAGE),
    )
    tool_fn = _user_facing_errors(remote_generate_molecule)
    instance.tool(
        name="generate_molecule",
        title="Draw a structure",
        structured_output=True,
        meta=_UI_META,
        annotations=ToolAnnotations(
            title="Draw a structure",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )(tool_fn)
    instance.resource(
        _RESOURCE_URI,
        mime_type="text/html;profile=mcp-app",
        meta={"ui": {"permissions": {"clipboardWrite": {}}}},
    )(chem_app_ui)
    return instance


@dataclass
class _SlidingWindowLimiter:
    limit: int
    window_seconds: float
    _hits: dict[str, deque[float]] = field(default_factory=dict)

    def allow(self, key: str, now: float | None = None) -> tuple[bool, int]:
        ts = time.monotonic() if now is None else now
        cutoff = ts - self.window_seconds
        bucket = self._hits.get(key)
        if bucket is None:
            if len(self._hits) >= _MAX_TRACKED_CLIENTS:
                self._evict_stale(cutoff)
            bucket = deque()
            self._hits[key] = bucket
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= self.limit:
            retry = max(1, int(self.window_seconds - (ts - bucket[0])) + 1)
            return False, retry
        bucket.append(ts)
        return True, 0

    def _evict_stale(self, cutoff: float) -> None:
        stale = [k for k, q in self._hits.items() if not q or q[-1] <= cutoff]
        for k in stale:
            self._hits.pop(k, None)
        if len(self._hits) >= _MAX_TRACKED_CLIENTS:
            self._hits.clear()


def _client_ip(request: Request, trust_proxy: bool) -> str:
    if trust_proxy:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"


_PRIVACY_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Privacy policy: hosted chempane connector</title>
<style>body{{font:16px/1.55 system-ui,sans-serif;max-width:44rem;margin:3rem auto;padding:0 1.2rem;color:#1c1c1c}}
h1{{font-size:1.5rem}}h2{{font-size:1.1rem;margin-top:1.8rem}}code{{background:#f1f1f1;padding:.1em .3em;border-radius:3px}}</style>
</head><body>
<h1>Privacy policy for the hosted chempane connector</h1>
<p>Applies to the hosted MCP server at <code>https://{host}/mcp</code>, the connector you add in Claude.
The local chempane server that runs on your own computer is covered by its own
<a href="https://github.com/chempane/chempane/blob/main/docs/privacy.md">privacy page</a>.</p>
<h2>Who runs it</h2>
<p>The hosted connector is run by {operator}, contact {contact}. chempane is an unofficial open-source
project (Apache-2.0) and is not affiliated with Revvity (ChemDraw) or Anthropic.</p>
<h2>What the server receives</h2>
<p>Only the arguments of a tool call: the compound name or structure string you asked Claude to draw, an
optional label and display options. It does not receive your conversation, your files or your account
details. Claude sends tool calls through Anthropic's infrastructure, so the server sees Anthropic's
network address, not yours.</p>
<h2>What leaves the server</h2>
<p>A structure you type (SMILES, InChI) is parsed, laid out and drawn in memory on the server. It is
sent to no other service.</p>
<p>A compound name is resolved to a structure. If the name cannot be read offline, the name itself is
sent to PubChem (U.S. National Institutes of Health) and the NCI Chemical Identifier Resolver.</p>
<h2>What is stored</h2>
<p>Nothing about what you draw. The server has no database, no user accounts and no result cache that
outlives a request. Its log records start-up, errors and one line per request (time, path, status code);
it does not record compound names or structures. The server runs on Fly.io in Frankfurt, Germany;
Fly.io keeps platform logs for a limited time under its own
<a href="https://fly.io/legal/privacy-policy/">privacy policy</a>.</p>
<h2>No sign-in, no tracking</h2>
<p>The connector needs no account, sets no cookies and contains no analytics. A rate limit counts
requests per network address in memory for one minute and is discarded afterwards.</p>
<h2>Legal basis</h2>
<p>Handling a tool call to return the requested structure is based on Art. 6(1)(b) GDPR (providing the
service you requested). Technical request logs and in-memory rate limiting are based on Art. 6(1)(f) GDPR
(legitimate interest in keeping the server reliable and preventing abuse).</p>
<h2>Your rights</h2>
<p>Under the GDPR you have the right to access (Art. 15), rectify (Art. 16) or erase (Art. 17) your
personal data, to restrict its processing (Art. 18), to receive it in a portable format (Art. 20) and
to object to processing based on legitimate interests (Art. 21). Because this server stores no user
accounts or drawing history, it normally holds no personal data linked to you; to exercise any of these
rights, contact {contact}.</p>
<p>You also have the right to lodge a complaint with a data protection supervisory authority (Art. 77 GDPR),
for example in the EU/EEA member state of your habitual residence, your place of work or the place of the
alleged infringement.</p>
<h2>Changes and contact</h2>
<p>This page changes when the data flow changes. Questions and requests: {contact}.</p>
<p>Version {version}.</p>
</body></html>
"""


def _in_ranges(ip: str, networks: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...]) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(addr.version == net.version and addr in net for net in networks)


def create_remote_app(config: RemoteConfig | None = None) -> Starlette:
    """Create the ASGI app serving stateless Streamable HTTP on `/mcp` plus `/healthz`."""
    cfg = config or RemoteConfig.from_env()
    server = create_remote_server()
    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=list(cfg.allowed_hosts),
        allowed_origins=list(cfg.allowed_origins),
    )
    app = server.streamable_http_app(
        streamable_http_path=cfg.path,
        json_response=True,
        stateless_http=True,
        max_request_body_size=cfg.max_request_body_bytes,
        transport_security=security,
        host=cfg.host,
    )

    async def healthz(_request: Request) -> Response:
        return JSONResponse(
            {
                "status": "ok",
                "service": "chempane-remote",
                "version": _pkg_version(PACKAGE),
            }
        )

    app.routes.insert(0, Route("/healthz", endpoint=healthz, methods=["GET"]))

    async def privacy(request: Request) -> Response:
        # Ohne Betreiberangabe keine Seite: eine Erklärung ohne Verantwortlichen wäre falsch.
        if not (cfg.operator and cfg.contact):
            return JSONResponse({"error": "not_configured"}, status_code=404)
        return HTMLResponse(
            _PRIVACY_PAGE.format(
                host=html.escape(request.url.hostname or ""),
                operator=html.escape(cfg.operator),
                contact=html.escape(cfg.contact),
                version=html.escape(_pkg_version(PACKAGE)),
            )
        )

    app.routes.insert(0, Route("/privacy", endpoint=privacy, methods=["GET"]))

    limiter = _SlidingWindowLimiter(cfg.rate_limit_requests, cfg.rate_limit_window_seconds)
    shared_limiter = _SlidingWindowLimiter(cfg.shared_rate_limit_requests, cfg.rate_limit_window_seconds)
    shared_networks = tuple(ipaddress.ip_network(r, strict=False) for r in cfg.shared_ranges)
    daily_limiter = _SlidingWindowLimiter(cfg.daily_limit_requests, 86_400.0)
    semaphore = asyncio.Semaphore(cfg.max_concurrent)

    async def pilot_guards(request: Request, call_next):
        if request.url.path in {"/healthz", "/privacy"}:
            return await call_next(request)
        ip = _client_ip(request, cfg.trust_proxy)
        if _in_ranges(ip, shared_networks):
            allowed, retry_after = shared_limiter.allow(_SHARED_KEY)
        else:
            allowed, retry_after = limiter.allow(ip)
        if not allowed:
            return JSONResponse(
                {"error": "rate_limit_exceeded", "retry_after_seconds": retry_after},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )
        allowed, retry_after = daily_limiter.allow("all")
        if not allowed:
            return JSONResponse(
                {"error": "daily_limit_reached", "retry_after_seconds": retry_after},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )
        if semaphore.locked():
            return JSONResponse(
                {"error": "server_busy", "message": "Too many concurrent requests; retry shortly."},
                status_code=503,
                headers={"Retry-After": "2"},
            )
        async with semaphore:
            return await call_next(request)

    app.add_middleware(BaseHTTPMiddleware, dispatch=pilot_guards)
    return app


def main() -> None:
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    cfg = RemoteConfig.from_env()
    logging.getLogger(__name__).info(
        "Starting chempane remote MCP server on %s:%s%s (rate=%s/%ss, max_concurrent=%s)",
        cfg.host,
        cfg.port,
        cfg.path,
        cfg.rate_limit_requests,
        int(cfg.rate_limit_window_seconds),
        cfg.max_concurrent,
    )
    app = create_remote_app(cfg)
    uvicorn.run(app, host=cfg.host, port=cfg.port, log_level="info")


if __name__ == "__main__":
    main()
