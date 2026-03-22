#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

detect_target() {
    local os="$(uname -s)"
    local arch="$(uname -m)"
    
    case "$os" in
        Darwin)
            if [ "$arch" = "arm64" ]; then
                echo "aarch64-apple-darwin"
            else
                echo "x86_64-apple-darwin"
            fi
            ;;
        Linux)
            echo "x86_64-unknown-linux-gnu"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            echo "x86_64-pc-windows-msvc"
            ;;
        *)
            echo "Unknown platform: $os $arch" >&2
            exit 1
            ;;
    esac
}

build_frontend() {
    echo "=== Building Frontend ==="
    cd "$PROJECT_ROOT/web"
    
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        pnpm install
    fi
    
    echo "Building Vue application..."
    pnpm build
    
    echo "Frontend build complete"
}

build_sidecar() {
    echo "=== Building Sidecar ==="
    cd "$PROJECT_ROOT"
    bash scripts/build-sidecar.sh
}

build_tauri() {
    echo "=== Building Tauri Application ==="
    cd "$PROJECT_ROOT/src-tauri"
    
    echo "Building Tauri app..."
    cargo tauri build
    
    echo "Tauri build complete"
}

build_dev() {
    echo "=== Development Build ==="
    
    build_frontend
    build_sidecar
    
    echo "=== Development Build Complete ==="
    echo "Run 'cargo tauri dev' to start the development server"
}

build_release() {
    echo "=== Release Build ==="
    
    build_frontend
    build_sidecar
    build_tauri
    
    echo "=== Release Build Complete ==="
    echo "Check src-tauri/target/release/bundle/ for installers"
}

show_help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  dev       Build frontend and sidecar for development"
    echo "  release   Build complete release application"
    echo "  frontend  Build only the frontend"
    echo "  sidecar   Build only the sidecar"
    echo "  tauri     Build only the Tauri application"
    echo "  help      Show this help message"
}

main() {
    local command="${1:-release}"
    
    case "$command" in
        dev)
            build_dev
            ;;
        release)
            build_release
            ;;
        frontend)
            build_frontend
            ;;
        sidecar)
            build_sidecar
            ;;
        tauri)
            build_tauri
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo "Unknown command: $command" >&2
            show_help
            exit 1
            ;;
    esac
}

main "$@"