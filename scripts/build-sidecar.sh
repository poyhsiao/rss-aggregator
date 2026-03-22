#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$PROJECT_ROOT/src-tauri/binaries"

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

get_extension() {
    local os="$(uname -s)"
    case "$os" in
        MINGW*|MSYS*|CYGWIN*)
            echo ".exe"
            ;;
        *)
            echo ""
            ;;
    esac
}

build_sidecar() {
    local target="$1"
    local ext="$2"
    
    echo "Building sidecar for target: $target"
    
    cd "$PROJECT_ROOT"
    
    if [ ! -d ".venv" ]; then
        echo "Creating virtual environment..."
        uv venv
    fi
    
    echo "Installing dependencies..."
    uv sync
    
    echo "Running PyInstaller..."
    uv run pyinstaller scripts/rss-sidecar.spec \
        --distpath "$OUTPUT_DIR" \
        --workpath "$PROJECT_ROOT/build/pyinstaller" \
        --clean \
        --noconfirm
    
    local original_binary="$OUTPUT_DIR/rss-sidecar$ext"
    local target_binary="$OUTPUT_DIR/rss-sidecar-$target$ext"
    
    if [ -f "$original_binary" ]; then
        mv "$original_binary" "$target_binary"
        echo "Renamed binary to: $target_binary"
    fi
    
    local binary_name="rss-sidecar-$target$ext"
    local binary_path="$OUTPUT_DIR/$binary_name"
    
    if [ -f "$binary_path" ]; then
        echo "Sidecar built successfully: $binary_path"
        chmod +x "$binary_path"
    else
        echo "Error: Binary not found at $binary_path" >&2
        exit 1
    fi
}

main() {
    echo "=== Building RSS Aggregator Sidecar ==="
    
    local target
    if [ -n "$1" ]; then
        target="$1"
    else
        target="$(detect_target)"
    fi
    
    local ext
    if [ -n "$2" ]; then
        ext="$2"
    else
        ext="$(get_extension)"
    fi
    
    mkdir -p "$OUTPUT_DIR"
    
    build_sidecar "$target" "$ext"
    
    echo "=== Build Complete ==="
    echo "Binary: $OUTPUT_DIR/rss-sidecar-$target$ext"
}

main "$@"