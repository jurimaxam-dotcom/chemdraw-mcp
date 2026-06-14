# Plan de Migration : ChemDraw MCP de Claude Code vers Mistral AI (Vibe)

## 📋 Contexte

Ce document décrit les modifications nécessaires pour migrer le projet **chemdraw-mcp** de **Claude Code** vers **Mistral AI (Vibe)** avec authentification.

Le projet actuel est conçu pour fonctionner comme un serveur MCP (Model Context Protocol) pour **Claude Desktop**. L'objectif est de l'adapter pour qu'il fonctionne avec **Mistral AI Vibe** tout en ajoutant une couche d'authentification.

---

## 🔍 Analyse de l'Architecture Actuelle

### Structure du Projet
```
chemdraw-mcp/
├── chemdraw_tool/
│   ├── server.py          # Serveur FastMCP (point d'entrée principal)
│   ├── resolver.py        # Résolution SMILES/noms → structures
│   ├── generator.py       # Génération 2D via RDKit
│   ├── image_export.py    # Export PNG/SVG
│   ├── svg_renderer.py    # Rendu SVG pour l'UI
│   ├── ui/                # Interface React/Vite (MCP App)
│   └── ...
├── scripts/
│   └── install_claude_config.py  # Installation pour Claude Desktop
├── install.sh             # Script d'installation (Claude)
├── server.json            # Manifest MCP (référence PyPI)
├── CLAUDE.md              # Documentation spécifique à Claude
└── README.md              # Documentation principale
```

### Points Clés
- **Protocole** : MCP (Model Context Protocol) via FastMCP
- **Langage** : Python 3.11+ avec dépendances gérées par `uv`
- **UI** : Application React/Vite intégrée comme ressource MCP
- **Installation** : Configuration dans `claude_desktop_config.json`
- **Authentification** : Aucune (tout est local)
- **Stockage** : Fichiers générés dans `~/ChemDraw-Output/`

---

## 🎯 Objectifs de la Migration

1. **Compatibilité Vibe** : Rendre le serveur compatible avec Mistral AI Vibe
2. **Authentification** : Ajouter un système d'authentification pour l'accès distant
3. **Configuration** : Adapter les scripts d'installation pour Vibe
4. **Documentation** : Mettre à jour toute la documentation
5. **Sécurité** : Implémenter les bonnes pratiques de sécurité

---

## 📝 Modifications Nécessaires

### 1. 🔧 Configuration du Serveur MCP

#### Fichiers à modifier
- **`server.json`** : Mettre à jour les métadonnées du serveur
  - Changer le `name` et `repository.url` pour pointer vers le nouveau dépôt
  - Mettre à jour la `description` pour mentionner Vibe
  - Ajouter des informations sur l'authentification

#### Actions
```json
{
  "name": "io.github.NonoGRT/chemdraw-mcp",
  "title": "ChemDraw MCP for Mistral AI Vibe",
  "description": "Molecule names or SMILES to 2D structures, reactions, mechanisms, spectra - offline via RDKit. For Mistral AI Vibe.",
  "version": "0.3.0",
  "repository": {
    "url": "https://github.com/NonoGRT/chemdraw-mcp",
    "source": "github"
  }
}
```

---

### 2. 🔐 Système d'Authentification

#### Nouvelle Structure
```
chemdraw_tool/
└── auth/                  # Nouveau dossier
    ├── __init__.py
    ├── config.py          # Configuration des clés API
    ├── middleware.py      # Middleware d'authentification
    └── tokens.py          # Gestion des tokens JWT
```

#### Fichiers à créer

##### `chemdraw_tool/auth/config.py`
```python
"""Configuration de l'authentification pour Mistral AI Vibe."""

import os
from pathlib import Path

# Clé secrète pour signer les tokens JWT (à générer via openssl rand -hex 32)
SECRET_KEY = os.environ.get("CHEMDRAW_SECRET_KEY", "")

# Algorithme de signature
ALGORITHM = "HS256"

# Durée de validité des tokens (en minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Fichier de stockage des utilisateurs autorisés
USERS_DB_PATH = Path.home() / ".chemdraw-mcp" / "users.json"

# URL de callback pour l'authentification OAuth2 (si applicable)
OAUTH_CALLBACK_URL = os.environ.get("CHEMDRAW_OAUTH_CALLBACK", "http://localhost:8000/auth/callback")

def validate_config():
    """Valide que la configuration est complète."""
    if not SECRET_KEY:
        raise ValueError(
            "CHEMDRAW_SECRET_KEY environment variable is required. "
            "Generate with: openssl rand -hex 32"
        )
```

##### `chemdraw_tool/auth/tokens.py`
```python
"""Gestion des tokens JWT pour l'authentification."""

from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import HTTPException, status

from chemdraw_tool.auth.config import ALGORITHM, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crée un token JWT d'accès."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Vérifie un token JWT et retourne ses données."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

##### `chemdraw_tool/auth/middleware.py`
```python
"""Middleware d'authentification pour FastMCP."""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from chemdraw_tool.auth.tokens import verify_token

security = HTTPBearer()


async def verify_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Vérifie la clé API dans l'en-tête Authorization."""
    # Pour une authentification simple par clé API
    api_key = credentials.credentials
    
    # À implémenter: vérification contre une base de données
    # ou une variable d'environnement
    valid_keys = os.environ.get("CHEMDRAW_API_KEYS", "").split(",")
    
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key


async def verify_jwt_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Vérifie le token JWT dans l'en-tête Authorization."""
    token = credentials.credentials
    payload = verify_token(token)
    return payload
```

#### Modifications dans `server.py`
Ajouter l'authentification au serveur FastMCP :

```python
from mcp.server.fastmcp import FastMCP
from fastapi import Depends, HTTPException
from chemdraw_tool.auth.middleware import verify_api_key, verify_jwt_token

# Créer le serveur avec authentification
mcp = FastMCP("ChemDraw Tool", dependencies=[Depends(verify_jwt_token)])

# Ou pour une authentification optionnelle :
# mcp = FastMCP("ChemDraw Tool")
# Puis ajouter @mcp.tool(dependencies=[Depends(verify_jwt_token)]) sur les outils protégés
```

---

### 3. 📦 Scripts d'Installation

#### Nouveau script : `install_vibe.sh`
```bash
#!/usr/bin/env bash
# Script d'installation pour Mistral AI Vibe
# 
#   1. Installe uv si nécessaire
#   2. Installe les dépendances Python
#   3. Configure le serveur pour Vibe
#   4. Génère une clé secrète si nécessaire

set -euo pipefail

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

echo "== ChemDraw-Tool Installer for Mistral AI Vibe =="
echo "Project: $PROJECT_DIR"
echo ""

# --- 1. uv ---
if ! command -v uv >/dev/null 2>&1; then
  echo "→ Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi
echo "✓ uv: $(command -v uv)"

# --- 2. Dependencies ---
echo ""
echo "→ Installing dependencies..."
uv sync --quiet
echo "✓ Dependencies ready."

# --- 3. Generate secret key if not exists ---
echo ""
echo "→ Checking authentication configuration..."
SECRET_KEY_FILE="$HOME/.chemdraw-mcp/secret_key.txt"
mkdir -p "$HOME/.chemdraw-mcp"

if [ ! -f "$SECRET_KEY_FILE" ]; then
  echo "→ Generating new secret key..."
  openssl rand -hex 32 > "$SECRET_KEY_FILE"
  chmod 600 "$SECRET_KEY_FILE"
  echo "✓ Secret key generated at $SECRET_KEY_FILE"
  echo "  Add to your environment: export CHEMDRAW_SECRET_KEY=$(cat $SECRET_KEY_FILE)"
else
  echo "✓ Secret key already exists at $SECRET_KEY_FILE"
fi

# --- 4. Configuration ---
echo ""
echo "→ Vibe configuration..."
echo "  To use with Vibe, add the following to your Vibe configuration:"
echo ""
echo "  mcpServers:"
echo "    chemdraw:"
echo "      command: uv"
echo "      args: [--directory, $PROJECT_DIR, run, chemdraw-tool-server]"
echo "      env:"
echo "        CHEMDRAW_SECRET_KEY: \"$(cat $SECRET_KEY_FILE)\""
echo ""

echo "✅ Installation complete!"
echo "  Restart Vibe and ask: 'draw caffeine'"
```

#### Mise à jour de `install.sh`
- Renommer en `install_claude.sh` ou ajouter une détection automatique
- Ajouter un message indiquant que pour Vibe, utiliser `install_vibe.sh`

---

### 4. 📚 Documentation

#### Fichiers à créer/mettre à jour

##### Nouveau fichier : `VIBE.md`
```markdown
# ChemDraw MCP for Mistral AI Vibe

MCP server for Mistral AI Vibe that turns molecule names or SMILES into
publication-style 2D structure drawings.

## Installation

### Quick Install

```bash
./install_vibe.sh
```

This will:
1. Install uv (Python package manager)
2. Install dependencies
3. Generate a secret key for authentication
4. Display configuration for Vibe

### Manual Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Generate a secret key:
   ```bash
   mkdir -p ~/.chemdraw-mcp
   openssl rand -hex 32 > ~/.chemdraw-mcp/secret_key.txt
   chmod 600 ~/.chemdraw-mcp/secret_key.txt
   ```

3. Configure Vibe:
   Add to your Vibe configuration:
   ```yaml
   mcpServers:
     chemdraw:
       command: uv
       args: [--directory, /path/to/chemdraw-mcp, run, chemdraw-tool-server]
       env:
         CHEMDRAW_SECRET_KEY: "your-secret-key-here"
   ```

4. Restart Vibe

## Authentication

### API Key Authentication

Set the `CHEMDRAW_API_KEYS` environment variable with comma-separated API keys:

```bash
export CHEMDRAW_API_KEYS="key1,key2,key3"
```

Then include in your request:
```
Authorization: Bearer your-api-key
```

### JWT Token Authentication

For more advanced use cases, you can use JWT tokens.

1. Generate a token (example):
   ```python
   from chemdraw_tool.auth.tokens import create_access_token
   token = create_access_token({"sub": "user123"})
   ```

2. Include in requests:
   ```
   Authorization: Bearer your-jwt-token
   ```

## Usage

Ask Vibe: "draw caffeine" or "show the structure of aspirin"

All features from the original Claude version are supported:
- Molecular structures (PNG/SVG)
- Reaction schemes
- Mechanisms
- Spectra
- 3D models
- Anki decks
- etc.
```

##### Mise à jour de `README.md`
- Ajouter une section pour Vibe
- Mentionner les deux options (Claude et Vibe)
- Documenter l'authentification
- Mettre à jour les badges (CI, etc.)

##### Mise à jour de `CLAUDE.md`
- Renommer en `INSTALLATION.md` ou `CLIENT_CONFIG.md`
- Ajouter des instructions pour Vibe
- Garder les instructions pour Claude

---

### 5. ⚙️ Configuration Environnement

#### Variables d'Environnement

| Variable | Description | Requise | Défaut |
|----------|-------------|---------|--------|
| `CHEMDRAW_SECRET_KEY` | Clé secrète pour signer les JWT | Oui | - |
| `CHEMDRAW_API_KEYS` | Liste de clés API autorisées (séparées par des virgules) | Non | - |
| `CHEMDRAW_VAULT_PATH` | Chemin vers la base de connaissances locale | Non | - |
| `CHEMDRAW_OUTPUT_DIR` | Dossier de sortie pour les fichiers générés | Non | `~/ChemDraw-Output` |

---

### 6. 🔒 Sécurité

#### Bonnes Pratiques

1. **Clé Secrète** : Toujours générer une nouvelle clé secrète pour chaque déploiement
   ```bash
   openssl rand -hex 32
   ```

2. **Permissions** : Limiter les permissions sur les fichiers sensibles
   ```bash
   chmod 600 ~/.chemdraw-mcp/secret_key.txt
   chmod 600 ~/.chemdraw-mcp/users.json
   ```

3. **HTTPS** : Toujours utiliser HTTPS en production pour protéger les tokens

4. **Rotation des Clés** : Mettre en place un système de rotation des clés API

5. **Audit** : Logger les accès pour audit

#### Fichier `.env.example`
```bash
# Authentication
CHEMDRAW_SECRET_KEY=your-secret-key-here
CHEMDRAW_API_KEYS=key1,key2,key3

# Storage
CHEMDRAW_OUTPUT_DIR=/path/to/output
CHEMDRAW_VAULT_PATH=/path/to/vault

# Server
CHEMDRAW_HOST=0.0.0.0
CHEMDRAW_PORT=8000
```

---

### 7. 🧪 Tests

#### Nouveaux Tests

Créer `tests/test_auth.py` :

```python
"""Tests pour l'authentification."""

import pytest
from fastapi.testclient import TestClient
from chemdraw_tool.server import mcp
from chemdraw_tool.auth.tokens import create_access_token, verify_token
from chemdraw_tool.auth.config import SECRET_KEY


@pytest.fixture
def client():
    return TestClient(mcp.app)


def test_create_and_verify_token():
    """Test la création et vérification des tokens JWT."""
    data = {"sub": "testuser", "role": "user"}
    token = create_access_token(data)
    
    payload = verify_token(token)
    assert payload["sub"] == "testuser"
    assert payload["role"] == "user"
    assert "exp" in payload


def test_invalid_token():
    """Test qu'un token invalide est rejeté."""
    with pytest.raises(HTTPException) as exc_info:
        verify_token("invalid.token.here")
    
    assert exc_info.value.status_code == 401


def test_protected_endpoint_without_auth(client):
    """Test qu'un endpoint protégé nécessite une authentification."""
    response = client.post("/tools/generate_molecule", json={
        "name_or_smiles": "caffeine"
    })
    assert response.status_code == 401


def test_protected_endpoint_with_auth(client):
    """Test qu'un endpoint protégé accepte un token valide."""
    token = create_access_token({"sub": "testuser"})
    
    response = client.post(
        "/tools/generate_molecule",
        json={"name_or_smiles": "caffeine"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

---

### 8. 📊 Architecture Cible

```
┌─────────────────────────────────────────────────────────────┐
│                     Mistral AI Vibe                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐  │
│  │   User Request   │───▶│         MCP Client               │  │
│  └─────────────────┘    └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   ChemDraw MCP Server                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐  │
│  │  Auth Middleware │───▶│         FastMCP Server            │  │
│  └─────────────────┘    └─────────────────────────────────┘  │
│       ▲                          │                          ▲        │
│       │                          ▼                          │        │
│  ┌────┴─────────┐    ┌─────────────────┐    ┌─────────────┴──────┐  │
│  │ JWT/Token    │    │  Tool Handlers   │    │   MCP App UI      │  │
│  │ Validation   │    │  (generate_*,    │    │   (React/Vite)    │  │
│  └──────────────┘    │   lookup_*, etc.) │    └──────────────────┘  │
│                     └─────────────────┘                        │
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

---

## 📅 Roadmap de Migration

### Phase 1 : Préparation (1-2 jours)
- [ ] Créer la branche `vibe/migration-mistral-ai`
- [ ] Créer ce document de planification
- [ ] Revoir et valider le plan avec l'équipe

### Phase 2 : Implémentation de l'Authentification (2-3 jours)
- [ ] Créer le module `chemdraw_tool/auth/`
- [ ] Implémenter la configuration d'authentification
- [ ] Implémenter la gestion des tokens JWT
- [ ] Implémenter le middleware d'authentification
- [ ] Intégrer l'authentification dans le serveur FastMCP
- [ ] Écrire les tests unitaires pour l'authentification

### Phase 3 : Adaptation des Scripts (1 jour)
- [ ] Créer `install_vibe.sh`
- [ ] Mettre à jour `install.sh` pour mentionner Vibe
- [ ] Tester les scripts d'installation

### Phase 4 : Mise à jour de la Documentation (1-2 jours)
- [ ] Créer `VIBE.md`
- [ ] Mettre à jour `README.md`
- [ ] Mettre à jour `CLAUDE.md` → `INSTALLATION.md`
- [ ] Mettre à jour `server.json`
- [ ] Mettre à jour les commentaires dans le code

### Phase 5 : Tests et Validation (2-3 jours)
- [ ] Tester l'installation avec Vibe
- [ ] Tester l'authentification
- [ ] Tester toutes les fonctionnalités existantes
- [ ] Corriger les bugs
- [ ] Optimiser les performances

### Phase 6 : Déploiement (1 jour)
- [ ] Créer une release candidate
- [ ] Documenter les étapes de migration pour les utilisateurs
- [ ] Mettre à jour le dépôt GitHub
- [ ] Annoncer la disponibilité

---

## 🔄 Changements de Comportement

### Pour les Utilisateurs

| Aspect | Avant (Claude) | Après (Vibe) |
|--------|---------------|--------------|
| Installation | `install.sh` | `install_vibe.sh` |
| Configuration | `claude_desktop_config.json` | Configuration Vibe |
| Authentification | Aucune | Clé API ou JWT requise |
| Accès | Local uniquement | Local ou distant |
| Stockage | `~/ChemDraw-Output/` | Configurable |

### Pour les Développeurs

| Aspect | Avant | Après |
|--------|-------|-------|
| Dépendances | Aucune | `pyjwt`, `python-dotenv` |
| Configuration | Hardcodée | Via variables d'environnement |
| Tests | Tests existants | Tests existants + tests auth |

---

## ⚠️ Risques et Atténuation

### Risques

1. **Compatibilité MCP** : Vibe pourrait avoir des différences dans l'implémentation MCP
   - *Atténuation* : Tester tôt avec Vibe, rapporter les incompatibilités

2. **Performances** : L'authentification pourrait ajouter de la latence
   - *Atténuation* : Utiliser des tokens JWT avec courte durée de vie, cache

3. **Sécurité** : Mauvaise configuration pourrait exposer le serveur
   - *Atténuation* : Documentation claire, exemples sécurisés par défaut

4. **Migration Utilisateurs** : Les utilisateurs existants devront reconfigurer
   - *Atténuation* : Guide de migration détaillé, support

### Dépendances Supplémentaires

```toml
# À ajouter dans pyproject.toml
[project]
dependencies = [
    # ... existantes ...
    "pyjwt>=2.0.0",
    "python-dotenv>=1.0.0",
]
```

---

## 📞 Support et Maintenance

### Canaux de Support
- Issues GitHub : Pour les bugs et demandes de fonctionnalités
- Documentation : `VIBE.md` et `README.md`
- Discussions : Ouvrir une discussion GitHub pour les questions

### Maintenance Continue
- Mettre à jour les dépendances régulièrement
- Surveiller les vulnérabilités de sécurité
- Maintenir la compatibilité avec les nouvelles versions de Vibe
- Maintenir la compatibilité avec les nouvelles versions de MCP

---

## 🏁 Conclusion

La migration de **chemdraw-mcp** de **Claude Code** vers **Mistral AI Vibe** avec authentification est un projet réalisable en environ 1-2 semaines. Les principales modifications concernent :

1. L'ajout d'un système d'authentification (JWT/Clé API)
2. L'adaptation des scripts d'installation
3. La mise à jour de la documentation
4. Les tests de compatibilité avec Vibe

Le cœur fonctionnel du projet (génération de structures moléculaires) ne nécessite pas de modifications majeures, ce qui limite les risques de régression.

---

*Document généré le : [DATE]*
*Version : 1.0*
*Statut : Planification*
