# Desktop Version Implementation Tasks

## Overview

This document outlines the implementation tasks for adding desktop application support to RSS Aggregator. Tasks are organized into phases with clear dependencies.

## Phase 1: Python stdio Adapter Layer

### 1.1 Core Infrastructure

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-1.1.1 | Create `src/stdio/` module structure | Create `__init__.py`, `server.py`, `router.py`, `protocol.py` | [ ] | None |
| T-1.1.2 | Implement JSON-RPC 2.0 protocol handler | Parse and validate JSON-RPC messages in `protocol.py` | [ ] | T-1.1.1 |
| T-1.1.3 | Implement stdio server loop | Read from stdin, process, write to stdout in `server.py` | [ ] | T-1.1.2 |
| T-1.1.4 | Implement request router | Route JSON-RPC methods to existing API handlers in `router.py` | [ ] | T-1.1.3 |

### 1.2 API Route Mapping

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-1.2.1 | Map GET endpoints | Map all GET routes (feed, sources, keys, stats, logs, health) | [ ] | T-1.1.4 |
| T-1.2.2 | Map POST endpoints | Map all POST routes (sources, keys) | [ ] | T-1.2.1 |
| T-1.2.3 | Map PUT/DELETE endpoints | Map PUT and DELETE routes (sources) | [ ] | T-1.2.2 |
| T-1.2.4 | Handle query parameters | Extract and pass query parameters to handlers | [ ] | T-1.2.3 |
| T-1.2.5 | Handle request headers | Extract and pass headers (X-API-Key) to handlers | [ ] | T-1.2.4 |
| T-1.2.6 | Handle request body | Parse and pass JSON body to handlers | [ ] | T-1.2.5 |

### 1.3 Entry Point

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-1.3.1 | Create `main_stdio.py` | Create stdio mode entry point | [ ] | T-1.2.6 |
| T-1.3.2 | Add PyInstaller spec | Create PyInstaller spec file for stdio build | [ ] | T-1.3.1 |
| T-1.3.3 | Test stdio mode locally | Verify stdio mode works with manual JSON-RPC input | [ ] | T-1.3.2 |

**Phase 1 Deliverable**: Working Python stdio adapter that can receive JSON-RPC requests and return responses.

---

## Phase 2: Tauri Project Initialization

### 2.1 Project Setup

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-2.1.1 | Initialize Tauri v2 project | Run `cargo tauri init` in project root | [ ] | Phase 1 |
| T-2.1.2 | Configure Cargo.toml | Add dependencies (serde, tokio, tauri plugins) | [ ] | T-2.1.1 |
| T-2.1.3 | Configure tauri.conf.json | Set app name, version, identifier, window settings | [ ] | T-2.1.2 |
| T-2.1.4 | Setup capabilities | Configure Tauri v2 security capabilities | [ ] | T-2.1.3 |
| T-2.1.5 | Add application icons | Create icons for all platforms | [ ] | T-2.1.4 |

### 2.2 Directory Structure

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-2.2.1 | Create module structure | Create `setup/`, `interceptor/`, `sidecar/`, `utils/` directories | [ ] | T-2.1.5 |
| T-2.2.2 | Create module files | Create `mod.rs` and base files for each module | [ ] | T-2.2.1 |
| T-2.2.3 | Setup lib.rs exports | Export all modules in `lib.rs` | [ ] | T-2.2.2 |

**Phase 2 Deliverable**: Initialized Tauri project with proper structure and configuration.

---

## Phase 3: Sidecar Manager

### 3.1 Process Management

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-3.1.1 | Implement path resolution | Resolve sidecar binary path for each platform | [ ] | Phase 2 |
| T-3.1.2 | Implement process spawning | Spawn sidecar process with stdin/stdout pipes | [ ] | T-3.1.1 |
| T-3.1.3 | Implement process lifecycle | Start, stop, restart, cleanup functions | [ ] | T-3.1.2 |
| T-3.1.4 | Handle process errors | Capture stderr, detect crashes, report errors | [ ] | T-3.1.3 |

### 3.2 Data Directory Setup

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-3.2.1 | Implement path utilities | Cross-platform path resolution for `./data/` | [ ] | T-3.1.4 |
| T-3.2.2 | Create data directory | Ensure `./data/` exists on startup | [ ] | T-3.2.1 |
| T-3.2.3 | Set working directory | Set sidecar working directory to app location | [ ] | T-3.2.2 |

**Phase 3 Deliverable**: Working sidecar manager that can start/stop Python process.

---

## Phase 4: JSON-RPC Client

### 4.1 Client Implementation

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-4.1.1 | Define request/response types | Create Rust structs for JSON-RPC messages | [ ] | Phase 3 |
| T-4.1.2 | Implement stdin writer | Write JSON-RPC requests to sidecar stdin | [ ] | T-4.1.1 |
| T-4.1.3 | Implement stdout reader | Read JSON-RPC responses from sidecar stdout | [ ] | T-4.1.2 |
| T-4.1.4 | Implement request ID tracking | Track request IDs for response matching | [ ] | T-4.1.3 |
| T-4.1.5 | Implement timeout handling | Add timeout for requests (default 30s) | [ ] | T-4.1.4 |
| T-4.1.6 | Implement error handling | Parse error responses, convert to Rust errors | [ ] | T-4.1.5 |

### 4.2 Client Integration

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-4.2.1 | Create JsonRpcClient struct | Main client struct with send method | [ ] | T-4.1.6 |
| T-4.2.2 | Integrate with SidecarManager | Client uses sidecar stdin/stdout | [ ] | T-4.2.1 |
| T-4.2.3 | Add unit tests | Test request serialization, response parsing | [ ] | T-4.2.2 |

**Phase 4 Deliverable**: Working JSON-RPC client that can communicate with Python sidecar.

---

## Phase 5: Protocol Interceptor

### 5.1 Interceptor Implementation

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-5.1.1 | Register app://localhost protocol | Register custom protocol in Tauri | [ ] | Phase 4 |
| T-5.1.2 | Implement request interception | Intercept WebView requests to app://localhost | [ ] | T-5.1.1 |
| T-5.1.3 | Parse HTTP request | Extract method, path, query, headers, body | [ ] | T-5.1.2 |
| T-5.1.4 | Convert to JSON-RPC | Transform HTTP request to JSON-RPC format | [ ] | T-5.1.3 |
| T-5.1.5 | Send via JsonRpcClient | Forward request to sidecar | [ ] | T-5.1.4 |
| T-5.1.6 | Convert response | Transform JSON-RPC response to WebView response | [ ] | T-5.1.5 |

### 5.2 Response Handling

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-5.2.1 | Implement WebResourceResponse | Create WebView-compatible response | [ ] | T-5.1.6 |
| T-5.2.2 | Handle errors | Return appropriate HTTP error codes | [ ] | T-5.2.1 |
| T-5.2.3 | Set response headers | Set content-type and other headers | [ ] | T-5.2.2 |

**Phase 5 Deliverable**: Working protocol interceptor that routes frontend requests to sidecar.

---

## Phase 6: First-run Setup

### 6.1 Configuration Management

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-6.1.1 | Define config schema | Create Config struct for desktop settings | [ ] | Phase 5 |
| T-6.1.2 | Implement config read/write | Load from and save to config.json | [ ] | T-6.1.1 |
| T-6.1.3 | Implement .setup_done marker | Create and check marker file | [ ] | T-6.1.2 |

### 6.2 Database Initialization

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-6.2.1 | Implement DB existence check | Check if rss.db exists | [ ] | T-6.1.3 |
| T-6.2.2 | Implement migration runner | Run alembic migrations via sidecar | [ ] | T-6.2.1 |
| T-6.2.3 | Implement data validation | Validate imported database schema | [ ] | T-6.2.2 |
| T-6.2.4 | Implement data import | Copy and migrate imported database | [ ] | T-6.2.3 |

### 6.3 Setup Wizard UI

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-6.3.1 | Create setup window | Separate Tauri window for setup | [ ] | T-6.2.4 |
| T-6.3.2 | Implement welcome page | Step 1: Welcome screen | [ ] | T-6.3.1 |
| T-6.3.3 | Implement config page | Step 2: Timezone, language selection | [ ] | T-6.3.2 |
| T-6.3.4 | Implement RSS sources page | Step 3: Add default sources | [ ] | T-6.3.3 |
| T-6.3.5 | Implement import page | Step 4: Data import options | [ ] | T-6.3.4 |
| T-6.3.6 | Implement progress page | Step 5: Show initialization progress | [ ] | T-6.3.5 |
| T-6.3.7 | Implement complete page | Step 6: Setup complete, launch app | [ ] | T-6.3.6 |

### 6.4 Setup Flow Integration

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-6.4.1 | Integrate setup check | Check .setup_done on app start | [ ] | T-6.3.7 |
| T-6.4.2 | Implement skip setup | Skip setup if marker exists | [ ] | T-6.4.1 |
| T-6.4.3 | Test setup flow | End-to-end setup flow test | [ ] | T-6.4.2 |

**Phase 6 Deliverable**: Working first-run setup wizard.

---

## Phase 7: Frontend Adaptation

### 7.1 Environment Detection

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-7.1.1 | Create environment.ts | Implement isTauri(), getEnvironment(), getPlatformFeatures() | [ ] | Phase 5 |
| T-7.1.2 | Add type definitions | Create environment.d.ts | [ ] | T-7.1.1 |

### 7.2 API Adaptation

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-7.2.1 | Modify api/index.ts | Set baseURL based on environment | [ ] | T-7.1.2 |
| T-7.2.2 | Add @tauri-apps/api | Install Tauri API package | [ ] | T-7.2.1 |
| T-7.2.3 | Test API calls | Verify API calls work in both modes | [ ] | T-7.2.2 |

### 7.3 Desktop Features

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-7.3.1 | Create tauri-bridge.ts | Implement openDataFolder, exportData, importData, restartBackend | [ ] | T-7.2.3 |
| T-7.3.2 | Add desktop settings UI | Conditionally show desktop features in SettingsPage | [ ] | T-7.3.1 |
| T-7.3.3 | Add Tauri commands | Implement Rust commands for desktop features | [ ] | T-7.3.2 |
| T-7.3.4 | Test desktop features | Verify all desktop-only features work | [ ] | T-7.3.3 |

**Phase 7 Deliverable**: Frontend adapted for both web and desktop modes.

---

## Phase 8: Build Scripts

### 8.1 Sidecar Build

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-8.1.1 | Create build-sidecar.sh | PyInstaller build script | [ ] | Phase 1-7 |
| T-8.1.2 | Configure PyInstaller | Set up spec file for all platforms | [ ] | T-8.1.1 |
| T-8.1.3 | Test sidecar build | Build sidecar for current platform | [ ] | T-8.1.2 |
| T-8.1.4 | Add to tauri.conf.json | Configure externalBin for sidecar | [ ] | T-8.1.3 |

### 8.2 Full Build

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-8.2.1 | Create build-all.sh | Complete build pipeline script | [ ] | T-8.1.4 |
| T-8.2.2 | Test Windows build | Build and test on Windows | [ ] | T-8.2.1 |
| T-8.2.3 | Test macOS build | Build and test on macOS (Intel + ARM) | [ ] | T-8.2.2 |
| T-8.2.4 | Test Linux build | Build and test on Linux | [ ] | T-8.2.3 |

### 8.3 CI/CD

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-8.3.1 | Create GitHub Actions workflow | Multi-platform build automation | [ ] | T-8.2.4 |
| T-8.3.2 | Add release workflow | Automated release creation | [ ] | T-8.3.1 |

**Phase 8 Deliverable**: Complete build pipeline with CI/CD.

---

## Phase 9: Testing and Documentation

### 9.1 Integration Testing

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-9.1.1 | Test fresh install | Complete first-run flow test | [ ] | Phase 8 |
| T-9.1.2 | Test data import | Import from Docker database | [ ] | T-9.1.1 |
| T-9.1.3 | Test data export | Export and verify data | [ ] | T-9.1.2 |
| T-9.1.4 | Test error scenarios | Test various error conditions | [ ] | T-9.1.3 |

### 9.2 Documentation

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-9.2.1 | Update README.md | Add desktop installation instructions | [ ] | T-9.1.4 |
| T-9.2.2 | Update CHANGELOG.md | Document new desktop support | [ ] | T-9.2.1 |
| T-9.2.3 | Create desktop-specific docs | User guide for desktop features | [ ] | T-9.2.2 |

**Phase 9 Deliverable**: Fully tested and documented desktop application.

---

## Task Dependencies Graph

```
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5
                                                        │
                                                        ▼
                                          Phase 6 ◄────┘
                                              │
                                              ▼
                                          Phase 7 ◄────┘
                                              │
                                              ▼
                                          Phase 8 ──► Phase 9
```

## Effort Estimation

| Phase | Estimated Days | Risk Level |
|-------|---------------|------------|
| Phase 1 | 3-5 | Medium |
| Phase 2 | 1-2 | Low |
| Phase 3 | 2-3 | Medium |
| Phase 4 | 3-4 | High |
| Phase 5 | 3-5 | High |
| Phase 6 | 5-7 | Medium |
| Phase 7 | 2-3 | Low |
| Phase 8 | 3-4 | Medium |
| Phase 9 | 2-3 | Low |
| **Total** | **24-36 days** | - |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Phase 4 complexity (JSON-RPC) | Prototype early in Phase 1 |
| Phase 5 complexity (Interceptor) | Study Tauri protocol examples |
| Cross-platform issues | Test on all platforms in Phase 8 |
| PyInstaller packaging issues | Use proven configurations, test early |