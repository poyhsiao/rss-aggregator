#!/usr/bin/env node
/**
 * Generate PWA icons from SVG source using sharp
 * 
 * Usage: pnpm generate-icons
 * 
 * This script reads the SVG icon from public/icons/icon.svg
 * and generates PNG icons for all sizes specified in manifest.json
 */

import sharp from 'sharp';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512];
const SVG_PATH = join(__dirname, '../public/icons/icon.svg');
const OUTPUT_DIR = join(__dirname, '../public/icons');

async function generateIcons() {
  // Check if SVG exists
  if (!existsSync(SVG_PATH)) {
    console.error('Error: icon.svg not found at', SVG_PATH);
    process.exit(1);
  }

  // Ensure output directory exists
  if (!existsSync(OUTPUT_DIR)) {
    mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  // Read SVG buffer
  const svgBuffer = readFileSync(SVG_PATH);

  console.log('Generating PWA icons...');

  // Generate each size
  for (const size of ICON_SIZES) {
    const outputPath = join(OUTPUT_DIR, `icon-${size}x${size}.png`);
    
    await sharp(svgBuffer)
      .resize(size, size)
      .png()
      .toFile(outputPath);
    
    console.log(`  ✓ Generated icon-${size}x${size}.png`);
  }

  // Generate favicon.ico (32x32)
  const faviconPath = join(__dirname, '../public/favicon.ico');
  await sharp(svgBuffer)
    .resize(32, 32)
    .png()
    .toFile(faviconPath.replace('.ico', '.png'));
  
  console.log('  ✓ Generated favicon.png');
  console.log('\nAll icons generated successfully!');
}

generateIcons().catch((err) => {
  console.error('Error generating icons:', err);
  process.exit(1);
});