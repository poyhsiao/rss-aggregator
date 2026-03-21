# Desktop Version Design

## 1. System Architecture

### 1.1 Overview

The desktop version uses a **Sidecar Architecture** where Tauri (Rust) wraps the Python backend and Vue frontend. Communication between frontend and backend uses JSON-RPC over stdio, eliminating the need for TCP ports.

```
┌────────────────────────────────────────────────────────────────┐
│                      Desktop Application                        │
│                      (Tauri v2 Wrapper)                         │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Frontend Layer                         │  │
│  │  Vue 3 App (WebView)                                      │  │
│  │  - fetch("app://localhost/api/v1/...")                    │  │
│  │  - Complete reuse of existing web/ code                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              │ app://localhost/*                │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 Tauri Protocol Handler                    │  │
│  │  - Intercept app://localhost/* requests                   │  │
│  │  - Convert to JSON-RPC format                             │  │
│  │  - Forward to Python Sidecar via stdio                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              │ stdin/stdout (JSON-RPC 2.0)     │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Backend Layer                          │  │
│  │  FastAPI Server (Sidecar)                                 │  │
│  │  - stdio mode (no HTTP port binding)                      │  │
│  │  - Complete reuse of existing src/ code                    │  │
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

### 1.2 Comparison with Docker Mode

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Mode                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐         ┌─────────────────────────────────────┐│
│  │ Browser     │─HTTP───►│ FastAPI Server                      ││
│  │             │ :51085  │ main.py                             ││
│  └─────────────┘         │ - HTTP over TCP                     ││
│                          │ - Port binding required              ││
│                          └─────────────────────────────────────┘│
│                                        │                        │
│                                        ▼                        │
│                          ┌─────────────────────────────────────┐│
│                          │ Docker Volume                        ││
│                          │ ./data/rss.db                       ││
│                          └─────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Module Design

### 2.1 Python Backend (src/stdio/)

#### 2.1.1 Module Structure

```
src/stdio/
├── __init__.py
├── server.py       # stdio server main loop
├── router.py       # Request routing to existing handlers
└── protocol.py     # JSON-RPC 2.0 message handling
```

#### 2.1.2 Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| `server.py` | Main event loop, stdin/stdout I/O, error handling |
| `router.py` | Parse HTTP method/path, route to existing API handlers |
| `protocol.py` | JSON-RPC 2.0 message formatting and validation |

#### 2.1.3 Server Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    stdio Server Loop                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  while True:                                                │
│      │                                                      │
│      ▼                                                      │
│  ┌─────────────────┐                                        │
│  │ Read from stdin │  (blocking)                            │
│  └─────────────────┘                                        │
│      │                                                      │
│      ▼                                                      │
│  ┌─────────────────┐                                        │
│  │ Parse JSON-RPC  │                                        │
│  └─────────────────┘                                        │
│      │                                                      │
│      ├──[Parse Error]──► Return error response              │
│      │                                                      │
│      ▼                                                      │
│  ┌─────────────────┐                                        │
│  │ Route request   │                                        │
│  └─────────────────┘                                        │
│      │                                                      │
│      ├──[Route Not Found]──► Return error response          │
│      │                                                      │
│      ▼                                                      │
│  ┌─────────────────┐                                        │
│  │ Execute handler │  (call existing API logic)             │
│  └─────────────────┘                                        │
│      │                                                      │
│      ├──[Exception]──► Return error response                │
│      │                                                      │
│      ▼                                                      │
│  ┌─────────────────┐                                        │
│  │ Write to stdout │  (JSON-RPC response)                   │
│  └─────────────────┘                                        │
│      │                                                      │
│      ▼                                                      │
│  (loop continues)                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Rust Backend (src-tauri/src/)

#### 2.2.1 Module Structure

```
src-tauri/src/
├── main.rs           # Application entry point
├── lib.rs            # Module exports
├── setup/            # First-run setup
│   ├── mod.rs
│   ├── config.rs     # Configuration management
│   ├── database.rs   # Database initialization
│   └── wizard.rs     # Setup wizard UI logic
├── interceptor/      # Protocol interceptor
│   ├── mod.rs
│   ├── handler.rs    # app://localhost handler
│   └── response.rs   # Response transformation
├── sidecar/          # Sidecar management
│   ├── mod.rs
│   ├── process.rs    # Process lifecycle
│   └── client.rs     # JSON-RPC client
└── utils/            # Utilities
    ├── mod.rs
    └── paths.rs      # Path handling
```

#### 2.2.2 Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| `main.rs` | Tauri app initialization, window creation |
| `setup/*` | First-run wizard, config/db initialization |
| `interceptor/*` | Intercept app://localhost, convert to JSON-RPC |
| `sidecar/*` | Manage Python process, JSON-RPC communication |
| `utils/*` | Cross-platform path handling, helpers |

### 2.3 Frontend Adaptation (web/src/)

#### 2.3.1 New Files

```
web/src/
├── api/
│   └── index.ts          # Modified: environment-aware base URL
├── utils/
│   ├── environment.ts    # NEW: Environment detection
│   └── tauri-bridge.ts   # NEW: Tauri IPC bridge
└── types/
    └── environment.d.ts  # NEW: Type definitions
```

#### 2.3.2 Environment Detection

```typescript
// web/src/utils/environment.ts

export const isTauri = (): boolean => {
  return typeof window !== 'undefined' && '__TAURI__' in window
}

export type Environment = 'web' | 'tauri'

export const getEnvironment = (): Environment => {
  return isTauri() ? 'tauri' : 'web'
}

export interface PlatformFeatures {
  showDesktopFeatures: boolean
  canOpenFolder: boolean
  canExportImport: boolean
  canRestartBackend: boolean
}

export const getPlatformFeatures = (): PlatformFeatures => {
  if (isTauri()) {
    return {
      showDesktopFeatures: true,
      canOpenFolder: true,
      canExportImport: true,
      canRestartBackend: true,
    }
  }
  return {
    showDesktopFeatures: false,
    canOpenFolder: false,
    canExportImport: false,
    canRestartBackend: false,
  }
}
```

## 3. Communication Protocol

### 3.1 JSON-RPC 2.0 Specification

#### 3.1.1 Request Format

```json
{
  "jsonrpc": "2.0",
  "method": "<HTTP_METHOD> <PATH>",
  "params": {
    "query": { "<key>": "<value>" },
    "headers": { "<key>": "<value>" },
    "body": <any>
  },
  "id": <number>
}
```

#### 3.1.2 Success Response Format

```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": <HTTP_STATUS_CODE>,
    "headers": { "<key>": "<value>" },
    "body": <any>
  },
  "id": <number>
}
```

#### 3.1.3 Error Response Format

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": <ERROR_CODE>,
    "message": "<ERROR_MESSAGE>",
    "data": <optional_error_details>
  },
  "id": <number>
}
```

### 3.2 Error Codes

| Code | Message | Description |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid Request | Not a valid JSON-RPC request |
| -32601 | Method not found | Route does not exist |
| -32602 | Invalid params | Invalid query/body parameters |
| -32603 | Internal error | Server-side error |

### 3.3 Request/Response Examples

#### GET Request

```json
// Request
{
  "jsonrpc": "2.0",
  "method": "GET /api/v1/feed",
  "params": {
    "query": { "format": "json", "sort_by": "published_at" },
    "headers": { "X-API-Key": "user-api-key" }
  },
  "id": 1
}

// Response
{
  "jsonrpc": "2.0",
  "result": {
    "status": 200,
    "headers": { "content-type": "application/json" },
    "body": {
      "items": [...],
      "total": 100
    }
  },
  "id": 1
}
```

#### POST Request

```json
// Request
{
  "jsonrpc": "2.0",
  "method": "POST /api/v1/sources",
  "params": {
    "headers": { "X-API-Key": "user-api-key" },
    "body": {
      "name": "Example Feed",
      "url": "https://example.com/feed.xml"
    }
  },
  "id": 2
}

// Response
{
  "jsonrpc": "2.0",
  "result": {
    "status": 201,
    "headers": { "content-type": "application/json" },
    "body": {
      "id": 1,
      "name": "Example Feed",
      "url": "https://example.com/feed.xml"
    }
  },
  "id": 2
}
```

## 4. Data Design

### 4.1 Data Directory Structure

```
./data/
├── rss.db            # SQLite database
├── config.json       # Desktop configuration
├── .setup_done       # First-run completion marker
└── logs/             # Application logs (optional)
    └── sidecar.log
```

### 4.2 Configuration Schema

```json
// config.json
{
  "version": "0.5.1",
  "setup_completed_at": "2026-03-21T10:30:00+08:00",
  "timezone": "Asia/Taipei",
  "language": "en",
  "last_run_at": "2026-03-21T15:00:00+08:00"
}
```

### 4.3 First-run Marker

The `.setup_done` file is an empty file created after successful first-run setup completion. Its presence indicates setup is complete and the wizard should not be shown again.

## 5. First-run Setup Design

### 5.1 Setup Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    First-run Setup Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐                                               │
│  │ App Start    │                                               │
│  └──────┬───────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐     Yes    ┌──────────────┐                   │
│  │ .setup_done  │────────────►│ Skip Setup   │                   │
│  │ exists?      │             └──────────────┘                   │
│  └──────┬───────┘                    │                          │
│         │ No                          │                          │
│         ▼                             │                          │
│  ┌──────────────┐                     │                          │
│  │ Show Setup   │                     │                          │
│  │ Wizard       │                     │                          │
│  └──────┬───────┘                     │                          │
│         │                             │                          │
│         ▼                             │                          │
│  ┌──────────────┐                     │                          │
│  │ Step 1:      │                     │                          │
│  │ Welcome      │                     │                          │
│  └──────┬───────┘                     │                          │
│         │                             │                          │
│         ▼                             │                          │
│  ┌──────────────┐                     │                          │
│  │ Step 2:      │                     │                          │
│  │ Basic Config │                     │                          │
│  │ (TZ, Lang)   │                     │                          │
│  └──────┬───────┘                     │                          │
│         │                             │                          │
│         ▼                             │                          │
│  ┌──────────────┐                     │                          │
│  │ Step 3:      │                     │                          │
│  │ Default RSS  │                     │                          │
│  │ (Optional)   │                     │                          │
│  └──────┬───────┘                     │                          │
│         │                             │                          │
│         ▼                             │                          │
│  ┌──────────────┐                     │                          │
│  │ Step 4:      │                     │                          │
│  │ Import Data  │                     │                          │
│  │ (Optional)   │                     │                          │
│  └──────┬───────┘                     │                          │
│         │                             │                          │
│         ▼                             │                          │
│  ┌──────────────┐                     │                          │
│  │ Step 5:      │                     │                          │
│  │ Initialize   │                     │                          │
│  └──────┬───────┘                     │                          │
│         │                             │                          │
│         ▼                             ▼                          │
│  ┌──────────────┐              ┌──────────────┐                  │
│  │ Create       │              │ Start Main   │                  │
│  │ .setup_done  │              │ Application  │                  │
│  └──────────────┘              └──────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Database Initialization Logic

```
┌─────────────────────────────────────────────────────────────┐
│                Database Initialization                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Case A: Fresh Install                                      │
│  ─────────────────────                                      │
│  1. Ensure ./data/ directory exists                         │
│  2. Run alembic upgrade head                                │
│  3. Create .setup_done marker                               │
│                                                             │
│  Case B: Import Existing Data                               │
│  ─────────────────────────                                  │
│  1. User selects source file (rss.db)                       │
│  2. Validate file integrity                                 │
│     - Check if valid SQLite DB                              │
│     - Check schema version                                  │
│  3. Copy to ./data/rss.db                                   │
│  4. Run alembic upgrade head if needed (migration)          │
│  5. Create .setup_done marker                               │
│                                                             │
│  Case C: Version Upgrade (.setup_done exists)               │
│  ─────────────────────────────────────────                  │
│  1. Check config.json version                               │
│  2. If version < current, run migrations                    │
│  3. Update config.json version                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 6. Build Design

### 6.1 Build Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                     Build Pipeline                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Stage 1: Python Sidecar Build                                  │
│  ─────────────────────────────                                  │
│  Input:  src/                                                   │
│  Tool:   PyInstaller                                            │
│  Output: binaries/rss-aggregator-backend-{platform}             │
│                                                                 │
│  Stage 2: Vue Frontend Build                                    │
│  ─────────────────────────────                                  │
│  Input:  web/                                                   │
│  Tool:   Vite                                                   │
│  Output: web/dist/                                              │
│                                                                 │
│  Stage 3: Tauri Build                                           │
│  ─────────────────────────────                                  │
│  Input:  src-tauri/ + binaries/ + web/dist/                     │
│  Tool:   cargo tauri build                                      │
│  Output: Platform-specific installers                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Output Artifacts

| Platform | Format | Filename Pattern |
|----------|--------|-----------------|
| Windows | EXE, MSI | `rss-aggregator_{version}_x64-setup.exe` |
| macOS | DMG | `rss-aggregator_{version}_x64.dmg` |
| macOS ARM | DMG | `rss-aggregator_{version}_aarch64.dmg` |
| Linux | DEB | `rss-aggregator_{version}_amd64.deb` |
| Linux | AppImage | `rss-aggregator_{version}_amd64.AppImage` |

## 7. Error Handling

### 7.1 Sidecar Startup Errors

| Error | User Message | Recovery Action |
|-------|--------------|-----------------|
| Sidecar binary not found | "Application files are corrupted. Please reinstall." | Reinstall |
| Sidecar crash on startup | "Failed to start backend service. Check logs for details." | Show logs, retry |
| Database locked | "Database is in use by another instance." | Close other instance |

### 7.2 JSON-RPC Errors

| Error | Handling |
|-------|----------|
| Parse error | Return JSON-RPC error, log raw input |
| Route not found | Return 404 equivalent error |
| Handler exception | Return 500 equivalent error, log stack trace |

### 7.3 Setup Wizard Errors

| Error | Handling |
|-------|----------|
| Invalid import file | Show error message, allow retry |
| Database migration failure | Show error, offer to start fresh |
| Permission denied | Show error, guide user to fix permissions |

## 8. Testing Strategy

### 8.1 Unit Tests

| Component | Test Focus |
|-----------|------------|
| `stdio/server.py` | JSON parsing, request routing |
| `stdio/protocol.py` | JSON-RPC format validation |
| `sidecar/client.rs` | JSON-RPC client logic |
| `interceptor/handler.rs` | Request transformation |

### 8.2 Integration Tests

| Test Case | Description |
|-----------|-------------|
| End-to-end API call | Frontend → Interceptor → Sidecar → Response |
| First-run flow | Complete setup wizard |
| Data import | Import Docker database |
| Data export | Export and verify data |

### 8.3 Platform Tests

| Platform | Test Matrix |
|----------|-------------|
| Windows | Windows 10, Windows 11 |
| macOS | Intel (x64), Apple Silicon (ARM) |
| Linux | Ubuntu 22.04, Debian 12 |

## 9. Deployment Comparison

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