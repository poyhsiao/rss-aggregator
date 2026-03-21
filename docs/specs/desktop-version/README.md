# Desktop Version Specification

## Overview

This specification defines the desktop application support for RSS Aggregator, enabling users to run the application without Docker or TCP port binding.

## Documents

| Document | Description |
|----------|-------------|
| [requirements.md](./requirements.md) | Functional and non-functional requirements, user stories |
| [design.md](./design.md) | Technical architecture, module design, communication protocol |
| [tasks.md](./tasks.md) | Implementation tasks organized by phase |

## Quick Reference

### Key Decisions

- **Framework**: Tauri v2 for desktop wrapper
- **Communication**: JSON-RPC 2.0 over stdio (no TCP ports)
- **Data Storage**: Portable `./data/` directory
- **Code Sharing**: Single codebase for Docker and Desktop modes

### Deployment Modes Comparison

| Item | Docker Mode | Desktop Mode |
|------|-------------|--------------|
| TCP Port | Required | Not required |
| Docker | Required | Not required |
| Communication | HTTP over TCP | JSON-RPC over stdio |
| Data Location | Docker volume | `./data/` (portable) |
| Entry Point | `main.py` | `main_stdio.py` |

### Implementation Phases

1. Python stdio Adapter Layer
2. Tauri Project Initialization
3. Sidecar Manager
4. JSON-RPC Client
5. Protocol Interceptor
6. First-run Setup
7. Frontend Adaptation
8. Build Scripts
9. Testing and Documentation

### Estimated Effort

- **Total**: 24-36 days
- **High Risk Phases**: Phase 4 (JSON-RPC Client), Phase 5 (Protocol Interceptor)