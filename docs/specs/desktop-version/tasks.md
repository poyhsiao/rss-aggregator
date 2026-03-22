# Desktop Version Implementation Tasks

## Overview

This document outlines the implementation tasks for adding desktop application support to RSS Aggregator. Tasks are organized into phases with clear dependencies.

## Implementation Status: ✅ COMPLETE

All phases have been implemented and verified.

---

## Phase 1: Python stdio Adapter Layer ✅

### 1.1 Core Infrastructure

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-1.1.1 | Create `src/stdio/` module structure | Create `__init__.py`, `server.py`, `router.py`, `protocol.py` | [x] | None |
| T-1.1.2 | Implement JSON-RPC 2.0 protocol handler | Parse and validate JSON-RPC messages in `protocol.py` | [x] | T-1.1.1 |
| T-1.1.3 | Implement stdio server loop | Read from stdin, process, write to stdout in `server.py` | [x] | T-1.1.2 |
| T-1.1.4 | Implement request router | Route JSON-RPC methods to existing API handlers in `router.py` | [x] | T-1.1.3 |

### 1.2 API Route Mapping

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-1.2.1 | Map GET endpoints | Map all GET routes (feed, sources, keys, stats, logs, health) | [x] | T-1.1.4 |
| T-1.2.2 | Map POST endpoints | Map all POST routes (sources, keys) | [x] | T-1.2.1 |
| T-1.2.3 | Map PUT/DELETE endpoints | Map PUT and DELETE routes (sources) | [x] | T-1.2.2 |
| T-1.2.4 | Handle query parameters | Extract and pass query parameters to handlers | [x] | T-1.2.3 |
| T-1.2.5 | Handle request headers | Extract and pass headers (X-API-Key) to handlers | [x] | T-1.2.4 |
| T-1.2.6 | Handle request body | Parse and pass JSON body to handlers | [x] | T-1.2.5 |

### 1.3 Entry Point

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-1.3.1 | Create `main_stdio.py` | Create stdio mode entry point | [x] | T-1.2.6 |
| T-1.3.2 | Add PyInstaller spec | Create PyInstaller spec file for stdio build | [x] | T-1.3.1 |
| T-1.3.3 | Test stdio mode locally | Verify stdio mode works with manual JSON-RPC input | [x] | T-1.3.2 |

---

## Phase 2: Tauri Project Initialization ✅

### 2.1 Project Setup

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-2.1.1 | Initialize Tauri v2 project | Run `cargo tauri init` in project root | [x] | Phase 1 |
| T-2.1.2 | Configure Cargo.toml | Add dependencies (serde, tokio, tauri plugins) | [x] | T-2.1.1 |
| T-2.1.3 | Configure tauri.conf.json | Set app name, version, identifier, window settings | [x] | T-2.1.2 |
| T-2.1.4 | Setup capabilities | Configure Tauri v2 security capabilities | [x] | T-2.1.3 |
| T-2.1.5 | Add application icons | Create icons for all platforms | [x] | T-2.1.4 |

### 2.2 Directory Structure

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-2.2.1 | Create module structure | Create `setup/`, `interceptor/`, `sidecar/`, `utils/` directories | [x] | T-2.1.5 |
| T-2.2.2 | Create module files | Create `mod.rs` and base files for each module | [x] | T-2.2.1 |
| T-2.2.3 | Setup lib.rs exports | Export all modules in `lib.rs` | [x] | T-2.2.2 |

---

## Phase 3: Sidecar Manager ✅

### 3.1 Process Management

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-3.1.1 | Implement path resolution | Resolve sidecar binary path for each platform | [x] | Phase 2 |
| T-3.1.2 | Implement process spawning | Spawn sidecar process with stdin/stdout pipes | [x] | T-3.1.1 |
| T-3.1.3 | Implement process lifecycle | Start, stop, restart, cleanup functions | [x] | T-3.1.2 |
| T-3.1.4 | Handle process errors | Capture stderr, detect crashes, report errors | [x] | T-3.1.3 |

### 3.2 Data Directory Setup

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-3.2.1 | Implement path utilities | Cross-platform path resolution for `./data/` | [x] | T-3.1.4 |
| T-3.2.2 | Create data directory | Ensure `./data/` exists on startup | [x] | T-3.2.1 |
| T-3.2.3 | Set working directory | Set sidecar working directory to app location | [x] | T-3.2.2 |

---

## Phase 4: JSON-RPC Client ✅

### 4.1 Client Implementation

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-4.1.1 | Define request/response types | Create Rust structs for JSON-RPC messages | [x] | Phase 3 |
| T-4.1.2 | Implement stdin writer | Write JSON-RPC requests to sidecar stdin | [x] | T-4.1.1 |
| T-4.1.3 | Implement stdout reader | Read JSON-RPC responses from sidecar stdout | [x] | T-4.1.2 |
| T-4.1.4 | Implement request ID tracking | Track request IDs for response matching | [x] | T-4.1.3 |
| T-4.1.5 | Implement timeout handling | Add timeout for requests (default 30s) | [x] | T-4.1.4 |
| T-4.1.6 | Implement error handling | Parse error responses, convert to Rust errors | [x] | T-4.1.5 |

### 4.2 Client Integration

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-4.2.1 | Create JsonRpcClient struct | Main client struct with send method | [x] | T-4.1.6 |
| T-4.2.2 | Integrate with SidecarManager | Client uses sidecar stdin/stdout | [x] | T-4.2.1 |
| T-4.2.3 | Add unit tests | Test request serialization, response parsing | [x] | T-4.2.2 |

---

## Phase 5: Protocol Interceptor ✅

### 5.1 Interceptor Implementation

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-5.1.1 | Register app://localhost protocol | Register custom protocol in Tauri | [x] | Phase 4 |
| T-5.1.2 | Implement request interception | Intercept WebView requests to app://localhost | [x] | T-5.1.1 |
| T-5.1.3 | Parse HTTP request | Extract method, path, query, headers, body | [x] | T-5.1.2 |
| T-5.1.4 | Convert to JSON-RPC | Transform HTTP request to JSON-RPC format | [x] | T-5.1.3 |
| T-5.1.5 | Send via JsonRpcClient | Forward request to sidecar | [x] | T-5.1.4 |
| T-5.1.6 | Convert response | Transform JSON-RPC response to WebView response | [x] | T-5.1.5 |

### 5.2 Response Handling

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-5.2.1 | Implement WebResourceResponse | Create WebView-compatible response | [x] | T-5.1.6 |
| T-5.2.2 | Handle errors | Return appropriate HTTP error codes | [x] | T-5.2.1 |
| T-5.2.3 | Set response headers | Set content-type and other headers | [x] | T-5.2.2 |

---

## Phase 6: First-run Setup ✅

### 6.1 Configuration Management

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-6.1.1 | Define config schema | Create Config struct for desktop settings | [x] | Phase 5 |
| T-6.1.2 | Implement config read/write | Load from and save to config.json | [x] | T-6.1.1 |
| T-6.1.3 | Implement .setup_done marker | Create and check marker file | [x] | T-6.1.2 |

### 6.2 Database Initialization

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-6.2.1 | Implement DB existence check | Check if rss.db exists | [x] | T-6.1.3 |
| T-6.2.2 | Implement migration runner | Run alembic migrations via sidecar | [x] | T-6.2.1 |
| T-6.2.3 | Implement data validation | Validate imported database schema | [x] | T-6.2.2 |
| T-6.2.4 | Implement data import | Copy and migrate imported database | [x] | T-6.2.3 |

### 6.3 Setup Wizard UI

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-6.3.1 | Create setup window | Separate Tauri window for setup | [x] | T-6.2.4 |
| T-6.3.2 | Implement welcome page | Step 1: Welcome screen | [x] | T-6.3.1 |
| T-6.3.3 | Implement config page | Step 2: Timezone, language selection | [x] | T-6.3.2 |
| T-6.3.4 | Implement RSS sources page | Step 3: Add default sources | [x] | T-6.3.3 |
| T-6.3.5 | Implement import page | Step 4: Data import options | [x] | T-6.3.4 |
| T-6.3.6 | Implement progress page | Step 5: Show initialization progress | [x] | T-6.3.5 |
| T-6.3.7 | Implement complete page | Step 6: Setup complete, launch app | [x] | T-6.3.6 |

### 6.4 Setup Flow Integration

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-6.4.1 | Integrate setup check | Check .setup_done on app start | [x] | T-6.3.7 |
| T-6.4.2 | Implement skip setup | Skip setup if marker exists | [x] | T-6.4.1 |
| T-6.4.3 | Test setup flow | End-to-end setup flow test | [x] | T-6.4.2 |

---

## Phase 7: Frontend Adaptation ✅

### 7.1 Environment Detection

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-7.1.1 | Create environment.ts | Implement isTauri(), getEnvironment(), getPlatformFeatures() | [x] | Phase 5 |
| T-7.1.2 | Add type definitions | Create environment.d.ts | [x] | T-7.1.1 |

### 7.2 API Adaptation

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-7.2.1 | Modify api/index.ts | Set baseURL based on environment | [x] | T-7.1.2 |
| T-7.2.2 | Add @tauri-apps/api | Install Tauri API package | [x] | T-7.2.1 |
| T-7.2.3 | Test API calls | Verify API calls work in both modes | [x] | T-7.2.2 |

### 7.3 Desktop Features

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-7.3.1 | Create tauri-bridge.ts | Implement openDataFolder, exportData, importData, restartBackend | [x] | T-7.2.3 |
| T-7.3.2 | Add desktop settings UI | Conditionally show desktop features in SettingsPage | [x] | T-7.3.1 |
| T-7.3.3 | Add Tauri commands | Implement Rust commands for desktop features | [x] | T-7.3.2 |
| T-7.3.4 | Test desktop features | Verify all desktop-only features work | [x] | T-7.3.3 |

---

## Phase 8: Build Scripts ✅

### 8.1 Sidecar Build

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-8.1.1 | Create build-sidecar.sh | PyInstaller build script | [x] | Phase 1-7 |
| T-8.1.2 | Configure PyInstaller | Set up spec file for all platforms | [x] | T-8.1.1 |
| T-8.1.3 | Test sidecar build | Build sidecar for current platform | [x] | T-8.1.2 |
| T-8.1.4 | Add to tauri.conf.json | Configure externalBin for sidecar | [x] | T-8.1.3 |

### 8.2 Full Build

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-8.2.1 | Create build-all.sh | Complete build pipeline script | [x] | T-8.1.4 |
| T-8.2.2 | Test Windows build | Build and test on Windows | [x] | T-8.2.1 |
| T-8.2.3 | Test macOS build | Build and test on macOS (Intel + ARM) | [x] | T-8.2.2 |
| T-8.2.4 | Test Linux build | Build and test on Linux | [x] | T-8.2.3 |

### 8.3 CI/CD

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-8.3.1 | Create GitHub Actions workflow | Multi-platform build automation | [x] | T-8.2.4 |
| T-8.3.2 | Add release workflow | Automated release creation | [x] | T-8.3.1 |

---

## Phase 9: Testing and Documentation ✅

### 9.1 Integration Testing

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-9.1.1 | Test fresh install | Complete first-run flow test | [x] | Phase 8 |
| T-9.1.2 | Test data import | Import from Docker database | [x] | T-9.1.1 |
| T-9.1.3 | Test data export | Export and verify data | [x] | T-9.1.2 |
| T-9.1.4 | Test error scenarios | Test various error conditions | [x] | T-9.1.3 |

### 9.2 Documentation

| ID | Task | Description | Status | Dependencies |
|----|------|-------------|--------|--------------|
| T-9.2.1 | Update README.md | Add desktop installation instructions | [x] | T-9.1.4 |
| T-9.2.2 | Update CHANGELOG.md | Document new desktop support | [x] | T-9.2.1 |
| T-9.2.3 | Create desktop-specific docs | User guide for desktop features | [x] | T-9.2.2 |

---

## Summary

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Complete | Python stdio Adapter Layer |
| Phase 2 | ✅ Complete | Tauri Project Initialization |
| Phase 3 | ✅ Complete | Sidecar Manager |
| Phase 4 | ✅ Complete | JSON-RPC Client |
| Phase 5 | ✅ Complete | Protocol Interceptor |
| Phase 6 | ✅ Complete | First-run Setup |
| Phase 7 | ✅ Complete | Frontend Adaptation |
| Phase 8 | ✅ Complete | Build Scripts |
| Phase 9 | ✅ Complete | Testing and Documentation |

**Implementation Date:** 2026-03-21
**Total Time:** Completed in single session