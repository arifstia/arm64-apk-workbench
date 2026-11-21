# ARM64 APK Workbench - Dokumentasi Bahasa Indonesia

**ARM64 APK Workbench** - Toolkit analisis dan modifikasi APK Android untuk Ubuntu ARM64 dan Termux.
Dibuat dan dikelola oleh **arifstia** - https://github.com/arifstia

---

## Daftar Isi

1. [Ikhtisar Proyek](#ikhtisar-proyek)
2. [Fitur](#fitur)
3. [Persyaratan Sistem](#persyaratan-sistem)
4. [Instalasi](#instalasi)
5. [Perintah CLI](#perintah-cli)
6. [Alur Kerja Analisis APK](#alur-kerja-analisis-apk)
7. [Alur Kerja Modifikasi APK](#alur-kerja-modifikasi-apk)
8. [Mode Performa](#mode-performa)
9. [Troubleshooting](#troubleshooting)
10. [Keamanan](#keamanan)
11. [Keterbatasan](#keterbatasan)
12. [Roadmap](#roadmap)
13. [Kontribusi](#kontribusi)
14. [Lisensi](#lisensi)
15. [Penulis](#penulis)

---

## Ikhtisar Proyek

ARM64 APK Workbench adalah toolkit command-line interface (CLI) untuk analisis dan modifikasi file APK Android, dirancang khusus untuk arsitektur **ARM64 (aarch64)** di **Ubuntu 26.04** dan **Termux proot-distro**.

Proyek ini mengintegrasikan berbagai tools standar industri:
- **JADX** - Dekompiler DEX ke Java/Kotlin
- **APKTool 3.0.3** - Decode/build resource dan Smali (project-local, mendukung targetSdk 37)
- **Androguard** - Analisis APK mendalam (Python)
- **apksigner** - Signing dan verifikasi APK
- **zipalign** - Optimasi alignment APK
- **aapt/aapt2** - Android Asset Packaging Tool
- **smali/baksmali** - Assembly/disassembly DEX
- **OpenCode** - Integrasi AI untuk analisis otomatis

---

## Fitur

| Fitur | Deskripsi |
|-------|-----------|
| **Audit APK** | Analisis manifest, permissions, DEX, native libraries, resources, certificates |
| **Decode APK** | Ekstrak resource dan Smali menggunakan APKTool 3.0.3 (~14 menit untuk 12MB APK di ARM64, historis) |
| **Build APK** | Build ulang APK dari source yang sudah di-decode |
| **Sign APK** | Signing dengan test key (hanya untuk development) |
| **Verify APK** | Verifikasi signature dan certificate chain |
| **Backup APK** | Backup otomatis dengan timestamp sebelum modifikasi |
| **Mode Performa** | FAST / NORMAL / DEEP untuk kebutuhan berbeda |
| **Integrasi AI** | OpenCode siap digunakan untuk analisis otomatis |
| **Laporan** | Output JSON dan Markdown untuk setiap operasi |

---

## Persyaratan Sistem

### Minimum
- **OS**: Ubuntu 26.04 LTS (Resolute Raccoon) ARM64
- **Arsitektur**: aarch64 / ARM64 (wajib - binary x86_64 tidak akan jalan)
- **RAM**: 4 GB tersedia (10 GB direkomendasikan)
- **Storage**: 10 GB kosong
- **Java**: OpenJDK 21+ (ARM64)
- **Python**: 3.10+ dengan venv
- **Node.js**: 18+ (untuk OpenCode)

### Direkomendasikan
- **RAM**: 10 GB+
- **Storage**: 50 GB+
- **CPU**: 4+ core ARM64
- **Termux**: proot-distro Ubuntu 26.04

---

## Instalasi

### Otomatis (Direkomendasikan)

```bash
# Clone repository
git clone https://github.com/arifstia/arm64-apk-workbench.git
cd arm64-apk-workbench

# Jalankan installer
chmod +x install.sh
./install.sh
```

Installer akan:
1. Mendeteksi OS dan arsitektur ARM64
2. Memeriksa Java, Python, Node.js, OpenCode
3. Menginstal tool Android (APKTool, apksigner, zipalign, aapt, aapt2, smali, baksmali)
4. Mengunduh dan memasang JADX
5. Membuat virtual environment Python
6. Memasang Androguard
7. Membuat struktur workspace
8. Menghasilkan test keystore
9. Memverifikasi instalasi

### Manual

Jika installer gagal, ikuti langkah manual:

```bash
# 1. Install dependensi sistem
apt-get update && apt-get install -y \
    openjdk-21-jdk-headless \
    python3 python3-venv python3-pip \
    nodejs \
    apktool \
    android-sdk-build-tools \
    smali \
    unzip wget curl

# 2. Install JADX
JADX_VERSION="1.5.6"
wget "https://github.com/jadx-decompiler/jadx/releases/download/v${JADX_VERSION}/jadx-${JADX_VERSION}.zip"
unzip jadx-${JADX_VERSION}.zip -d /opt/jadx-${JADX_VERSION}
ln -sf /opt/jadx-${JADX_VERSION}/bin/jadx /usr/local/bin/jadx

# 3. Setup Python venv
python3 -m venv .venv
.venv/bin/pip install androguard==4.1.4

# 4. Install OpenCode (opsional)
# Ikuti instruksi di https://opencode.ai

# 5. Buat workspace
mkdir -p input original backup decoded analysis patches build output logs scripts config reports tools docs examples tests

# 6. Generate test keystore
mkdir -p build/keys
keytool -genkey -v -keystore build/keys/test_key.jks \
    -alias test_key -keyalg RSA -keysize 2048 -validity 365 \
    -keypass testkey -storepass testkey \
    -dname "CN=Test Key, OU=Test, O=Test, L=Test, S=Test, C=US"
```

---

## Perintah CLI

Semua perintah dijalankan melalui executable `apk-workbench`:

```bash
# Bantuan
apk-workbench --help
apk-workbench --version

# System check
apk-workbench doctor                    # Cek dependensi dan environment
apk-workbench tools                     # List tool terpasang dengan versi

# APK Analysis
apk-workbench audit <file.apk>          # Audit lengkap APK
apk-workbench audit <file.apk> --mode fast    # Audit cepat (hanya metadata)
apk-workbench audit <file.apk> --mode normal  # Audit standar (default)
apk-workbench audit <file.apk> --mode deep    # Audit mendalam
apk-workbench analyze <file.apk>        # Alias untuk audit

# APK Decode
apk-workbench decode <file.apk>         # Decode resource + Smali
apk-workbench decode <file.apk> -o /path/to/output  # Custom output directory

# APK Backup
apk-workbench backup <file.apk>         # Backup dengan timestamp

# APK Build
apk-workbench build <decoded_dir>       # Build dari source yang di-decode
apk-workbench build -s <decoded_dir> -o output.apk  # Custom output

# APK Verify
apk-workbench verify <file.apk>         # Verifikasi signature
```

### Contoh Penggunaan Lengkap

```bash
# 1. Cek sistem
apk-workbench doctor

# 2. Audit APK
apk-workbench audit input/app.apk

# 3. Backup APK asli
apk-workbench backup input/app.apk

# 4. Decode APK (butuh waktu ~15 menit di ARM64)
apk-workbench decode input/app.apk

# 5. Modifikasi file di decoded/decoded_app_timestamp/
#    - Edit AndroidManifest.xml
#    - Edit smali/ untuk logika aplikasi
#    - Edit res/ untuk resource

# 6. Build APK
apk-workbench build decoded/decoded_app_timestamp

# 7. Verifikasi hasil build
apk-workbench verify build/rebuild_*.apk

# 8. APK siap di output/
```

---

## Alur Kerja Analisis APK

### Phase 1: Persiapan
```bash
apk-workbench doctor        # Verifikasi environment
apk-workbench audit app.apk # Audit lengkap
```

### Phase 2: Analisis Laporan
Laporan dihasilkan di `analysis/`:
- `audit_<nama>_<timestamp>.json` - Data terstruktur
- `audit_<nama>_<timestamp>.md` - Laporan readable

Laporan berisi:
- **Basic Info**: Package name, version, min/target SDK, label, ABIs, locales, densities
- **Size Analysis**: Ukuran file, compression ratio, ZIP entries
- **Permissions**: Semua permissions dari aapt dan Androguard
- **Manifest**: Activities, services, receivers, providers, libraries
- **DEX Analysis**: Jumlah DEX, classes, methods, fields, strings
- **Native Libraries**: .so files per ABI dengan ukuran
- **Resources**: Jumlah file per tipe resource
- **Certificates**: Informasi signer dan digest

---

## Alur Kerja Modifikasi APK

### Standar Pipeline

```bash
# 1. Audit
apk-workbench doctor
apk-workbench audit input/app.apk

# 2. Backup (WAJIB)
apk-workbench backup input/app.apk

# 3. Decode (~15 menit di ARM64)
apk-workbench decode input/app.apk

# 4. Modifikasi
# Edit file di decoded/decoded_app_timestamp/:
# - AndroidManifest.xml (permissions, components, dll)
# - smali/ (logika aplikasi - butuh pengetahuan Smali)
# - res/ (resource: layout, drawable, values, dll)

# 5. Catat perubahan di patches/
# Format: YAML/JSON dengan timestamp

# 6. Build
apk-workbench build -s decoded/decoded_app_timestamp

# 7. Zipalign & Sign (otomatis via build engine)
# Atau manual:
zipalign -v 4 build/output.apk aligned.apk
apksigner sign --ks build/keys/test_key.jks --ks-pass pass:testkey \
    --out signed.apk aligned.apk

# 8. Verify
apk-workbench verify signed.apk
```

### Aturan Keamanan Modifikasi

1. **APK asli TIDAK BOLEH ditimpa** - Simpan di `original/`
2. **Backup TIDAK BOLEH dihapus otomatis** - Simpan di `backup/`
3. **HANYA gunakan test key** - Jangan gunakan production key
4. **JANGAN install APK otomatis** - Manual install saja
5. **JANGAN klaim build sukses sebelum verifikasi**
6. **Catat SETIAP perubahan** di `patches/`
7. **HANYA modifikasi aplikasi milik sendiri** atau yang punya izin

---

## Mode Performa

### FAST MODE
Untuk pemeriksaan cepat:
- Pemeriksaan minimum (metadata saja)
- Tidak dekompilasi ulang jika cache valid
- Hanya baca file yang diperlukan
- Gunakan cache yang tervalidasi
- Skip analisis seluruh proyek

### NORMAL MODE (Default)
Untuk pekerjaan standar:
- Audit APK lengkap
- Decode jika diperlukan
- Analisis file terkait
- Patch dan build
- Verifikasi

### DEEP MODE
Untuk pemeriksaan menyeluruh:
- Audit lengkap + manifest analysis
- DEX analysis mendalam
- Resource analysis lengkap
- Native library inspection
- Perubahan detection
- Build dan verification penuh

```bash
apk-workbench audit app.apk --mode fast
apk-workbench audit app.apk --mode normal
apk-workbench audit app.apk --mode deep
```

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Decode timeout (>15 menit) | Tingkatkan timeout ke 1800s; cek partial decode di `decoded/` |
| `apktool.yml` tidak ditemukan | Jalankan decode ulang lengkap; pastikan tidak ada error |
| Build gagal | Verifikasi direktori source berisi `apktool.yml` |
| Sign gagal | Generate test keystore dengan `keytool` |
| Verify gagal | Cek validitas certificate chain |
| RAM penuh | Proses satu APK saja; jangan paralel |
| JADX error | Pastikan Java ARM64; cek versi JADX |

### Log dan Debug
- Semua log tersimpan di `logs/`
- Cek `apk-workbench doctor` untuk status tool
- Gunakan `apk-workbench tools` untuk versi detail

---

## Keamanan

### Pedoman Penggunaan
- **HANYA untuk APK yang Anda miliki** atau punya izin modifikasi
- **JANGAN** gunakan untuk:
  - Mencuri data atau intellectual property
  - Bypass autentikasi atau proteksi lisensi
  - Intercept komunikasi atau eksfiltrasi data
  - Modifikasi aplikasi tanpa izin

### Penanganan Data
- **JANGAN** kirim APK atau kontennya ke layanan eksternal
- **JANGAN** gunakan signing key pihak ketiga (hanya test key)
- **JANGAN** install APK otomatis tanpa persetujuan user
- **SELALU** simpan APK asli di `original/`

### Test Signing
- Gunakan test keystore: `build/keys/test_key.jks`
- Password: `testkey`
- Key alias: `test_key`
- Valid: 365 hari

### Verifikasi Build
- Selalu jalankan `apk-workbench verify` setelah signing
- Cek certificate chain validity
- Konfirmasi signature cocok dengan test keystore

### Compliance
- Ikuti semua hukum dan regulasi berlaku
- Hormati lisensi software dan terms of service
- Jangan gunakan tool ini untuk redistribusi komersial tanpa izin

---

## Keterbatasan

1. **ARM64 Only** - Binary x86_64 tidak kompatibel
2. **Decode Lambat** - ~14 menit untuk 12MB APK di ARM64 (batasan APKTool + Java)
3. **RAM Tinggi** - Butuh 4GB+ RAM untuk APK besar
4. **Smali Manual** - Modifikasi logika butuh pengetahuan Smali assembly
5. **Test Key Only** - APK hasil build hanya untuk testing, tidak untuk distribusi
6. **No GUI** - CLI only, tidak ada antarmuka grafis
7. **Single APK** - Proses satu APK per waktu untuk manajemen RAM

---

## Roadmap

### v1.1.0 (Current)
- ✅ Cache audit per SHA-256 + mode — deep: 62 detik → 0,58 detik pada cache hit
- ✅ Opsi `--no-cache` + penanda `cache.hit` di laporan JSON/Markdown
- ✅ Patch management: snapshot, diff, rollback, export bundle, apply, `--dry-run`
- ✅ Backup otomatis sebelum timpa; tidak ada file yang dihapus
- ✅ `requirements.txt` dengan androguard 4.1.4 terpin — 30 unit test, CI hijau

### v1.0.1
- ✅ Perbaikan portabilitas CLI (bisa di-clone ke direktori mana saja)
- ✅ APKTool 3.0.3 + aapt2 ARM64 native + framework API 36 (targetSdk 37)
- ✅ GitHub Actions smoke test & dokumentasi bilingual

### v1.0.0
- ✅ APK audit, decode, analysis
- ✅ Build workflow
- ✅ CLI dengan semua command
- ✅ OpenCode integration
- ✅ ARM64 support
- ✅ Installer & documentation

### v1.2.0 (Planned)
- 🔄 Advanced project analysis
- 🔄 Improved patch management
- 🔄 Additional automation

### v2.0.0 (Planned)
- 🔄 Modular architecture
- 🔄 Expanded Linux ARM64 support
- 🔄 More AI-assisted workflows

---

## Kontribusi

Lihat [CONTRIBUTING.md](../CONTRIBUTING.md) untuk panduan kontribusi.

Singkatnya:
1. Fork repository
2. Buat feature branch
3. Ikuti coding standards (PEP 8 untuk Python)
4. Test perubahan Anda
5. Submit Pull Request

---

## Lisensi

**MIT License** - Lihat [LICENSE](../LICENSE) untuk detail.

Copyright (c) 2026 arifstia

Tools pihak ketiga memiliki lisensi masing-masing:
- JADX: Apache 2.0
- APKTool: Apache 2.0
- Androguard: Apache 2.0
- smali/baksmali: BSD 3-Clause
- Android SDK Build Tools: Apache 2.0
- OpenJDK: GPL v2 with Classpath Exception

---

## Penulis

**Created and maintained by arifstia**

- GitHub: https://github.com/arifstia
- Repository: https://github.com/arifstia/arm64-apk-workbench

---

*Dokumentasi ini adalah terjemahan Bahasa Indonesia dari README.md. Untuk versi terbaru dan lengkap, rujuk README.md (Bahasa Inggris).*