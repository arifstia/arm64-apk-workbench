# Status Promosi Repository

Tanggal: 2026-11-21 · Penulis: arifstia

Laporan ini mencatat apa yang sudah dikerjakan untuk meningkatkan visibilitas
`arifstia/arm64-apk-workbench`, dan apa yang masih perlu aksi manual di UI GitHub.

---

## ✅ Selesai (otomatis / via API / via git)

| Item | Detail | Status |
|------|--------|--------|
| GitHub Topics | 20 topik: `android`, `apk`, `reverse-engineering`, `arm64`, `aarch64`, `termux`, `apktool`, `jadx`, `androguard`, `mobile-security`, `cli`, `ubuntu`, `static-analysis`, `apk-signing`, `android-reverse-engineering`, `smali`, `apk-analysis`, `security-tools`, `command-line`, `linux` | ✅ |
| Deskripsi repo | Diperbarui via REST API | ✅ |
| Homepage repo | Mengarah ke `docs/ID.md` | ✅ |
| Issues diaktifkan | `has_issues: true` | ✅ |
| Social preview | `docs/assets/social-preview.png` (1280×640, 8-bit sRGB, 52 KB) + sumber SVG | ✅ file siap |
| README bilingual | Satu `README.md` berisi Bahasa Indonesia + English, pemilih bahasa di atas | ✅ |
| Real demo output | Contoh `doctor`, `audit --mode fast`, dan `build` targetSdk 37 di kedua bahasa | ✅ |
| One-line install | Ditaruh di dekat bagian atas README | ✅ |
| Badge | CI, release, stars, forks, platform, MIT | ✅ |
| GitHub Actions | `.github/workflows/smoke.yml` — x86_64 + ARM64 (advisory), 10 unit tests, guard binary/secret | ✅ |
| Unit tests | `tests/test_smoke.py` — 10 test, dijalankan lokal: **OK** (0.053s) | ✅ |
| Issue templates | Bug report, feature request, config | ✅ |
| Artikel promosi | `docs/ARTIKEL_PROMOSI_ID.md`, `docs/PROMOTIONAL_ARTICLE_EN.md` | ✅ |
| Awesome-list | `docs/AWESOME_LIST_ENTRIES.md` (3 varian entri + template PR) | ✅ |
| Bug portabilitas | Entry point tidak lagi hardcode `/root/projects/apk-workbench` | ✅ |

---

## ⚠️ Perlu aksi manual di UI GitHub

1. **Pasang Social Preview image**
   - Buka repo → **Settings** → **General** → **Social preview** → **Upload image**
   - Pilih `docs/assets/social-preview.png` (sudah 1280×640).
   - REST API tidak menyediakan endpoint untuk ini.

2. **Buat label secara manual** (token PAT hanya punya izin metadata + contents, bukan Issues)
   - **Issues** → **Labels** → **New label**, lalu buat:
     `bug` (`#d73a4a`), `enhancement` (`#a2eeef`), `documentation` (`#0075ca`),
     `good first issue` (`#7057ff`), `help wanted` (`#008672`), `arm64` (`#5bd8f5`),
     `question` (`#d876e3`).

3. **Aktifkan Discussions** (opsional)
   - **Settings** → **Features** → centang **Discussions**.
   - Template issue sudah menautkan ke URL Discussions.

4. **Submit PR ke awesome-list**
   - Cari repo yang masih aktif, lalu gunakan entri dari `docs/AWESOME_LIST_ENTRIES.md`.
   - Satu PR = satu repo. Jangan spam.

5. **Publish artikel**
   - Indonesia: `docs/ARTIKEL_PROMOSI_ID.md` → Medium / Substack / LinkedIn.
   - English: `docs/PROMOTIONAL_ARTICLE_EN.md` → dev.to / Hashnode / Reddit.
   - Untuk Reddit, sertakan dulu konteks masalah (APKTool 2.7 gagal), bukan promosi mentah.

6. **Verifikasi badge CI**
   - Setelah push, buka **Actions** dan pastikan workflow `Smoke Test` hijau.
   - Job ARM64 bersifat advisory (`continue-on-error: true`).

---

## Catatan kejujuran

- Tidak ada star, fork, atau follower yang dibeli/dibot.
- Semua angka di README dan artikel berasal dari pengujian nyata yang tercatat di
  `reports/PERFORMANCE_REPORT.md` dan `reports/GITHUB_RELEASE_AUDIT.md`.
- Image generator AI gagal karena kredensial tidak valid; social preview dibuat sebagai
  SVG lalu dikonversi ke PNG dengan ImageMagick yang tersedia lokal.
- Label GitHub belum terpasang karena keterbatasan izin token, bukan karena diabaikan.
