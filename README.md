# ARM64 APK Workbench

**Workbench Modifikasi APK Android / Android APK Modification Workbench** — alat CLI otomatis untuk **audit, decode, build, sign, dan verifikasi APK** pada **Ubuntu 26.04 ARM64** dan **Termux proot-distro**.

Dibuat dan dipelihara oleh **arifstia** — https://github.com/arifstia

[![Release](https://img.shields.io/badge/release-v1.0.0-22c55e?style=flat-square)](https://github.com/arifstia/arm64-apk-workbench/releases/tag/v1.0.0)
[![Platform](https://img.shields.io/badge/platform-Linux%20ARM64-5bd8f5?style=flat-square)](https://github.com/arifstia/arm64-apk-workbench)
[![License](https://img.shields.io/badge/license-MIT-a69bff?style=flat-square)](LICENSE)

> **Pilih bahasa / Choose language:** [🇮🇩 Bahasa Indonesia](#bahasa-indonesia) · [🇬🇧 English](#english) · [📖 Panduan lengkap ID](docs/ID.md)

---

<a name="bahasa-indonesia"></a>

## 🇮🇩 Bahasa Indonesia

### Fitur

| Fitur | Deskripsi |
|-------|-----------|
| **Audit APK** | Analisis manifest, permission, DEX, native library, resource, dan sertifikat |
| **Mode performa** | `fast`, `normal`, `deep` — sesuai kebutuhan (deep menyertakan dekompilasi JADX) |
| **Decode APK** | Ekstrak resource dan Smali dengan APKTool 3.0.3 (mendukung targetSdk 37) |
| **Build APK** | Build ulang dari source hasil decode → zipalign → tanda tangan → verifikasi |
| **Sign & Verify** | Signing dengan test key dan verifikasi v1/v2/v3 via apksigner |
| **Backup otomatis** | Salinan APK dengan timestamp sebelum modifikasi |
| **Patch record** | Catatan perubahan tersimpan di `patches/` |
| **Ramah ARM64** | RAM rendah, pemrosesan berurutan, tanpa binary x86_64 |
| **Aman** | APK asli tidak pernah ditimpa, backup tidak dihapus, tidak install APK otomatis |

### Persyaratan

- **Arsitektur:** ARM64 (`aarch64`)
- **Sistem:** Ubuntu 26.04 LTS atau Termux proot-distro
- **Python:** 3.14+ (dengan virtual environment)
- **Java:** OpenJDK 21+ (untuk APKTool & JADX)
- **RAM:** minimal 4 GB (disarankan 8 GB untuk APK besar)
- **Disk:** minimal 10 GB kosong

### Instalasi

```bash
git clone https://github.com/arifstia/arm64-apk-workbench.git
cd arm64-apk-workbench
chmod +x install.sh
./install.sh
```

Installer akan:
1. Memverifikasi arsitektur ARM64 dan tool sistem
2. Mengunduh **APKTool 3.0.3** dari rilis resmi + verifikasi SHA-256
3. Mengunduh **aapt2 ARM64 native** (ADT build-tools 37.0.0) + verifikasi SHA-256
4. Membuat wrapper `tools/bin/apktool` dan `tools/bin/aapt2`
5. Membangkitkan framework APKTool dari Android API 36
6. Menyiapkan virtual environment Python dan test keystore

Verifikasi instalasi:

```bash
./apk-workbench doctor
./apk-workbench tools
```

### Mulai Cepat

```bash
# 1. Cek kesehatan sistem
apk-workbench doctor

# 2. Audit APK (mode normal)
apk-workbench audit input/app.apk

# 3. Audit cepat / mendalam
apk-workbench audit input/app.apk --mode fast
apk-workbench audit input/app.apk --mode deep

# 4. Backup APK asli
apk-workbench backup input/app.apk

# 5. Decode resource + Smali
apk-workbench decode input/app.apk

# 6. Build ulang dari hasil decode
apk-workbench build -s decoded/decoded_app_TIMESTAMP

# 7. Verifikasi APK hasil build
apk-workbench verify output/signed_decoded_app_TIMESTAMP.apk
```

### Referensi Perintah

| Perintah | Fungsi | Contoh |
|----------|--------|--------|
| `--help` | Bantuan umum | `apk-workbench --help` |
| `--version` | Versi CLI | `apk-workbench --version` |
| `doctor` | Cek sistem & toolchain | `apk-workbench doctor` |
| `tools` | Daftar tool + versi | `apk-workbench tools` |
| `audit` | Analisis APK | `apk-workbench audit app.apk --mode normal` |
| `analyze` | Alias untuk `audit` | `apk-workbench analyze app.apk` |
| `decode` | Decode resource & Smali | `apk-workbench decode app.apk` |
| `backup` | Backup APK ber-timestamp | `apk-workbench backup app.apk` |
| `build` | Build + sign + verify | `apk-workbench build -s decoded/decoded_app_TIMESTAMP` |
| `verify` | Verifikasi tanda tangan | `apk-workbench verify output/app.apk` |
| `patch` | Rekam perubahan | `apk-workbench patch -s decoded/decoded_app_TIMESTAMP -o "deskripsi"` |

Opsi global:

```bash
--mode {fast,normal,deep}   # Mode audit (default: normal)
-s, --source DIR            # Direktori source untuk build/patch
-o, --output VALUE          # Output / deskripsi patch
-v, --verbose               # Output lebih detail
```

### Mode Audit

| Mode | Kapan dipakai | Keterangan |
|------|---------------|------------|
| `fast` | Smoke test / CI | Manifest, permission, library native |
| `normal` | Audit rutin | + resource dan jumlah file DEX |
| `deep` | Analisis mendalam | + dekompilasi JADX (±80 detik untuk APK 12 MB) |

### Struktur Workspace

```
arm64-apk-workbench/
├── input/          # APK asli (read-only)
├── original/       # Salinan APK asli
├── backup/         # Backup dengan timestamp
├── decoded/        # Resource & Smali hasil decode
├── analysis/       # Laporan audit (JSON + Markdown)
├── patches/        # Catatan modifikasi
├── build/          # APK antara & keystore test
├── output/         # APK final yang sudah ditandatangani
├── logs/           # Log eksekusi
├── scripts/        # Mesin CLI (Python)
├── config/         # Konfigurasi
├── reports/        # Laporan akhir (release & performa)
├── tools/          # Wrapper tool (binary diunduh installer)
├── docs/           # Dokumentasi bahasa Indonesia
└── .venv/          # Virtual environment Python
```

### Alur Kerja

```text
input/app.apk
   │
   ├─► backup/           (backup otomatis)
   │
   ├─► decode/           (resource + Smali)
   │        │
   │        ├─► edit file Smali/XML sesuai kebutuhan
   │        │
   │        └─► patch record dicatat di patches/
   │
   └─► analysis/         (laporan audit JSON + Markdown)

decoded/ → build/ → zipalign → apksigner → output/ → verify
```

> **Catatan:** APK asli di `input/` tidak pernah dimodifikasi. Selalu bekerja pada salinan di `decoded/`.

### Toolchain

| Tool | Versi | Fungsi |
|------|-------|--------|
| JADX | 1.5.6 | Dekompiler DEX → Java/Kotlin |
| APKTool | 3.0.3 (project-local) | Decode/build resource & Smali, targetSdk 37 |
| apksigner | 0.9 | Signing & verifikasi APK |
| zipalign | 10.0 | Alignment ZIP APK |
| aapt / aapt2 | 2.19 | Android asset packaging |
| smali / baksmali | 2.5.2 | Assembly/disassembly DEX |
| Androguard | 4.1.4 | Analisis APK berbasis Python |

**Catatan ARM64:**
- APKTool 2.7 bawaan sistem gagal decode ARSC modern (`targetSdkVersion: 37`). Workbench memakai **APKTool 3.0.3** terverifikasi.
- aapt2 bawaan APKTool 3.x adalah binary **x86_64** dan tidak jalan di ARM64. Workbench memakai **aapt2 ARM64 native**.
- Framework dibangkitkan dari **Android API 36** agar resource `android:color/system_*` (targetSdk 35+) tersedia.
- Resource Material Components diawali `$` otomatis direname sebelum build dan dicatat di `patches/`.

### Laporan

- [`reports/PERFORMANCE_REPORT.md`](reports/PERFORMANCE_REPORT.md) — hasil pengukuran nyata
- [`reports/GITHUB_RELEASE_AUDIT.md`](reports/GITHUB_RELEASE_AUDIT.md) — audit kesiapan rilis
- [`TOOLCHAIN.md`](TOOLCHAIN.md) · [`WORKFLOW.md`](WORKFLOW.md) · [`docs/ID.md`](docs/ID.md)

### Keamanan & Etika

Tool ini **hanya untuk penggunaan yang sah** — menganalisis atau memodifikasi APK yang Anda miliki atau memiliki izin untuk memodifikasinya. Workbench **tidak pernah** menimpa APK asli, menghapus backup, menginstall APK otomatis, menyertakan private key pihak ketiga, atau mengaktifkan fitur penyalahgunaan. Lihat [SECURITY.md](SECURITY.md).

### Lisensi

MIT License — lihat [LICENSE](LICENSE). Copyright (c) 2026 **arifstia**.

---

<a name="english"></a>

## 🇬🇧 English

### Features

| Feature | Description |
|---------|-------------|
| **APK Audit** | Manifest, permissions, DEX, native libraries, resources and certificates |
| **Performance modes** | `fast`, `normal`, `deep` (deep includes JADX decompilation) |
| **Decode APK** | Extract resources and Smali with APKTool 3.0.3 (targetSdk 37 support) |
| **Build APK** | Rebuild from decoded source → zipalign → sign → verify |
| **Sign & Verify** | Test-key signing and v1/v2/v3 verification via apksigner |
| **Automatic backup** | Timestamped copy before any modification |
| **Patch records** | Change records stored in `patches/` |
| **ARM64 friendly** | Low RAM, sequential processing, no x86_64 binaries |
| **Safe** | Originals are never overwritten, backups never deleted, no auto-install |

### Requirements

- **Architecture:** ARM64 (`aarch64`)
- **OS:** Ubuntu 26.04 LTS or Termux proot-distro
- **Python:** 3.14+ (with virtual environment)
- **Java:** OpenJDK 21+ (APKTool & JADX)
- **RAM:** 4 GB minimum (8 GB recommended for large APKs)
- **Disk:** 10 GB free space

Bundled tools: JADX 1.5.6, APKTool 3.0.3, apksigner, zipalign, aapt/aapt2, smali/baksmali 2.5.2, Androguard 4.1.4.

### Installation

```bash
git clone https://github.com/arifstia/arm64-apk-workbench.git
cd arm64-apk-workbench
chmod +x install.sh
./install.sh
```

The installer will:
1. Verify ARM64 architecture and system tools
2. Download **APKTool 3.0.3** from the official release + verify SHA-256
3. Download **native ARM64 aapt2** (ADT build-tools 37.0.0) + verify SHA-256
4. Create `tools/bin/apktool` and `tools/bin/aapt2` wrappers
5. Generate the APKTool framework from Android API 36
6. Set up the Python virtual environment and test keystore

Verify the installation:

```bash
./apk-workbench doctor
./apk-workbench tools
```

### Quick Start

```bash
# 1. System health check
apk-workbench doctor

# 2. Audit an APK (normal mode)
apk-workbench audit input/app.apk

# 3. Fast / deep audit
apk-workbench audit input/app.apk --mode fast
apk-workbench audit input/app.apk --mode deep

# 4. Back up the original APK
apk-workbench backup input/app.apk

# 5. Decode resources and Smali
apk-workbench decode input/app.apk

# 6. Rebuild from decoded source
apk-workbench build -s decoded/decoded_app_TIMESTAMP

# 7. Verify the built APK
apk-workbench verify output/signed_decoded_app_TIMESTAMP.apk
```

### Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `--help` | Show help | `apk-workbench --help` |
| `--version` | CLI version | `apk-workbench --version` |
| `doctor` | Check system & toolchain | `apk-workbench doctor` |
| `tools` | List tools + versions | `apk-workbench tools` |
| `audit` | Analyze APK | `apk-workbench audit app.apk --mode normal` |
| `analyze` | Alias for `audit` | `apk-workbench analyze app.apk` |
| `decode` | Decode resources & Smali | `apk-workbench decode app.apk` |
| `backup` | Timestamped backup | `apk-workbench backup app.apk` |
| `build` | Build + sign + verify | `apk-workbench build -s decoded/decoded_app_TIMESTAMP` |
| `verify` | Verify signature | `apk-workbench verify output/app.apk` |
| `patch` | Record changes | `apk-workbench patch -s decoded/decoded_app_TIMESTAMP -o "description"` |

Global options:

```bash
--mode {fast,normal,deep}   # Audit mode (default: normal)
-s, --source DIR            # Source directory for build/patch
-o, --output VALUE          # Output / patch description
-v, --verbose               # Verbose output
```

### Audit Modes

| Mode | When to use | Details |
|------|-------------|---------|
| `fast` | CI / smoke tests | Manifest, permissions, native libraries |
| `normal` | Routine audits | + resources and DEX file count |
| `deep` | In-depth analysis | + JADX decompilation (~80 s for a 12 MB APK) |

### Workspace Structure

```
arm64-apk-workbench/
├── input/          # Original APKs (read-only)
├── original/       # Copies of originals
├── backup/         # Timestamped backups
├── decoded/        # Decoded resources & Smali
├── analysis/       # Audit reports (JSON + Markdown)
├── patches/        # Modification records
├── build/          # Intermediate APKs & test keystore
├── output/         # Final signed APKs
├── logs/           # Execution logs
├── scripts/        # CLI engine (Python)
├── config/         # Configuration
├── reports/        # Final reports (release & performance)
├── tools/          # Tool wrappers (binaries downloaded by installer)
├── docs/           # Indonesian documentation
└── .venv/          # Python virtual environment
```

### Workflow

```text
input/app.apk
   │
   ├─► backup/           (automatic backup)
   │
   ├─► decode/           (resources + Smali)
   │        │
   │        ├─► edit Smali/XML as needed
   │        │
   │        └─► patch record written to patches/
   │
   └─► analysis/         (JSON + Markdown audit reports)

decoded/ → build/ → zipalign → apksigner → output/ → verify
```

> **Note:** APKs in `input/` are never modified. Always work on a copy in `decoded/`.

### Toolchain

| Tool | Version | Purpose |
|------|---------|---------|
| JADX | 1.5.6 | DEX → Java/Kotlin decompiler |
| APKTool | 3.0.3 (project-local) | Resource/Smali decode & build, targetSdk 37 |
| apksigner | 0.9 | APK signing & verification |
| zipalign | 10.0 | APK ZIP alignment |
| aapt / aapt2 | 2.19 | Android asset packaging |
| smali / baksmali | 2.5.2 | DEX assembly/disassembly |
| Androguard | 4.1.4 | Python-based APK analysis |

**ARM64 notes:**
- System APKTool 2.7 cannot decode modern ARSC (`targetSdkVersion: 37`); this project uses verified **APKTool 3.0.3**.
- APKTool 3.x ships an **x86_64** aapt2 that cannot run on ARM64; this project uses **native ARM64 aapt2**.
- The framework is generated from **Android API 36** so `android:color/system_*` resources (targetSdk 35+) resolve.
- Material Components resources starting with `$` are renamed before build and recorded in `patches/`.

### Reports

- [`reports/PERFORMANCE_REPORT.md`](reports/PERFORMANCE_REPORT.md) — measured timings
- [`reports/GITHUB_RELEASE_AUDIT.md`](reports/GITHUB_RELEASE_AUDIT.md) — release readiness audit
- [`TOOLCHAIN.md`](TOOLCHAIN.md) · [`WORKFLOW.md`](WORKFLOW.md) · [`docs/ID.md`](docs/ID.md)

### Security & Ethics

This toolset is for **authorized use only** — analyzing or modifying APKs you own or have permission to modify. It **never** overwrites originals, deletes backups, installs APKs automatically, ships third-party private keys, or enables abuse features. See [SECURITY.md](SECURITY.md).

### License

MIT License — see [LICENSE](LICENSE). Copyright (c) 2026 **arifstia**.
