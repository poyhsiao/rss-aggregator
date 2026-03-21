# Dual Deployment Architecture Design

## Overview

This document describes the architecture for supporting two deployment modes:
1. **Docker Mode**: Containerized deployment for server environments
2. **Desktop Mode**: Native desktop application (Windows, macOS, Linux) without Docker or TCP ports

## Design Goals

- **Zero Code Duplication**: Share the same Python backend and Vue frontend codebase between both modes
- **No Docker Required**: Desktop users can run the application without installing Docker
- **No TCP Ports**: Desktop mode uses stdio for IPC, eliminating port binding
- **Portable Data**: Desktop data stored in `./data/` directory for USB drive portability
- **First-run Setup**: Guided setup wizard for desktop users

## Architecture

### System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      Desktop Application                        │
│                      (Tauri v2 Wrapper)                         │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Frontend Layer                         │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │  Vue 3 App (WebView)                                │ │  │
│  │  │  - fetch("app://localhost/api/v1/...")              │ │  │
│  │  │  - Complete reuse of existing web/ code              │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              │ app://localhost/*                │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 Tauri Protocol Handler                    │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │  Rust Interceptor Layer                             │ │  │
│  │  │  - Intercept app://localhost/* requests             │ │  │
│  │  │  - Convert to JSON-RPC format                       │ │  │
│  │  │  - Forward to Python Sidecar via stdio              │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              │ stdin/stdout (JSON-RPC 2.0)     │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Backend Layer                          │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │  FastAPI Server (Sidecar)                           │ │  │
│  │  │  - stdio mode (no HTTP port binding)                │ │  │
│  │  │  - Complete reuse of existing src/ code              │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Data Layer                              │  │
│  │  ./data/                                                  │  │
│  │  ├── rss.db          (SQLite database)                   │  │
│  │  ├── config.json     (Desktop settings)                  │  │
│  │  └── .setup_done     (First-run marker)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### Docker Mode Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      Docker Container                           │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FastAPI Server (main.py)                                      │
│  - HTTP over TCP (port 8000)                                   │
│  - Bound to 127.0.0.1                                          │
│                                                                 │
│  Vue Frontend (served separately or proxied)                   │
│  - Access via http://localhost:51085                           │
│                                                                 │
│  Data: Docker Volume                                           │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
rss-collection/
├── src/                          # Python backend
│   ├── api/                      # API routes (unchanged)
│   ├── models/                   # Data models (unchanged)
│   ├── services/                 # Business logic (unchanged)
│   ├── db/                       # Database (unchanged)
│   ├── formatters/               # Formatters (unchanged)
│   ├── scheduler/                # Scheduler (unchanged)
│   ├── utils/                    # Utilities (unchanged)
│   ├── main.py                   # FastAPI entry point (unchanged)
│   ├── main_stdio.py             # NEW: stdio mode entry point
│   ├── config.py                 # Config (unchanged)
│   └── stdio/                    # NEW: stdio adapter layer
│       ├── __init__.py
│       ├── server.py             # stdio server
│       ├── router.py             # Request router
│       └── protocol.py           # JSON-RPC handling
│
├── web/                          # Vue frontend
│   ├── src/
│   │   ├── api/
│   │   │   └── index.ts          # Modified: environment adaptation
│   │   ├── utils/
│   │   │   ├── environment.ts    # NEW: environment detection
│   │   │   └── tauri-bridge.ts   # NEW: Tauri IPC bridge
│   │   └── pages/
│   │       └── SettingsPage.vue  # Modified: desktop features
│   └── ...
│
├── src-tauri/                    # NEW: Tauri desktop app
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── capabilities/
│   ├── icons/
│   ├── binaries/                 # Sidecar executables
│   │   └── rss-aggregator-backend*
│   └── src/
│       ├── main.rs
│       ├── lib.rs
│       ├── setup/                # First-run setup
│       │   ├── mod.rs
│       │   ├── config.rs
│       │   ├── database.rs
│       │   └── wizard.rs
│       ├── interceptor/          # Protocol interceptor
│       │   ├── mod.rs
│       │   ├── handler.rs
│       │   └── response.rs
│       ├── sidecar/              # Sidecar management
│       │   ├── mod.rs
│       │   ├── process.rs
│       │   └── client.rs
│       └── utils/
│           ├── mod.rs
│           └── paths.rs
│
├── scripts/                      # NEW: Build scripts
│   ├── build-sidecar.sh
│   └── build-all.sh
│
├── docker-compose.yml            # Docker deployment (unchanged)
├── Dockerfile                    # Docker deployment (unchanged)
├── pyproject.toml                # Python config (unchanged)
└── data/                         # NEW: Runtime data (portable)
    ├── rss.db
    ├── config.json
    └── .setup_done
```

## Communication Protocol

### JSON-RPC 2.0 over stdio

**Request Format:**
```json
{
  "jsonrpc": "2.0",
  "method": "GET /api/v1/feed",
  "params": {
    "query": { "format": "json", "sort_by": "published_at" },
    "headers": { "X-API-Key": "xxx" }
  },
  "id": 1
}
```

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": 200,
    "headers": { "content-type": "application/json" },
    "body": { "items": [...], "total": 100 }
  },
  "id": 1
}
```

**Error Response:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": { "detail": "Database connection failed" }
  },
  "id": 1
}
```

## First-run Setup Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    First-run Setup Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: Welcome Page                                           │
│  - Introduction and setup overview                              │
│                                                                 │
│  Step 2: Basic Settings                                         │
│  - Timezone selection                                           │
│  - Language selection                                           │
│                                                                 │
│  Step 3: Default RSS Sources (Optional)                         │
│  - Add default RSS feed URLs                                    │
│  - Can be skipped and added later                               │
│                                                                 │
│  Step 4: Import Existing Data (Optional)                        │
│  - Import from Docker version                                   │
│  - Import from previous installation                            │
│  - Start fresh option                                           │
│                                                                 │
│  Step 5: Initialization                                         │
│  - Create database                                              │
│  - Run migrations                                               │
│  - Import data (if selected)                                    │
│  - Create config.json                                           │
│                                                                 │
│  Step 6: Complete                                               │
│  - Show data location                                           │
│  - Launch application                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Storage

### Desktop Mode (Portable)
- Location: `./data/` (relative to application executable)
- Supports USB drive portability
- Files:
  - `rss.db` - SQLite database
  - `config.json` - Desktop settings
  - `.setup_done` - First-run completion marker

### Docker Mode
- Location: Docker volume
- Path: `./data/` in container (mapped to host)

## Frontend Adaptation

### Environment Detection
```typescript
export const isTauri = (): boolean => {
  return typeof window !== 'undefined' && '__TAURI__' in window
}
```

### API Base URL
```typescript
if (isTauri()) {
  api.defaults.baseURL = 'app://localhost'
} else {
  api.defaults.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
}
```

### Desktop-only Features
- Open data folder
- Export/Import data
- Restart backend service

## Build Process

### Build Pipeline
1. **Python Sidecar Build**: PyInstaller packages FastAPI as standalone executable
2. **Vue Frontend Build**: Vite builds production bundle
3. **Tauri Build**: Combines everything into platform-specific installers

### Output Artifacts
- Windows: `.exe` installer, `.msi`
- macOS: `.dmg`
- Linux: `.deb`, `.AppImage`

## Comparison: Docker vs Desktop

| Item | Docker Mode | Desktop Mode |
|------|-------------|--------------|
| Entry Point | `main.py` | `main_stdio.py` |
| Communication | HTTP over TCP | JSON-RPC over stdio |
| Frontend | Browser `localhost:port` | WebView `app://localhost` |
| Network | TCP port binding | No TCP port |
| Dependencies | Docker Engine | None (standalone) |
| Data Location | Docker volume | `./data/` (portable) |
| Installation | `docker-compose up` | Installer package |
| Target Users | Server deployment | Personal desktop use |

## Implementation Phases

| Phase | Task | Dependencies |
|-------|------|--------------|
| 1 | Python stdio adapter layer (`src/stdio/`) | None |
| 2 | Tauri project initialization (`src-tauri/`) | Phase 1 |
| 3 | Sidecar manager (Rust process management) | Phase 2 |
| 4 | JSON-RPC Client (Rust communication) | Phase 3 |
| 5 | Protocol Interceptor (`app://localhost`) | Phase 4 |
| 6 | First-run Setup (wizard UI) | Phase 5 |
| 7 | Frontend adaptation (Vue environment detection) | Phase 5 |
| 8 | Build scripts (packaging automation) | Phase 1-7 |
| 9 | Testing and debugging | Phase 8 |

## Key Design Decisions

1. **Sidecar Mode**: Python backend packaged as standalone executable, managed by Tauri
2. **JSON-RPC over stdio**: No TCP port binding, pure IPC via stdin/stdout
3. **Portable Data**: All data in `./data/` for USB drive portability
4. **Zero Code Changes**: Existing Python and Vue code unchanged; new adapter layers added
5. **Dual Entry Points**: `main.py` for Docker, `main_stdio.py` for Desktop