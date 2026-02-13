#!/bin/bash
# VirtualBrowser Chromium Build Script
# This script builds a fingerprint-modified Chromium browser

set -e

# Configuration
CHROMIUM_VERSION="${CHROMIUM_VERSION:-139.0.7258.154}"
BUILD_TYPE="${BUILD_TYPE:-Release}"
JOBS="${JOBS:-$(nproc)}"
OUTPUT_DIR="${OUTPUT_DIR:-/out}"

echo "========================================"
echo "VirtualBrowser Chromium Builder"
echo "========================================"
echo "Chromium Version: $CHROMIUM_VERSION"
echo "Build Type: $BUILD_TYPE"
echo "Jobs: $JOBS"
echo "Output: $OUTPUT_DIR"
echo "========================================"

# Step 1: Fetch Chromium source
echo "[1/6] Fetching Chromium source..."
if [ ! -d "chromium" ]; then
    mkdir chromium && cd chromium
    fetch chromium
    cd src
else
    cd chromium/src
fi

# Step 2: Checkout specific version
echo "[2/6] Checking out version $CHROMIUM_VERSION..."
git checkout tags/$CHROMIUM_VERSION || git checkout $CHROMIUM_VERSION
gclient sync -D

# Step 3: Download Ungoogled Chromium patches
echo "[3/6] Downloading Ungoogled Chromium patches..."
if [ ! -d "ungoogled-chromium" ]; then
    git clone --depth=1 https://github.com/ungoogled-software/ungoogled-chromium.git
fi

# Step 4: Apply Ungoogled patches
echo "[4/6] Applying Ungoogled Chromium patches..."
for patch in ungoogled-chromium/patches/*.patch; do
    echo "Applying: $patch"
    patch -p1 < "$patch" || echo "Warning: Patch $patch may have failed"
done

# Step 5: Apply VirtualBrowser fingerprint patches
echo "[5/6] Applying VirtualBrowser fingerprint patches..."
for patch in /home/builder/patches/*.patch; do
    echo "Applying: $patch"
    patch -p1 < "$patch" || echo "Warning: Patch $patch may have failed"
done

# Step 6: Configure and build
echo "[6/6] Configuring and building..."

# Generate build configuration
cat > out/Default/args.gn << EOF
is_debug = false
is_component_build = false
symbol_level = 0
enable_nacl = false
chrome_pgo_phase = 0
treat_warnings_as_errors = false
fatal_linker_warnings = false
use_lld = true
is_cfi = false
enable_linux_installer = true
EOF

gn gen out/Default

# Build Chromium
echo "Starting build with $JOBS parallel jobs..."
autoninja -C out/Default chrome

# Copy output
echo "Copying build artifacts to $OUTPUT_DIR..."
mkdir -p $OUTPUT_DIR
cp -r out/Default/chrome $OUTPUT_DIR/
cp -r out/Default/*.so $OUTPUT_DIR/ 2>/dev/null || true
cp -r out/Default/resources $OUTPUT_DIR/ 2>/dev/null || true
cp -r out/Default/locales $OUTPUT_DIR/ 2>/dev/null || true

# Create installer package (Linux)
if [ -f "out/Default/chrome" ]; then
    echo "Creating installer package..."
    mkdir -p $OUTPUT_DIR/virtualbrowser-linux
    cp -r out/Default/* $OUTPUT_DIR/virtualbrowser-linux/
    cd $OUTPUT_DIR
    tar -czvf virtualbrowser-linux-$CHROMIUM_VERSION.tar.gz virtualbrowser-linux
    rm -rf virtualbrowser-linux
fi

echo "========================================"
echo "Build complete!"
echo "Output files in: $OUTPUT_DIR"
echo "========================================"
