# VirtualBrowser Chromium Build Script for Windows
# PowerShell script to build fingerprint-modified Chromium

param(
    [string]$ChromiumVersion = "139.0.7258.154",
    [string]$BuildType = "Release",
    [int]$Jobs = 8,
    [string]$OutputDir = "C:\virtualbrowser-build\output"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================"
Write-Host "VirtualBrowser Chromium Builder (Windows)"
Write-Host "========================================"
Write-Host "Chromium Version: $ChromiumVersion"
Write-Host "Build Type: $BuildType"
Write-Host "Jobs: $Jobs"
Write-Host "Output: $OutputDir"
Write-Host "========================================"

# Check prerequisites
Write-Host "[0/7] Checking prerequisites..."

# Check Visual Studio
$vsWhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path $vsWhere)) {
    Write-Error "Visual Studio Installer not found. Please install Visual Studio 2022."
    exit 1
}

$vsPath = & $vsWhere -latest -property installationPath
Write-Host "Visual Studio: $vsPath"

# Check depot_tools
if (-not (Get-Command "gclient" -ErrorAction SilentlyContinue)) {
    Write-Error "depot_tools not found in PATH. Please install depot_tools."
    exit 1
}

# Check Python
$pythonVersion = python --version 2>&1
Write-Host "Python: $pythonVersion"

# Step 1: Create working directory
Write-Host "[1/7] Creating working directory..."
$workDir = "C:\virtualbrowser-build\chromium"
if (-not (Test-Path $workDir)) {
    New-Item -ItemType Directory -Path $workDir -Force | Out-Null
}
Set-Location $workDir

# Step 2: Fetch Chromium source
Write-Host "[2/7] Fetching Chromium source..."
if (-not (Test-Path "src")) {
    fetch chromium
}
Set-Location src

# Step 3: Checkout specific version
Write-Host "[3/7] Checking out version $ChromiumVersion..."
git checkout tags/$ChromiumVersion
gclient sync -D

# Step 4: Download Ungoogled Chromium patches
Write-Host "[4/7] Downloading Ungoogled Chromium patches..."
$ungoogledDir = "ungoogled-chromium"
if (-not (Test-Path $ungoogledDir)) {
    git clone --depth=1 https://github.com/ungoogled-software/ungoogled-chromium.git $ungoogledDir
}

# Step 5: Apply Ungoogled patches
Write-Host "[5/7] Applying Ungoogled Chromium patches..."
$patches = Get-ChildItem "$ungoogledDir\patches\*.patch"
foreach ($patch in $patches) {
    Write-Host "Applying: $($patch.Name)"
    git apply $patch.FullName 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: Patch $($patch.Name) may have failed"
    }
}

# Step 6: Apply VirtualBrowser fingerprint patches
Write-Host "[6/7] Applying VirtualBrowser fingerprint patches..."
$patchDir = "$PSScriptRoot\patches"
$vbPatches = Get-ChildItem "$patchDir\*.patch"
foreach ($patch in $vbPatches) {
    Write-Host "Applying: $($patch.Name)"
    git apply $patch.FullName 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: Patch $($patch.Name) may have failed"
    }
}

# Step 7: Configure and build
Write-Host "[7/7] Configuring and building..."

# Create output directory
if (-not (Test-Path "out\Default")) {
    New-Item -ItemType Directory -Path "out\Default" -Force | Out-Null
}

# Generate args.gn
$argsGn = @"
is_debug = false
is_component_build = false
symbol_level = 0
enable_nacl = false
chrome_pgo_phase = 0
treat_warnings_as_errors = false
fatal_linker_warnings = false
is_clang = true
use_lld = true
"@

Set-Content -Path "out\Default\args.gn" -Value $argsGn

# Generate build files
gn gen out/Default

# Build
Write-Host "Starting build with $Jobs parallel jobs..."
autoninja -C out/Default chrome -j $Jobs

# Copy output
Write-Host "Copying build artifacts to $OutputDir..."
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Copy-Item -Path "out\Default\chrome.exe" -Destination $OutputDir -Force
Copy-Item -Path "out\Default\*.dll" -Destination $OutputDir -Force -ErrorAction SilentlyContinue
Copy-Item -Path "out\Default\resources" -Destination $OutputDir -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item -Path "out\Default\locales" -Destination $OutputDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "========================================"
Write-Host "Build complete!"
Write-Host "Output files in: $OutputDir"
Write-Host "========================================"

# Create ZIP package
$zipFile = "$OutputDir\virtualbrowser-windows-$ChromiumVersion.zip"
Write-Host "Creating ZIP package: $zipFile"
Compress-Archive -Path "$OutputDir\*" -DestinationPath $zipFile -Force

Write-Host "Done!"
