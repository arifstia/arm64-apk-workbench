# Entri Awesome List — siap copy-paste

File ini berisi entri siap pakai untuk mengajukan PR ke daftar "awesome" terkait.
**Cari dulu repositori yang masih aktif** (commit terakhir < 12 bulan) sebelum mengirim PR,
dan ikuti format/alfabet yang dipakai repo tersebut.

---

## Kandidat repositori

| Repo | Topik |
|------|-------|
| `awesome-termux` / `termux-awesome` | Termux, proot-distro, mobile hacking |
| `awesome-android` | Android development & tooling |
| `awesome-android-security` | Mobile security |
| `awesome-reverse-engineering` | Reverse engineering |
| `awesome-cli-tools` | Command-line tools |
| `awesome-arm` / `awesome-aarch64` | ARM64 tooling |

> GitHub Search: `awesome termux in:name`, `awesome android security in:name`, dll.

---

## Entri pendek (1 baris — paling sering dipakai)

```markdown
- [ARM64 APK Workbench](https://github.com/arifstia/arm64-apk-workbench) — CLI audit, decode, build, sign & verify APK untuk Ubuntu ARM64 / Termux proot-distro (APKTool 3.0.3 + native aapt2).
```

## Entri dengan deskripsi 2 baris

```markdown
- [ARM64 APK Workbench](https://github.com/arifstia/arm64-apk-workbench) — Workbench CLI untuk audit, decode, build, sign dan verifikasi APK di ARM64. Memakai APKTool 3.0.3 dan aapt2 native ARM64 sehingga targetSdk 37 bisa dibangun ulang tanpa Android Studio x86_64. MIT.
```

## Entri Bahasa Indonesia

```markdown
- [ARM64 APK Workbench](https://github.com/arifstia/arm64-apk-workbench) — Kumpulan perintah CLI untuk audit, decode, build, tanda tangani dan verifikasi APK di Ubuntu ARM64 / Termux. Mendukung targetSdk 37 dengan APKTool 3.0.3 + aapt2 ARM64.
```

---

## Pesan PR (template)

```markdown
Halo,

Saya ingin menambahkan [ARM64 APK Workbench](https://github.com/arifstia/arm64-apk-workbench)
ke daftar ini.

Penggalan yang ditambahkan:
- [ARM64 APK Workbench](...) — CLI audit, decode, build, sign & verify APK untuk Ubuntu ARM64 / Termux proot-distro.

Mengapa relevan:
- Berjalan di ARM64 (aarch64), termasuk Termux proot-distro.
- Memecahkan masalah nyata: APKTool 2.7 gagal decode ARSC targetSdk 37; proyek ini
  memakai APKTool 3.0.3 + aapt2 ARM64 terverifikasi.
- Open-source (MIT), semua perintah memiliki laporan pengujian publik di folder reports/.
- Aktif dipelihara oleh @arifstia.

Terima kasih atas pertimbangannya.
```

---

## Tips

- Jangan kirim PR ke repo yang sudah lama tidak aktif atau yang tidak menerima kontribusi.
- Satu PR = satu entri. Jangan spam beberapa repo sekaligus dalam waktu singkat.
- Balas komentar reviewer dengan cepat dan sopan.
- Kalau PR ditolak, jangan memaksa — cari daftar lain yang lebih relevan.
