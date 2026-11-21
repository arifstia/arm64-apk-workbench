# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] — menuju 1.1.0

### Added
- **Audit caching**: hasil audit disimpan per SHA-256 APK + mode + versi skema di `analysis/.cache/`
- Opsi `--no-cache` untuk memaksa analisis penuh
- Report JSON/Markdown menandai `cache.hit` dan asal timestamp saat hasil diambil dari cache
- `scripts/apk_cache.py` + 8 unit test khusus cache

### Measured
- Deep audit `input/test.apk`: **62 s → 0,58 s** pada cache hit (~106× lebih cepat)
- Fast audit `input/mini2.apk`: **1,20 s → 0,22 s** pada cache hit

---

## [1.0.1] - 2026-11-21

### Added
- GitHub Actions smoke test (`.github/workflows/smoke.yml`) with portable unit tests (`tests/test_smoke.py`)
- Issue templates (bug report, feature request) and issue configuration
- Bilingual README (Indonesian + English in one file) with real output examples and one-line install
- Social preview banner (`docs/assets/social-preview.png` + SVG source)
- Promotional articles in Indonesian and English, plus ready-to-paste awesome-list entries
- GitHub repository topics, description, homepage and issue tracking enabled

### Fixed
- **Portability:** both CLI entry points had a hard-coded `/root/projects/apk-workbench` path;
  they now resolve the workspace relative to `__file__` and work after cloning anywhere

---

## [1.0.0] - 2026-11-21

### Added
- Initial release of ARM64 APK Workbench
- `apk-workbench doctor` - System and toolchain health check
- `apk-workbench tools` - List installed tools with versions
- `apk-workbench audit` - Comprehensive APK analysis (manifest, DEX, native libs, resources, certificates)
- `apk-workbench decode` - Decode APK resources and Smali using APKTool
- `apk-workbench analyze` - Alias for audit command
- `apk-workbench backup` - Create timestamped backup of APK
- `apk-workbench build` - Build APK from decoded source
- `apk-workbench verify` - Verify APK signature and certificates
- Python virtual environment with Androguard for deep APK analysis
- Test keystore generation for development signing
- Performance modes: FAST, NORMAL, DEEP (planned)
- ARM64 optimized for Ubuntu 26.04 and Termux proot-distro
- OpenCode AI integration via AGENTS.md
- Professional documentation (README.md, WORKFLOW.md, TOOLCHAIN.md, SECURITY.md)
- Indonesian documentation (docs/ID.md)
- Installer (install.sh) and uninstaller (uninstall.sh)

### Fixed
- Import issues in CLI scripts
- Zipalign version detection
- Androguard DEX analysis compatibility
- APKTool 2.7.0 could not decode modern ARSC (targetSdk 37); upgraded to project-local APKTool 3.0.3 (official JAR, SHA-256 verified)
- ARM64 SIGILL from APKTool's bundled x86_64 aapt2; added native aapt2 compatibility wrapper with project-local framework
- Deep audit JADX exit 3 with partial output now reported as `partial` instead of `failed`
- Full targetSdk 37 APK rebuild now works: native ARM64 aapt2 from ADT build-tools,
  Android API 36 framework, and automatic renaming of aapt2-incompatible `$` resources

### Changed
- Performance modes FAST/NORMAL/DEEP are fully implemented (previously planned)
- `doctor`/`tools` now report the project-local APKTool 3.0.3 version

### Security
- Test-only signing keys (no production keys included)
- Workspace isolation (original APKs never modified)
- Audit logging for all operations

---

## Upcoming

### [1.1.0] - In progress
- ~~Performance optimization with caching~~ — done in Unreleased
- Improved error handling and recovery
- Enhanced analysis reports
- Patch management system (apply/rollback)
- ~~Fast mode for quick audits~~ — shipped in 1.0.0
- ~~Deep mode for comprehensive analysis~~ — shipped in 1.0.0

### [1.2.0] - Planned
- Advanced project analysis
- Improved patch management
- Additional automation workflows

### [2.0.0] - Planned
- Modular architecture
- Expanded Linux ARM64 support
- More AI-assisted workflows