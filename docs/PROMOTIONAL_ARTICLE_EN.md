# Reverse Engineering APKs on ARM64 Without x86_64 Android Studio

*A ready-to-publish article for dev.to, Hashnode, Reddit r/termux, r/androiddev, or r/ReverseEngineering. English.*

---

I recently tried to inspect an APK on **Ubuntu 26.04 ARM64 running inside Termux proot-distro**. I ran the distro's APKTool 2.7 like I always do, and got this:

```
Exception in thread "main" brut.androlib.AndrolibException: Could not decode arsc file
Caused by: java.io.IOException: Expected: 0x00000008, got: 0x0000005c
```

The APK was `org.fdroid.fdroid` 2.0.2, **targetSdk 37**. The APK was fine. My toolchain was not.

## Three stacked problems on ARM64

1. **APKTool 2.7 cannot parse modern ARSC.** The resource table format changed, so decoding fails immediately.
2. **APKTool 3.x bundles an x86_64 aapt2.** On ARM64 it dies with `SIGILL` (exit 132). Unusable.
3. **Distro aapt2 2.19 has its own limits:** it rejects `--no-compile-sdk-metadata`, cannot read API 36 `resources.arsc`, and refuses Material Components resource names beginning with `$`.

If you have been through this, you know the loop: try one tool, fail, swap tools, fail again.

## The solution: ARM64 APK Workbench

I consolidated everything into one CLI with a single rule: **every command must actually run, not merely exist.**

```bash
git clone https://github.com/arifstia/arm64-apk-workbench.git
cd arm64-apk-workbench
./install.sh
./apk-workbench doctor
```

What happens under the hood:

- **APKTool 3.0.3** is downloaded from the official release and SHA-256 verified (`dbf930b0...`). This is what decodes targetSdk 37.
- **Native ARM64 aapt2** from ADT build-tools 37.0.0 replaces the x86_64 binary, also checksum-verified (`c10af9c9...`).
- **The APKTool framework is generated from Android API 36**, so `android:color/system_*` resources used by targetSdk 35+ apps resolve during rebuild.
- **`$`-prefixed resources are renamed automatically** before build, and every change is recorded in `patches/` — no silent edits.

## Results

I ran the full pipeline:

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

A 12 MB targetSdk 37 APK decoded, rebuilt, signed and verified (v2 + v3). Deep audit works too — JADX produced 11,950 Java files, and even when it exits 3 the tooling reports `partial` instead of a hard failure.

All measurements are public in [`reports/PERFORMANCE_REPORT.md`](https://github.com/arifstia/arm64-apk-workbench/blob/main/reports/PERFORMANCE_REPORT.md).

## Available commands

| Command | Purpose |
|---------|---------|
| `doctor` | Health-check the toolchain |
| `tools` | List tool versions |
| `audit --mode fast\|normal\|deep` | Analyze an APK |
| `decode` | Extract resources + Smali |
| `backup` | Timestamped APK copy |
| `build -s DIR` | Build + zipalign + sign + verify |
| `verify` | Verify signatures |
| `patch` | Record modifications |

## Safety

This is for **authorized use only** — APKs you own or have permission to modify. It never overwrites originals, deletes backups, installs APKs automatically, or ships third-party private keys. Only a self-signed test key is included for development.

## Wrapping up

If you do Android tooling on ARM64 — Ubuntu, proot-distro, or Termux — I hope this saves you a few hours. The project is MIT licensed:

🔗 **https://github.com/arifstia/arm64-apk-workbench**

Stars, issues and PRs are welcome. If an APK still fails, include your toolchain versions and logs — that is the fastest path to the next fix.

— *arifstia*
