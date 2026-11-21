# TOOLCHAIN.md

## Installed Tools Reference

| Category | Tool | Version | Path | Status |
|----------|------|---------|------|--------|
| **DEX Decompiler** | JADX | 1.5.6 | /root/opt/jadx-1.5.6 | ✅ Working |
| **APK Builder** | APKTool (project-local) | 3.0.3 | tools/bin/apktool → tools/apktool/apktool_3.0.3.jar | ✅ Working |
| **APK Builder (system)** | APKTool | 2.7.0-dirty | /usr/bin/apktool | ⚠️ Limited (targetSdk 35+) |
| **Signing** | apksigner | 0.9 | /usr/bin/apksigner | ✅ Working |
| **Alignment** | zipalign | 1:10.0.0+r36-1.1build1 | /usr/bin/zipalign | ✅ Working |
| **Asset Packaging** | aapt | 1:14~beta1-5 | /usr/bin/aapt | ✅ Working |
| **Asset Packaging2** | aapt2 |  | /usr/bin/aapt2 | ✅ Working |
| **Smali Assembler** | smali | 2.5.2.git2771eae-debian | /root/.local/bin/smali | ✅ Working |
| **Baksmali** | baksmali | 2.5.2.git2771eae-debian | /root/.local/bin/baksmali | ✅ Working |
| **APK Analysis** | Androguard | 4.1.4 | /root/projects/apk-workbench/.venv/bin/androguard | ✅ Working |

## Tool Details

### JADX
- **Download**: https://github.com/jadx-decompiler/jadx/releases/tag/v1.5.6
- **Purpose**: DEX to source code (Java/Kotlin) decompilation
- **CLI**: `jadx <apk_path>` → outputs HTML/smali
- **Note**: GUI available but CLI works fine on ARM64

### APKTool 3.0.3 (project-local, preferred)
- **Download**: https://github.com/iBotPeaches/Apktool/releases/download/v3.0.3/apktool_3.0.3.jar
- **SHA-256**: `dbf930b076c6b9be08d57c449cacefc3bdd6b71ebd59b3066fc0e1f5b14f9423`
- **Wrapper**: `tools/bin/apktool` (java -Xmx1024m, UTF-8)
- **Purpose**: Resource decoding/encoding, Smali management
- **CLI**: `tools/bin/apktool d <apk> -o <dir>` / `tools/bin/apktool b --aapt tools/bin/aapt2 -p tools/apktool/framework <dir> -o <apk>`
- **Why 3.0.3**: System APKTool 2.7.0 fails on modern ARSC (`targetSdkVersion: 37`) with
  `Could not decode arsc file — Expected: 0x00000008, got: 0x0000005c`. 3.0.3 decodes it correctly.
- **ARM64 note**: APKTool's bundled `prebuilt/linux/aapt2` is x86_64 (SIGILL on ARM64).
  Always pass `--aapt tools/bin/aapt2`, which prefers native ARM64 aapt2 from ADT
  build-tools 37.0.0 (SHA-256 `c10af9c9e92b60f9662bb16cb7ce2687d9dd01c07d441d445ae68b06d76159a2`),
  with a filtered distro-aapt2 fallback.
- **Framework**: `tools/apktool/framework/1.apk` is generated from Android API 36
  platform by `install.sh` (needed for `android:color/system_*` resources used by
  targetSdk 35+ apps); the global `~/.local/share/apktool/framework/1.apk` can be
  stale/corrupt on ARM64 systems.
- **$-resource fix**: the CLI automatically renames Material Components resources
  beginning with `$` (rejected by aapt2) and records the change in `patches/`.
- **Note**: Takes ~14 minutes for 12MB APK on ARM64 (historical measurement). Full
  decode→build→sign→verify of a targetSdk 37 / 12 MB APK is now verified (~30 s build).

### apksigner
- **Part of**: Android SDK Build Tools
- **Purpose**: APK signing and verification
- **CLI**: `apksigner sign ...` / `apksigner verify ...`

### zipalign
- **Part of**: Android SDK Build Tools
- **Purpose**: ZIP alignment for optimal runtime performance
- **CLI**: `zipalign -v 4 <in.apk> <out.apk>`

### aapt/aapt2
- **Part of**: Android SDK Build Tools
- **Purpose**: Android asset packaging and badging
- **CLI**: `aapt dump badging <apk>`

### smali/baksmali
- **Download**: https://github.com/JesusFreke/smali/releases/tag/v3.0.10
- **Purpose**: DEX ⇄ Smali assembly/disassembly
- **CLI**: `smali <dex_dir> <out.jar>` / `baksmali <jar> <out_dir>`
- **Note**: Debian 2.5.2 wrapper works via Java JAR

### Androguard
- **Install**: `python3 -m pip install androguard` in `.venv`
- **Purpose**: Full APK analysis (manifest, DEX, native libs, permissions)
- **CLI**: Via Python API or `androguard` command
- **Note**: Use virtual environment at `./.venv`

## Python Dependencies (.venv)

```
androguard==4.1.4
```

Install with:
```bash
python3 -m venv /root/projects/apk-workbench/.venv
/root/projects/apk-workbench/.venv/bin/pip install androguard
```

## Environment Requirements

- **OS**: Ubuntu 26.04 (Resolute Raccoon) ARM64
- **Architecture**: aarch64 / ARM64 (critical - x86_64 binaries will not run)
- **RAM**: Minimum 4 GB available (~3.3 GB free typically)
- **Storage**: ~63 GB available
- **Java**: OpenJDK 25.0.5 (arm64)
- **Python**: 3.14.4
- **Node.js**: 24.22.1

## Workspace Paths

| Directory | Purpose |
|-----------|---------|
| `input/` | Read-only original APKs |
| `original/` | Original APK copies (never modify) |
| `backup/` | Timestamped backups |
| `decoded/` | Decoded resources/Smali (modify here) |
| `analysis/` | Audit reports |
| `patches/` | Modification patches |
| `build/` | Rebuilt APKs |
| `output/` | Final signed/aligned APKs |
| `logs/` | Execution logs |
| `scripts/` | Python engine scripts |
| `config/` | Configuration files |
| `reports/` | Final reports |
| `tools/` | Tool binaries |
| `.venv/` | Python virtual environment |

## Build Pipeline Flow

```
APK (input/)
    │
    ├── apk-tool d → decoded/ (resource + smali)
    │                       │
    │                       ├── modify files here
    │                       └── patches/ records changes
    │                       │
    └── ap-tool b → build/ (unsigned APK)
                        │
                        ├── zipalign → aligned APK
                        └── apksigner sign → output/ (signed APK)
```

## Known Tool Availability Notes

- **smali 3.0.10 JAR**: Not found at expected location; Debian 2.5.2 works via wrapper
- **apktool decode timing**: ~14 min for 12MB APK on ARM64 (expected performance characteristic)
- **Androguard**: Virtual environment required at `.venv`
- **Java**: ARM64 OpenJDK (25.0.5) active; x86_64 JDK will fail if used

## Alternative Tools (if primary unavailable)

| Primary | Alternative | Note |
|---------|-----------|------|
| JADX | apktool --no-res + d option | Slower but works |
| APKTool | Manual XML/Smali editing | Educational only |
| Androguard | aapt dump + custom Python | Subset of features |