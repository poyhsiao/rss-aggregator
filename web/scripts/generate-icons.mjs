#!/usr/bin/env node
/**
 * Generate PWA icons and favicon from SVG source using sharp
 *
 * Usage: pnpm generate-icons
 *
 * This script reads the SVG icon from assets/icon-source.svg
 * and generates:
 * - PNG icons for all sizes specified in manifest.json
 * - favicon.ico (multi-resolution ICO with 16, 32, 48)
 * - favicon.png (32x32 fallback)
 */

import sharp from 'sharp';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join, dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512];
const SVG_PATH = resolve(__dirname, '../../assets/icon-source.svg');
const OUTPUT_DIR = join(__dirname, '../public/icons');
const PUBLIC_DIR = join(__dirname, '../public');

async function generateIcons() {
  // Check if SVG exists
  if (!existsSync(SVG_PATH)) {
    console.error('Error: icon-source.svg not found at', SVG_PATH);
    process.exit(1);
  }

  console.log('Source SVG:', SVG_PATH);

  // Ensure output directory exists
  if (!existsSync(OUTPUT_DIR)) {
    mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  // Read SVG buffer
  const svgBuffer = readFileSync(SVG_PATH);

  console.log('\nGenerating PWA icons...');

  // Generate each size
  for (const size of ICON_SIZES) {
    const outputPath = join(OUTPUT_DIR, `icon-${size}x${size}.png`);

    await sharp(svgBuffer)
      .resize(size, size)
      .png()
      .toFile(outputPath);

    console.log(`  ✓ Generated icon-${size}x${size}.png`);
  }

  // Generate favicon.ico (multi-resolution ICO)
  console.log('\nGenerating favicon...');

  const faviconSizes = [16, 32, 48];
  const pngBuffers = await Promise.all(
    faviconSizes.map(async (size) => {
      return await sharp(svgBuffer)
        .resize(size, size)
        .png()
        .toBuffer();
    })
  );

  // Create ICO file format
  const iconDir = Buffer.alloc(6);
  iconDir.writeUInt16LE(0, 0); // Reserved
  iconDir.writeUInt16LE(1, 2); // Image type: 1 = ICO
  iconDir.writeUInt16LE(pngBuffers.length, 4); // Number of images

  // Calculate offsets
  const headerSize = 6 + pngBuffers.length * 16;
  let offset = headerSize;

  const iconEntries = [];
  const imageData = [];

  for (let i = 0; i < pngBuffers.length; i++) {
    const size = faviconSizes[i];
    const buffer = pngBuffers[i];

    const entry = Buffer.alloc(16);
    entry.writeUInt8(size > 255 ? 0 : size, 0); // Width (0 = 256)
    entry.writeUInt8(size > 255 ? 0 : size, 1); // Height (0 = 256)
    entry.writeUInt8(0, 2); // Color palette
    entry.writeUInt8(0, 3); // Reserved
    entry.writeUInt16LE(1, 4); // Color planes
    entry.writeUInt16LE(32, 6); // Bits per pixel
    entry.writeUInt32LE(buffer.length, 8); // Image data size
    entry.writeUInt32LE(offset, 12); // Offset to image data

    iconEntries.push(entry);
    imageData.push(buffer);
    offset += buffer.length;
  }

  // Combine all buffers
  const icoBuffer = Buffer.concat([iconDir, ...iconEntries, ...imageData]);

  // Write ICO file
  const icoPath = join(PUBLIC_DIR, 'favicon.ico');
  writeFileSync(icoPath, icoBuffer);
  console.log('  ✓ Generated favicon.ico (16, 32, 48)');

  // Also generate PNG favicon as fallback
  const pngPath = join(PUBLIC_DIR, 'favicon.png');
  await sharp(svgBuffer)
    .resize(32, 32)
    .png()
    .toFile(pngPath);
  console.log('  ✓ Generated favicon.png (32x32)');

  console.log('\n✅ All icons generated successfully!');
}

generateIcons().catch((err) => {
  console.error('Error generating icons:', err);
  process.exit(1);
});