# APKTool 2.7 Gagal Decode targetSdk 37 di ARM64 — Jadi Saya Bangun Workbench CLI

*Artikel siap publish ke Medium, Substack, LinkedIn, atau blog pribadi. Bahasa Indonesia.*

---

Beberapa hari lalu saya mencoba membedah sebuah APK di lingkungan **Ubuntu 26.04 ARM64 (Termux proot-distro)**. Seperti biasa, saya jalankan APKTool 2.7 bawaan distro. Hasilnya:

```
Exception in thread "main" brut.androlib.AndrolibException: Could not decode arsc file
Caused by: java.io.IOException: Expected: 0x00000008, got: 0x0000005c
```

APK itu adalah `org.fdroid.fdroid` 2.0.2 dengan **targetSdk 37**. Masalahnya bukan pada APK-nya — tapi pada toolchain yang tertinggal.

## Masalah yang sebenarnya

Ada tiga lapis masalah yang saling bertumpuk di ARM64:

1. **APKTool 2.7 tidak paham ARSC modern.** Format resource table berubah; decode langsung gagal.
2. **APKTool 3.x membundel aapt2 x86_64.** Binary ini kena `SIGILL` (exit 132) di ARM64. Mustahil dipakai.
3. **aapt2 2.19 dari distro punya dua keterbatasan:** tidak mengenal flag `--no-compile-sdk-metadata`, tidak bisa membaca `resources.arsc` API 36, dan menolak resource Material Components yang diawali `$`.

Kalau Anda pernah bergumul dengan ini, Anda tahu rasanya: coba satu tool, gagal, ganti tool, gagal lagi.

## Solusinya: ARM64 APK Workbench

Saya kumpulkan semuanya jadi satu CLI yang bisa dijalankan di ARM64, dengan satu prinsip: **semua perintah harus benar-benar jalan, bukan sekadar ada.**

```bash
git clone https://github.com/arifstia/arm64-apk-workbench.git
cd arm64-apk-workbench
./install.sh
./apk-workbench doctor
```

Yang terjadi di balik layar:

- **APKTool 3.0.3** diunduh dari rilis resmi dan diverifikasi SHA-256 (`dbf930b0...`). Ini yang bisa decode targetSdk 37.
- **aapt2 ARM64 native** dari ADT build-tools 37.0.0 dipakai sebagai pengganti binary x86_64, juga terverifikasi (`c10af9c9...`).
- **Framework APKTool dibangkitkan dari Android API 36**, supaya resource `android:color/system_*` yang dipakai aplikasi targetSdk 35+ tersedia saat build ulang.
- **Resource berawalan `$` otomatis direname** sebelum build, dan perubahannya dicatat di `patches/` — jadi tidak ada perubahan diam-diam.

## Hasilnya

Saya uji penuh dari decode sampai tanda tangan:

```
$ ./apk-workbench build -s decoded/decoded_test_v3_full
    Compatibility: renamed 41 $-prefixed resources (recorded in patches/)
[1/5] Building APK with apktool...        OK (29.77s)
[2/5] Using existing test keystore.
[3/5] Zipaligning (4-byte alignment)...   OK (0.14s)
[4/5] Signing with test key...            OK (2.09s)
[5/5] Verifying signature...              Signature VALID
[+] Build COMPLETE and VERIFIED
```

APK 12 MB, targetSdk 37, berhasil di-decode, dibangun ulang, ditandatangani, dan terverifikasi (v2 + v3). Audit mode `deep` juga jalan — JADX menghasilkan 11.950 file Java, dan kalau keluar exit 3 sekalipun, tooling melaporkannya sebagai `partial`, bukan gagal total.

Semua angka pengukuran ada terbuka di [`reports/PERFORMANCE_REPORT.md`](https://github.com/arifstia/arm64-apk-workbench/blob/main/reports/PERFORMANCE_REPORT.md).

## Perintah yang tersedia

| Perintah | Fungsi |
|----------|--------|
| `doctor` | Cek kesehatan toolchain |
| `tools` | Daftar versi tool |
| `audit --mode fast\|normal\|deep` | Analisis APK |
| `decode` | Ekstrak resource + Smali |
| `backup` | Salinan APK ber-timestamp |
| `build -s DIR` | Build + zipalign + sign + verify |
| `verify` | Cek tanda tangan |
| `patch` | Catat perubahan |

## Prinsip keamanan

Ini tool untuk **penggunaan yang sah** — APK yang Anda miliki atau punya izin untuk memodifikasinya. Workbench tidak pernah menimpa APK asli, tidak menghapus backup, tidak menginstall APK otomatis, dan tidak menyimpan private key pihak ketiga. Hanya test key self-signed untuk development.

## Penutup

Kalau Anda menjalankan Android tooling di ARM64 — baik di Ubuntu, proot-distro, maupun Termux — saya harap ini menghemat waktu Anda. Reponya open-source dengan lisensi MIT:

🔗 **https://github.com/arifstia/arm64-apk-workbench**

Star, issue, dan PR sangat saya hargai. Kalau Anda menemukan APK yang masih gagal, lampirkan versi toolchain dan log-nya — itu langsung jadi bahan perbaikan berikutnya.

— *arifstia*
