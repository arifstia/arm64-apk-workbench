#!/bin/bash
# install.sh - ARM64 APK Workbench Installer
# Created and maintained by arifstia
# https://github.com/arifstia/arm64-apk-workbench

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

WORKSPACE="/root/projects/apk-workbench"
LOGFILE="${WORKSPACE}/logs/install_$(date +%Y%m%d_%H%M%S).log"

# Logging functions
log() { echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOGFILE"; }
success() { echo -e "${GREEN}[✓]${NC} $*" | tee -a "$LOGFILE"; }
warning() { echo -e "${YELLOW}[!]${NC} $*" | tee -a "$LOGFILE"; }
error() { echo -e "${RED}[✗]${NC} $*" | tee -a "$LOGFILE"; }

mkdir -p "${WORKSPACE}/logs"

echo "========================================"
echo "  ARM64 APK Workbench Installer"
echo "  Created by arifstia"
echo "========================================"
log "Starting installation..."

# Check if running as root (not recommended but allowed)
if [[ $EUID -eq 0 ]]; then
    warning "Running as root. This is not recommended for production use."
fi

# 1. Detect OS and Architecture
log "Checking system requirements..."

ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" ]]; then
    error "This toolkit requires ARM64 (aarch64) architecture. Detected: $ARCH"
    exit 1
fi
success "Architecture: $ARCH (ARM64 ✓)"

if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    log "OS: $PRETTY_NAME"
    if [[ "$ID" != "ubuntu" ]]; then
        warning "This toolkit is optimized for Ubuntu. Current: $ID"
    fi
else
    warning "Could not detect OS distribution"
fi

# 2. Check Java
log "Checking Java..."
if command -v java &> /dev/null; then
    JAVA_VERSION=$(java -version 2>&1 | head -n1)
    success "Java found: $JAVA_VERSION"
else
    error "Java not found. Installing OpenJDK..."
    apt-get update && apt-get install -y openjdk-21-jdk-headless
    success "OpenJDK installed"
fi

# 3. Check Python
log "Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    success "Python found: $PYTHON_VERSION"
else
    error "Python3 not found. Installing..."
    apt-get update && apt-get install -y python3 python3-venv python3-pip
    success "Python installed"
fi

# 4. Check Node.js
log "Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    success "Node.js found: $NODE_VERSION"
else
    warning "Node.js not found. Installing..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
    success "Node.js installed"
fi

# 5. Check OpenCode
log "Checking OpenCode..."
if command -v opencode &> /dev/null; then
    OPENCODE_VERSION=$(opencode --version 2>&1)
    success "OpenCode found: $OPENCODE_VERSION"
else
    warning "OpenCode not found. Please install manually: https://opencode.ai"
fi

# 6. Check RAM and Storage
log "Checking system resources..."
TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
AVAILABLE_RAM=$(free -g | awk '/^Mem:/{print $7}')
DISK_AVAILABLE=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')

log "Total RAM: ${TOTAL_RAM}GB, Available: ${AVAILABLE_RAM}GB"
log "Available disk space: ${DISK_AVAILABLE}GB"

if [[ $TOTAL_RAM -lt 4 ]]; then
    warning "Low RAM detected (${TOTAL_RAM}GB). Minimum 4GB recommended."
fi

if [[ $DISK_AVAILABLE -lt 10 ]]; then
    warning "Low disk space (${DISK_AVAILABLE}GB). Minimum 10GB recommended."
fi

# 7. Install Android tools
log "Installing Android SDK tools..."

# Install APKTool 3.x (project-local, verified JAR from official release)
# APKTool 2.7 fails on modern ARSC (targetSdk 35+), so we bundle 3.x locally
APKTOOL_VERSION="3.0.3"
APKTOOL_SHA256="dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423"
APKTOOL_JAR="${WORKSPACE}/tools/apktool/apktool_${APKTOOL_VERSION}.jar"
APKTOOL_WRAPPER="${WORKSPACE}/tools/bin/apktool"

if [[ ! -f "$APKTOOL_JAR" ]]; then
    log "Downloading APKTool ${APKTOOL_VERSION} from official GitHub release..."
    mkdir -p "${WORKSPACE}/tools/apktool" "${WORKSPACE}/tools/bin"
    APKTOOL_URL="https://github.com/iBotPeaches/Apktool/releases/download/v${APKTOOL_VERSION}/apktool_${APKTOOL_VERSION}.jar"
    if ! curl -fL --retry 3 -o "$APKTOOL_JAR" "$APKTOOL_URL"; then
        error "Failed to download APKTool. Check network connection."
        exit 1
    fi
    log "Verifying SHA-256..."
    echo "${APKTOOL_SHA256}  ${APKTOOL_JAR}" | sha256sum -c -
    if [[ $? -ne 0 ]]; then
        error "APKTool checksum mismatch! Removing downloaded file."
        rm -f "$APKTOOL_JAR"
        exit 1
    fi
    success "APKTool ${APKTOOL_VERSION} downloaded and verified"
else
    success "APKTool ${APKTOOL_VERSION} already present"
fi

# Create project-local wrapper (Java JAR is architecture-agnostic, safe on ARM64)
mkdir -p "${WORKSPACE}/tools/bin"
cat > "$APKTOOL_WRAPPER" <<'APKTOOL_EOF'
#!/bin/bash
# APKTool 3.x wrapper - project-local, verified JAR
JAR="$(cd "$(dirname "$0")/.." && pwd)/apktool/apktool_3.0.3.jar"
exec java -Xmx1024m -Dfile.encoding=utf-8 -jar "$JAR" "$@"
APKTOOL_EOF
chmod +x "$APKTOOL_WRAPPER"
success "APKTool wrapper ready: ${APKTOOL_WRAPPER}"

# Download native ARM64 aapt2 from ADT build-tools (supports modern ARSC + flags)
AAPT2_ARM64="${WORKSPACE}/tools/bin/aapt2-arm64"
AAPT2_ARM64_SHA256="c10af9c9e92b60f9662bb16cb7ce2687d9dd01c07d441d445ae68b06d76159a2"
if [[ ! -x "$AAPT2_ARM64" ]]; then
    log "Downloading native ARM64 aapt2 (ADT build-tools 37.0.0)..."
    AAPT2_URL="https://github.com/soobujmiah/adt/releases/download/v37.0.0/build-tools-37.0.0-linux-arm64.tar.gz"
    if curl -fL --retry 3 -o /tmp/adt-build-tools.tar.gz "$AAPT2_URL"; then
        rm -rf /tmp/adt-bt-extract && mkdir -p /tmp/adt-bt-extract
        tar -xzf /tmp/adt-build-tools.tar.gz -C /tmp/adt-bt-extract
        cp /tmp/adt-bt-extract/build-tools/aapt2 "$AAPT2_ARM64"
        chmod +x "$AAPT2_ARM64"
        echo "${AAPT2_ARM64_SHA256}  ${AAPT2_ARM64}" | sha256sum -c -
        if [[ $? -ne 0 ]]; then
            error "aapt2 ARM64 checksum mismatch!"
            rm -f "$AAPT2_ARM64"
        else
            success "Native ARM64 aapt2 installed and verified"
        fi
        rm -rf /tmp/adt-bt-extract /tmp/adt-build-tools.tar.gz
    else
        warning "Could not download ARM64 aapt2; will use distro aapt2 fallback"
    fi
else
    success "Native ARM64 aapt2 already present"
fi

# Create aapt2 launcher: prefer native ARM64, fall back to filtered distro aapt2
AAPT2_WRAPPER="${WORKSPACE}/tools/bin/aapt2"
cat > "$AAPT2_WRAPPER" <<'AAPT2_EOF'
#!/bin/bash
# aapt2 launcher — native ARM64 first, distro fallback
# Created and maintained by arifstia, Copyright (c) 2026 arifstia
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ARM64_BIN="${HERE}/aapt2-arm64"
if [[ -x "$ARM64_BIN" ]]; then
    exec "$ARM64_BIN" "$@"
fi
REAL_AAPT2="$(readlink -f /usr/bin/aapt2)"
SDK_PLATFORMS="/usr/lib/android-sdk/platforms"
args=(); is_link=0; has_include=0; target_sdk=""
for arg in "$@"; do
    case "$arg" in
        --no-compile-sdk-metadata) ;;
        link) is_link=1; args+=("$arg") ;;
        -I) has_include=1; args+=("$arg") ;;
        --target-sdk-version) args+=("$arg"); target_sdk="__NEXT__" ;;
        *) if [[ "$target_sdk" == "__NEXT__" ]]; then target_sdk="$arg"; fi; args+=("$arg") ;;
    esac
done
if [[ $is_link -eq 1 && $has_include -eq 0 ]]; then
    jar="${SDK_PLATFORMS}/android-23/android.jar"
    if [[ -n "$target_sdk" && "$target_sdk" != "__NEXT__" ]]; then
        candidate="${SDK_PLATFORMS}/android-${target_sdk}/android.jar"
        [[ -f "$candidate" ]] && jar="$candidate"
    fi
    if [[ -f "$jar" ]]; then
        out=(); inserted=0
        for arg in "${args[@]}"; do
            out+=("$arg")
            if [[ $inserted -eq 0 && "$arg" == "link" ]]; then out+=("-I" "$jar"); inserted=1; fi
        done
        args=("${out[@]}")
    fi
fi
exec "$REAL_AAPT2" "${args[@]}"
AAPT2_EOF
chmod +x "$AAPT2_WRAPPER"
success "aapt2 launcher ready: ${AAPT2_WRAPPER}"

# Note: system apktool (2.7) remains for compatibility but workbench uses 3.x

# Install apksigner, zipalign, aapt, aapt2
if ! command -v apksigner &> /dev/null; then
    log "Installing Android SDK Build Tools..."
    apt-get update && apt-get install -y android-sdk-build-tools
    success "Android SDK Build Tools installed"
else
    success "Android SDK Build Tools already installed"
fi

# Generate project-local APKTool framework. Prefer Android API 36 platform
# (needed for android:color/system_* resources used by targetSdk 35+ apps).
# Fall back to the newest locally installed android.jar if download fails.
FRAMEWORK_DIR="${WORKSPACE}/tools/apktool/framework"
if [[ ! -f "${FRAMEWORK_DIR}/1.apk" ]]; then
    mkdir -p "$FRAMEWORK_DIR" /tmp/apk-workbench-framework
    cd /tmp/apk-workbench-framework
    rm -f AndroidManifest.xml resources.arsc framework.apk

    PLATFORM_ZIP=""
    if curl -fL --retry 2 -o platform36.zip \
        https://dl.google.com/android/repository/platform-36_r01.zip; then
        PLATFORM_ZIP="platform36.zip"
    fi

    ANDROID_JAR=""
    if [[ -n "$PLATFORM_ZIP" ]]; then
        unzip -q -o "$PLATFORM_ZIP" android-36/android.jar && \
            ANDROID_JAR="android-36/android.jar"
    fi
    if [[ -z "$ANDROID_JAR" ]]; then
        ANDROID_JAR="$(find /usr/lib/android-sdk/platforms -maxdepth 2 -name android.jar 2>/dev/null | sort -V | tail -1)"
    fi

    if [[ -n "$ANDROID_JAR" ]]; then
        log "Generating APKTool framework from ${ANDROID_JAR}..."
        unzip -q -o "$ANDROID_JAR" AndroidManifest.xml resources.arsc
        zip -0 -q framework.apk AndroidManifest.xml resources.arsc
        "$APKTOOL_WRAPPER" if -p "$FRAMEWORK_DIR" framework.apk || \
            cp framework.apk "${FRAMEWORK_DIR}/1.apk"
        success "Project-local APKTool framework ready"
    else
        warning "No android.jar found; using APKTool default framework (build may fail)"
    fi
    cd "$WORKSPACE"
    rm -rf /tmp/apk-workbench-framework
else
    success "Project-local APKTool framework already present"
fi

# Install JADX
if ! command -v jadx &> /dev/null; then
    log "Installing JADX..."
    JADX_VERSION="1.5.6"
    JADX_URL="https://github.com/jadx-decompiler/jadx/releases/download/v${JADX_VERSION}/jadx-${JADX_VERSION}.zip"
    cd /tmp
    wget -q "$JADX_URL" -O jadx.zip
    unzip -q jadx.zip -d /opt/jadx-${JADX_VERSION}
    ln -sf /opt/jadx-${JADX_VERSION}/bin/jadx /usr/local/bin/jadx
    ln -sf /opt/jadx-${JADX_VERSION}/bin/jadx-gui /usr/local/bin/jadx-gui
    success "JADX ${JADX_VERSION} installed"
else
    success "JADX already installed"
fi

# Install smali/baksmali
if ! command -v smali &> /dev/null; then
    log "Installing smali/baksmali..."
    apt-get update && apt-get install -y smali
    success "smali/baksmali installed"
else
    success "smali/baksmali already installed"
fi

# 8. Setup Python virtual environment
log "Setting up Python virtual environment..."
if [[ ! -d "${WORKSPACE}/.venv" ]]; then
    python3 -m venv "${WORKSPACE}/.venv"
    success "Virtual environment created"
else
    success "Virtual environment already exists"
fi

# 9. Install Python dependencies
log "Installing Python dependencies..."
"${WORKSPACE}/.venv/bin/pip" install --upgrade pip
"${WORKSPACE}/.venv/bin/pip" install androguard==4.1.4
success "Python dependencies installed"

# 10. Create workspace directories
log "Creating workspace directories..."
DIRS=("input" "original" "backup" "decoded" "analysis" "patches" "build" "output" "logs" "scripts" "config" "reports" "tools" "docs" "examples" "tests")
for dir in "${DIRS[@]}"; do
    mkdir -p "${WORKSPACE}/${dir}"
done
success "Workspace directories created"

# 11. Generate test keystore
log "Generating test keystore..."
KEYSTORE_DIR="${WORKSPACE}/build/keys"
mkdir -p "$KEYSTORE_DIR"
if [[ ! -f "${KEYSTORE_DIR}/test_key.jks" ]]; then
    keytool -genkey -v \
        -keystore "${KEYSTORE_DIR}/test_key.jks" \
        -alias test_key \
        -keyalg RSA \
        -keysize 2048 \
        -validity 365 \
        -keypass testkey \
        -storepass testkey \
        -dname "CN=Test Key, OU=Test, O=Test, L=Test, S=Test, C=US" \
        2>/dev/null
    success "Test keystore generated"
else
    success "Test keystore already exists"
fi

# Copy to config as well
cp "${KEYSTORE_DIR}/test_key.jks" "${WORKSPACE}/config/test.keystore" 2>/dev/null || true

# 12. Make main executable
log "Setting up CLI executable..."
chmod +x "${WORKSPACE}/apk-workbench"

# 13. Verify installation
log "Verifying installation..."
if "${WORKSPACE}/apk-workbench" doctor > /dev/null 2>&1; then
    success "Installation verified successfully!"
else
    warning "Doctor check has some issues. Run 'apk-workbench doctor' for details."
fi

# Summary
echo ""
echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo ""
echo "Workspace: ${WORKSPACE}"
echo "CLI: apk-workbench (or ${WORKSPACE}/apk-workbench)"
echo ""
echo "Quick start:"
echo "  apk-workbench doctor"
echo "  apk-workbench audit <apk>"
echo "  apk-workbench decode <apk>"
echo "  apk-workbench build <decoded_dir>"
echo "  apk-workbench verify <apk>"
echo ""
echo "Documentation:"
echo "  README.md - English documentation"
echo "  docs/ID.md - Indonesian documentation"
echo ""
echo "Log file: ${LOGFILE}"
echo ""
success "ARM64 APK Workbench is ready to use!"