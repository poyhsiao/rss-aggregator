#!/bin/bash
#
# Generate all icon sizes for Tauri desktop app and PWA from SVG source.
#

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SVG_SOURCE="$PROJECT_ROOT/assets/icon-source.svg"
TAURI_ICONS_DIR="$PROJECT_ROOT/src-tauri/icons"
PWA_ICONS_DIR="$PROJECT_ROOT/web/public/icons"
WEB_PUBLIC="$PROJECT_ROOT/web/public"

echo "=================================================="
echo "RSS Aggregator Icon Generator"
echo "=================================================="

if [ ! -f "$SVG_SOURCE" ]; then
    echo "Error: SVG source not found at $SVG_SOURCE"
    exit 1
fi

# Create directories
mkdir -p "$TAURI_ICONS_DIR"
mkdir -p "$PWA_ICONS_DIR"

# Convert SVG to PNG using sharp-cli
generate_png() {
    local size=$1
    local output=$2
    echo "Generating $output..."
    npx -y sharp-cli resize $size $size -i "$SVG_SOURCE" -o "$output" -f png 2>/dev/null || \
    npx -y sharp -i "$SVG_SOURCE" resize $size $size -o "$output" 2>/dev/null
}

echo ""
echo "Generating Tauri icons..."

# Tauri/Linux sizes: 32, 64, 128, 256, 512
TAURI_SIZES="32 64 128 256 512"
for size in $TAURI_SIZES; do
    filename="${size}x${size}.png"
    output="$TAURI_ICONS_DIR/$filename"
    generate_png $size "$output"
    echo "  Created: $filename"
done

# Also create 128x128@2x.png (alias for 256x256)
cp "$TAURI_ICONS_DIR/256x256.png" "$TAURI_ICONS_DIR/128x128@2x.png"
echo "  Created: 128x128@2x.png"

# Generate .icns for macOS
echo "  Generating .icns for macOS..."

TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

ICONSET_DIR="$TEMP_DIR/icon.iconset"
mkdir -p "$ICONSET_DIR"

# Required sizes for iconset
for size in 16 32 128 256; do
    generate_png $size "$ICONSET_DIR/icon_${size}x${size}.png"
    
    # Retina (@2x)
    if [ $size -le 256 ]; then
        generate_png $((size * 2)) "$ICONSET_DIR/icon_${size}x${size}@2x.png"
    fi
done

# Create .icns
iconutil -c icns -o "$TAURI_ICONS_DIR/icon.icns" "$ICONSET_DIR" 2>/dev/null || true
echo "    Created: icon.icns"

# Generate .ico for Windows
echo "  Generating .ico for Windows..."

ICO_PNGS=""
for size in 16 32 48 64 128 256; do
    png_path="$TEMP_DIR/ico_${size}.png"
    generate_png $size "$png_path"
    ICO_PNGS="$ICO_PNGS $png_path"
done

npx -y png-to-ico $ICO_PNGS > "$TAURI_ICONS_DIR/icon.ico" 2>/dev/null
echo "    Created: icon.ico"

# Copy SVG for Linux (scalable icon)
cp "$SVG_SOURCE" "$TAURI_ICONS_DIR/icon.svg"
echo "  Created: icon.svg (scalable)"

# Generate PWA icons
echo ""
echo "Generating PWA icons..."

PWA_SIZES="72 96 128 144 152 192 384 512"
for size in $PWA_SIZES; do
    output="$PWA_ICONS_DIR/icon-${size}x${size}.png"
    generate_png $size "$output"
    echo "  Created: icon-${size}x${size}.png"
done

# Copy SVG to PWA icons
cp "$SVG_SOURCE" "$PWA_ICONS_DIR/icon.svg"
echo "  Updated: icon.svg"

# Generate favicon
echo ""
echo "Generating favicon..."
generate_png 32 "$WEB_PUBLIC/favicon.png"
echo "  Created: favicon.png"

echo ""
echo "=================================================="
echo "All icons generated successfully!"
echo "=================================================="