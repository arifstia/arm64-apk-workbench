#!/bin/bash
# uninstall.sh - ARM64 APK Workbench Uninstaller
# Created and maintained by arifstia
# https://github.com/arifstia/arm64-apk-workbench

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

WORKSPACE="/root/projects/apk-workbench"

echo "========================================"
echo "  ARM64 APK Workbench Uninstaller"
echo "========================================"
echo ""
warning() { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*"; }
success() { echo -e "${GREEN}[✓]${NC} $*"; }
info() { echo -e "${BLUE}[i]${NC} $*"; }

# Confirm uninstall
echo "This will remove the ARM64 APK Workbench installation from:"
echo "  ${WORKSPACE}"
echo ""
echo "The following will be REMOVED:"
echo "  - Project scripts and configuration"
echo "  - Python virtual environment (.venv)"
echo "  - CLI executable (apk-workbench)"
echo "  - Generated reports and logs"
echo ""
echo "The following will be PRESERVED (require manual deletion):"
echo "  - System packages (Java, Python, Node.js, Android tools)"
echo "  - User APK files in input/, original/, backup/"
echo "  - Decoded APKs in decoded/"
echo "  - Built APKs in build/, output/"
echo ""
read -p "Are you sure you want to uninstall? (yes/no): " CONFIRM

if [[ "$CONFIRM" != "yes" ]]; then
    info "Uninstall cancelled."
    exit 0
fi

# Second confirmation for data removal
read -p "Also remove user data (input, backup, decoded, output)? This CANNOT be undone! (yes/no): " REMOVE_DATA

# Remove project files
info "Removing project files..."

PROJECT_FILES=(
    "apk-workbench"
    "install.sh"
    "uninstall.sh"
    "README.md"
    "LICENSE"
    "CHANGELOG.md"
    "CONTRIBUTING.md"
    "SECURITY.md"
    "CODE_OF_CONDUCT.md"
    "AGENTS.md"
    "TOOLCHAIN.md"
    "WORKFLOW.md"
    ".gitignore"
    ".gitattributes"
    "scripts"
    "config"
    "docs"
    "examples"
    "tests"
    ".venv"
    "logs"
    "reports"
    "tools"
    "analysis"
    "patches"
)

for item in "${PROJECT_FILES[@]}"; do
    if [[ -e "${WORKSPACE}/${item}" ]]; then
        rm -rf "${WORKSPACE}/${item}"
        success "Removed: ${item}"
    fi
done

# Remove user data if confirmed
if [[ "$REMOVE_DATA" == "yes" ]]; then
    warning "Removing user data..."
    DATA_DIRS=("input" "original" "backup" "decoded" "build" "output")
    for dir in "${DATA_DIRS[@]}"; do
        if [[ -d "${WORKSPACE}/${dir}" ]]; then
            rm -rf "${WORKSPACE}/${dir}"
            success "Removed data: ${dir}"
        fi
    done
else
    info "User data preserved in: input/, original/, backup/, decoded/, build/, output/"
fi

# Remove workspace directory if empty
if [[ -d "$WORKSPACE" ]] && [[ -z "$(ls -A "$WORKSPACE")" ]]; then
    rmdir "$WORKSPACE"
    success "Removed empty workspace directory"
fi

echo ""
echo "========================================"
echo "  Uninstall Complete"
echo "========================================"
echo ""
info "System packages (Java, Python, Node.js, Android tools) were NOT removed."
info "To remove them manually:"
echo "  apt-get remove --purge openjdk-* python3-venv python3-pip nodejs apktool android-sdk-build-tools smali"
echo ""
success "ARM64 APK Workbench has been uninstalled."