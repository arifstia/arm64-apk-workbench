# APK Workbench

**Android APK Modification Workbench** — Automated CLI tooling for APK analysis, decoding, building, and verification on Ubuntu 26.04 ARM64 (Termux proot-distro).

## Quick Start

```bash
# Check system health
apk-workbench doctor

# Audit an APK
apk-workbench audit /path/to/app.apk

# Decode resources and Smali
apk-workbench decode /path/to/app.apk -o /path/to/output

# Backup original APK
apk-workbench backup /path/to/app.apk

# Build from decoded source
apk-workbench build /path/to/decoded -o output.apk

# Verify APK signature
apk-workbench verify /path/to/app.apk
```

## Workspace Structure

```
apk-workbench/
├── input/       # Original APKs (read-only)
├── original/    # Original APK copies
├── backup/      # Timestamped backups
├── decoded/     # Decoded resources and Smali
├── analysis/    # Audit reports (JSON + Markdown)
├── patches/     # Modification patches
├── build/       # Rebuilt APKs
├── output/      # Final outputs
├── logs/        # Execution logs
├── scripts/     # Engine scripts (Python)
├── config/      # Configuration files
├── reports/     # Final reports
├── tools/       # Tool binaries
└── .venv/       # Python virtual environment
```

## Tools

| Tool | Version | Purpose |
|------|---------|---------|
| JADX | 1.5.6 | DEX decompiler (GUI/CLI) |
| APKTool | 3.0.3 (project-local) | APK resource decoding/building (supports targetSdk 37) |
| apksigner | 0.9 | APK signing/verification |
| zipalign | 4 | ZIP alignment |
| aapt/aapt2 | 14 | Android asset packaging |
| smali/baksmali | 2.5.2 | DEX assembly/disassembly |
| Androguard | 4.1.4 | APK analysis library |

## Security

This toolset is for **authorized use only** — analyzing and modifying APKs you own or have permission to modify. See [SECURITY.md](SECURITY.md).

## License

MIT License — See [LICENSE](LICENSE)