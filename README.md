# ARM64 APK Workbench

**Workbench Modifikasi APK Android** — kumpulan perintah CLI otomatis untuk **audit, decode, build, sign, dan verifikasi APK** pada **Ubuntu 26.04 ARM64** maupun **Termux proot-distro**.

Dibuat dan dipelihara oleh **arifstia** — https://github.com/arifstia

[![Release](https://img.shields.io/badge/release-v1.0.0-22c55e?style=flat-square)](https://github.com/arifstia/arm64-apk-workbench/releases/tag/v1.0.0)
[![Platform](https://img.shields.io/badge/platform-Linux%20ARM64-5bd8f5?style=flat-square)](https://github.com/arifstia/arm64-apk-workbench)
[![License](https://img.shields.io/badge/license-MIT-a69bff?style=flat-square)](LICENSE)

> **Bahasa:** [English](README.en.md) | **Bahasa Indonesia** (ini) | [Panduan lengkap](docs/ID.md)

---

## Fitur

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

---

## Persyaratan

- **Arsitektur:** ARM64 (`aarch64`)
- **Sistem:** Ubuntu 26.04 LTS atau Termux proot-distro
- **Python:** 3.14+ (dengan virtual environment)
- **Java:** OpenJDK 21+ (untuk APKTool & JADX)
- **RAM:** minimal 4 GB (disarankan 8 GB untuk APK besar)
- **Disk:** minimal 10 GB kosong

Tool yang terintegrasi: JADX 1.5.6, APKTool 3.0.3, apksigner, zipalign, aapt/aapt2, smali/baksmali 2.5.2, Androguard 4.1.4.

---

## Instalasi

```bash
git clone https://github.com/arifstia/arm64-apk-workbench.git
cd arm64-apk-workbench
chmod +x install.sh
./install.sh
```

Installer akan:
1. Memverifikasi arsitektur ARM64 dan tool sistem
2. Mengunduh **APKTool 3.0.3** dari rilis resmi + verifikasi SHA-256
3. Mengunduh **aapt2 ARM64 native** (dari ADT build-tools 37.0.0) + verifikasi SHA-256
4. Membuat wrapper `tools/bin/apktool` dan `tools/bin/aapt2`
5. Membangkitkan framework APKTool dari Android API 36
6. Menyiapkan virtual environment Python dan test keystore

Verifikasi instalasi:

```bash
./apk-workbench doctor
./apk-workbench tools
```

---

## Mulai Cepat

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

---

## Referensi Perintah

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

---

## Struktur Workspace

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

---

## Alur Kerja Umum

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

---

## Toolchain

| Tool | Versi | Fungsi |
|------|-------|--------|
| JADX | 1.5.6 | Dekompiler DEX → Java/Kotlin |
| APKTool | 3.0.3 (project-local) | Decode/build resource & Smali, targetSdk 37 |
| apksigner | 0.9 | Signing & verifikasi APK |
| zipalign | 10.0 | Alignment ZIP APK |
| aapt / aapt2 | 2.19 | Android asset packaging |
| smali / baksmali | 2.5.2 | Assembly/disassembly DEX |
| Androguard | 4.1.4 | Analisis APK berbasis Python |

### Catatan ARM64

- APKTool 2.7 bawaan sistem gagal decode ARSC modern (`targetSdkVersion: 37`). Workbench memakai **APKTool 3.0.3** hasil unduhan terverifikasi.
- aapt2 bawaan APKTool 3.x adalah binary **x86_64** dan tidak bisa jalan di ARM64. Workbench memakai **aapt2 ARM64 native** dari ADT build-tools 37.0.0.
- Framework APKTool dibangkitkan dari **Android API 36** agar resource `android:color/system_*` (targetSdk 35+) tersedia.
- Resource Material Components diawali `$` otomatis direname sebelum build dan dicatat di `patches/`.

---

## Laporan & Pengukuran

- [`reports/PERFORMANCE_REPORT.md`](reports/PERFORMANCE_REPORT.md) — hasil pengukuran nyata audit & build
- [`reports/GITHUB_RELEASE_AUDIT.md`](reports/GITHUB_RELEASE_AUDIT.md) — audit kesiapan rilis
- [`TOOLCHAIN.md`](TOOLCHAIN.md) — referensi detail toolchain
- [`WORKFLOW.md`](WORKFLOW.md) — alur kerja
- [`docs/ID.md`](docs/ID.md) — panduan lengkap bahasa Indonesia

---

## Keamanan & Etika

Tool ini **hanya untuk penggunaan yang sah** — menganalisis atau memodifikasi APK yang Anda miliki atau memiliki izin untuk memodifikasinya.

Workbench **tidak pernah**:
- Menimpa APK asli di `input/`
- Menghapus backup
- Menginstall APK ke perangkat secara otomatis
- Menyertakan private key pihak ketiga (hanya test key self-signed untuk development)
- Mengaktifkan fitur penyalahgunaan

Lihat [SECURITY.md](SECURITY.md) untuk detail.

---

## Lisensi

MIT License — lihat [LICENSE](LICENSE). Lisensi tool pihak ketiga tetap berlaku sebagaimana mestinya.

Copyright (c) 2026 **arifstia**
