# ChemDraw MCP for Mistral AI Vibe

**Molecule names or SMILES to 2D structures, reactions, mechanisms, spectra - offline via RDKit.**

This is the Mistral AI Vibe version of ChemDraw MCP server. It provides the same powerful chemistry tools as the original Claude Desktop version, but with **mandatory authentication** for secure remote access.

## ✨ Features

- **Molecular Structure Drawing**: Convert molecule names or SMILES to publication-quality 2D structures
- **Reaction Schemes**: Draw reaction schemes with reagents and conditions
- **Mechanism Arrows**: Step-by-step reaction mechanisms with curved electron-flow arrows
- **Spectra**: Schematic spectra (IR, NMR, UV/Vis, MS, etc.) from peak lists
- **3D Models**: Rotatable 3D ball-and-stick conformers
- **Anki Decks**: Create flashcard decks with embedded structures
- **Titration Curves**: pH vs. volume calculations with equivalence points
- **Species Distribution**: Protonation species fractions over pH
- **Molecule Comparison**: Side-by-side comparison with difference highlighting
- **Database Lookups**: PubChem, ChEBI, KEGG, UniProt integration
- **Validation**: Ph.Eur.-style content determination calculations

All features work **fully offline** via RDKit - no internet connection required!

## 🔐 Authentication (Required)

**Authentication is MANDATORY** for Mistral AI Vibe integration. The server will refuse to start without proper authentication configuration.

### Quick Start

1. **Generate a secret key** (32-byte hex):
   ```bash
   openssl rand -hex 32
   ```

2. **Set environment variables**:
   ```bash
   export CHEMDRAW_SECRET_KEY="your-32-byte-hex-key-here"
   export CHEMDRAW_API_KEYS="api-key-1,api-key-2"  # Optional
   ```

3. **Start the server**:
   ```bash
   uv run chemdraw-tool-server
   ```

### Authentication Methods

#### JWT Tokens (Recommended for Users)

```python
# Create a token (via MCP)
create_auth_token(subject="user123", role="user", expires_in=60)

# Returns:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIs...",
#   "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
#   "token_type": "bearer",
#   "expires_in": 60
# }
```

Use the token in requests:
```
Authorization: Bearer <access-token>
```

#### API Keys (Recommended for Services)

```python
# Add an API key (via MCP)
add_api_key(key="my-secret-api-key")

# List API keys
list_api_keys()

# Remove an API key
remove_api_key(key="my-secret-api-key")
```

Use the API key in requests:
```
Authorization: Bearer <api-key>
```

Or via header:
```
X-API-Key: <api-key>
```

### Token Management

- **Access tokens** expire after 30 minutes (configurable via `CHEMDRAW_TOKEN_EXPIRE_MINUTES`)
- **Refresh tokens** expire after 7 days
- Use `refresh_access_token()` to get a new access token from a refresh token

### Authentication Tools

The following tools are available for managing authentication:

| Tool | Description |
|------|-------------|
| `create_auth_token` | Create JWT access and refresh tokens |
| `add_api_key` | Add a new API key |
| `list_api_keys` | List all configured API keys (masked) |
| `remove_api_key` | Remove an API key |
| `get_auth_status` | Get authentication configuration status |

**Note**: Authentication tools do NOT require authentication (to avoid circular dependency).

## 🚀 Installation

### Option 1: Automatic Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/NonoGRT/chemdraw-mcp.git
cd chemdraw-mcp

# Run the Vibe installer
./install_vibe.sh
```

This will:
1. Install uv (Python package manager)
2. Install all dependencies
3. Generate secret key and API key
4. Display configuration instructions

### Option 2: Manual Install

```bash
# Clone the repository
git clone https://github.com/NonoGRT/chemdraw-mcp.git
cd chemdraw-mcp

# Install dependencies
uv sync

# Generate configuration
mkdir -p ~/.chemdraw-mcp
echo "$(openssl rand -hex 32)" > ~/.chemdraw-mcp/secret_key.txt
chmod 600 ~/.chemdraw-mcp/secret_key.txt

# Generate an API key
echo "$(openssl rand -hex 16)" > ~/.chemdraw-mcp/api_keys.txt
chmod 600 ~/.chemdraw-mcp/api_keys.txt
```

### Option 3: Using uvx (One-command)

```bash
uvx --from git+https://github.com/NonoGRT/chemdraw-mcp.git chemdraw-tool-server
```

Note: You'll need to set environment variables separately.

## 📝 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CHEMDRAW_SECRET_KEY` | ✅ Yes | - | JWT signing key (32-byte hex) |
| `CHEMDRAW_API_KEYS` | ❌ No | - | Comma-separated API keys |
| `CHEMDRAW_TOKEN_EXPIRE_MINUTES` | ❌ No | 30 | Token expiration time |
| `CHEMDRAW_OUTPUT_DIR` | ❌ No | `~/ChemDraw-Output` | Output directory |
| `CHEMDRAW_VAULT_PATH` | ❌ No | `~/.chemdraw-mcp` | Local vault path |

### Configuration File

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
# Edit .env with your values
```

Then load it:
```bash
# Using uv
uv run --env-file .env chemdraw-tool-server

# Or manually
set -a && source .env && set +a
uv run chemdraw-tool-server
```

## 🎯 Vibe Configuration

Add the ChemDraw MCP server to your Vibe configuration:

### Option 1: Direct Command

```yaml
# vibe.config.yaml (or similar)
mcpServers:
  chemdraw:
    command: uv
    args: [--directory, /path/to/chemdraw-mcp, run, chemdraw-tool-server]
    env:
      CHEMDRAW_SECRET_KEY: "your-secret-key-here"
      CHEMDRAW_API_KEYS: "api-key-1,api-key-2"
```

### Option 2: Using .env File

```yaml
mcpServers:
  chemdraw:
    command: uv
    args: [--directory, /path/to/chemdraw-mcp, --env-file, .env, run, chemdraw-tool-server]
```

### Option 3: Environment Variables in Shell

If you set the environment variables in your shell, Vibe will inherit them:

```bash
# In your ~/.bashrc or ~/.zshrc
export CHEMDRAW_SECRET_KEY="your-secret-key"
export CHEMDRAW_API_KEYS="api-key-1,api-key-2"

# Then configure Vibe
mcpServers:
  chemdraw:
    command: uv
    args: [--directory, /path/to/chemdraw-mcp, run, chemdraw-tool-server]
```

## 💡 Usage Examples

### First Time Setup

1. **Create a token for yourself**:
   ```
   create_auth_token(subject="my-user-id", role="admin")
   ```

2. **Use the token in your requests**:
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
   ```

3. **Or use an API key**:
   ```
   Authorization: Bearer my-api-key
   ```

### Drawing Molecules

```
# Draw a molecule by name
generate_molecule(name_or_smiles="caffeine")

# Draw a molecule by SMILES
generate_molecule(name_or_smiles="CC(=O)OC1=CC=CC=C1C(=O)O", label="Aspirin")

# With authentication header
Authorization: Bearer <your-token>
```

### Reaction Schemes

```
generate_reaction(
  reactants=["CC(=O)O", "CO"],
  products=["CC(=O)OC"],
  conditions="H2SO4, heat"
)
```

### Batch Processing

```
batch_generate(
  inputs=["aspirin", "caffeine", "ibuprofen"],
  formats=["png", "svg"]
)
```

## 🔧 Troubleshooting

### "Authentication is REQUIRED but not configured"

This error occurs when the server starts without `CHEMDRAW_SECRET_KEY` set.

**Solution**:
```bash
export CHEMDRAW_SECRET_KEY=$(openssl rand -hex 32)
```

### "Invalid or missing authentication credentials"

This error occurs when a tool is called without proper authentication.

**Solution**:
1. Create a token: `create_auth_token(subject="user1")`
2. Include it in your request: `Authorization: Bearer <token>`

### "Token expired"

Tokens expire after 30 minutes by default.

**Solution**:
1. Create a new token: `create_auth_token(subject="user1")`
2. Or use a refresh token to get a new access token

### "Invalid token"

The token signature is invalid.

**Solution**:
1. Ensure you're using the correct secret key
2. Generate a new token with the current secret key

## 📚 API Reference

### Authentication Tools

#### `create_auth_token`

Create JWT tokens for authentication.

**Parameters:**
- `subject` (str, required): User identifier
- `username` (str, optional): Display name
- `role` (str, optional): User role (e.g., "admin", "user")
- `expires_in` (int, optional): Expiration in minutes (default: 30)

**Returns:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 30
}
```

#### `add_api_key`

Add a new API key.

**Parameters:**
- `key` (str, required): The API key to add

**Returns:**
```json
{
  "status": "success",
  "message": "API key added",
  "key": "abcd1234..."
}
```

#### `list_api_keys`

List all configured API keys (masked for security).

**Returns:**
```json
{
  "api_keys": ["abcd1234...", "efgh5678..."],
  "count": 2
}
```

#### `remove_api_key`

Remove an API key.

**Parameters:**
- `key` (str, required): The API key to remove

**Returns:**
```json
{
  "status": "success",
  "message": "API key removed"
}
```

#### `get_auth_status`

Get authentication configuration status.

**Returns:**
```json
{
  "auth_enabled": true,
  "api_keys_count": 2,
  "algorithm": "HS256",
  "token_expiration_minutes": 30
}
```

### Chemistry Tools

All chemistry tools now require authentication. See the original README.md for complete documentation of chemistry tools.

## 🔒 Security Best Practices

1. **Keep your secret key secure**: Never commit it to version control
2. **Use strong keys**: Always use 32-byte hex keys (openssl rand -hex 32)
3. **Rotate keys periodically**: Change your secret key and API keys regularly
4. **Limit API key distribution**: Only share API keys with trusted services
5. **Use HTTPS**: Always use HTTPS in production to protect tokens in transit
6. **Set appropriate permissions**: `chmod 600` on secret and API key files
7. **Audit access**: Monitor who has access to your server

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Mistral AI Vibe                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐  │
│  │   User Request   │───▶│         MCP Client               │  │
│  └─────────────────┘    └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (with Authorization header)
┌─────────────────────────────────────────────────────────────┐
│                 AuthFastMCP Server                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐  │
│  │  Auth Middleware │───▶│         Tool Execution            │  │
│  └─────────────────┘    └─────────────────────────────────┘  │
│       │                          │                          ▲        │
│       ▼                          ▼                          │        │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┴──────┐  │
│  │ JWT/Token       │    │  Chemistry Tools  │    │   Auth Tools     │  │
│  │ Validation      │    │  (generate_*,    │    │   (no auth       │  │
│  └─────────────────┘    │   lookup_*, etc.) │    │   required)      │  │
│                     └─────────────────┘    └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend Services                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐  │
│  │   RDKit         │    │   External APIs (PubChem, etc.)   │  │
│  └─────────────────┘    └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 📄 License

Apache-2.0 - see [LICENSE](LICENSE). Copyright 2026 NonoGRT.

## 🙏 Acknowledgments

- Built on the original [jurimaxam-dotcom/chemdraw-mcp](https://github.com/jurimaxam-dotcom/chemdraw-mcp) project
- Uses [RDKit](https://www.rdkit.org/) for cheminformatics
- Uses [FastMCP](https://github.com/modelcontextprotocol/python-sdk) for MCP server
- Uses [PyJWT](https://pyjwt.readthedocs.io/) for JWT token management

---

**Note**: This is an unofficial, independent project, not affiliated with or endorsed by Revvity. *ChemDraw* is a trademark of Revvity Signals Software, Inc. This tool does not include or require ChemDraw; it can optionally export files in the open CDXML format.
