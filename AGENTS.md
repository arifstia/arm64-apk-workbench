# AGENTS.md - OpenCode Agent Instructions

This file defines the rules and workflows for OpenCode AI agents working in the `apk-workbench` project.

## Core Principles

1. **Always audit before changes** — Run `apk-workbench doctor` and `apk-workbench audit <apk>` before any modification
2. **Never delete files without approval** — Ask before removing any workspace files
3. **Always backup before modification** — Use `apk-workbench backup <apk>` before any changes
4. **Use the right tool for each task** — jadx for decompilation, apktool for resource/build, androguard for analysis
5. **Verify changes before build** — Check diffs and validate smali/xml modifications
6. **Don't claim success without verification** — Run `apk-workbench verify` after every build
7. **Log every change** — Record modifications in `patches/` with timestamps
8. **Provide brief reports after each task** — Summary of what was done, results, and any issues
9. **Avoid excessive RAM usage** — Process APKs sequentially, not in parallel
10. **Never fabricate test results** — Report actual outcomes, including failures

## Workspace Rules

- **input/** — Read-only original APKs
- **original/** — Copies of original APKs (never modify)
- **backup/** — Timestamped backups (never modify)
- **decoded/** — Decoded resources/Smali (modify here)
- **analysis/** — Audit reports (read-only after generation)
- **patches/** — Modification records (YAML/JSON patches)
- **build/** — Rebuilt APKs (intermediate)
- **output/** — Final signed/aligned APKs
- **logs/** — Execution logs
- **scripts/** — Engine scripts (modify only with approval)
- **config/** — Configuration files
- **reports/** — Final reports
- **tools/** — Tool binaries (managed by setup scripts)
- **.venv/** — Python virtual environment

## Command Reference

```bash
# System check
apk-workbench doctor

# Tool versions
apk-workbench tools

# Full APK audit
apk-workbench audit input/app.apk

# Decode resources & Smali (15+ min on ARM64)
apk-workbench decode input/app.apk

# Create backup
apk-workbench backup input/app.apk

# Build from decoded source
apk-workbench build -s decoded/decoded_app_timestamp

# Verify signature
apk-workbench verify output/app.apk
```

## ARM64 Performance Notes

- **Decode**: ~14 minutes for 12MB APK on Termux proot-distro
- **Build**: ~2-3 minutes
- **Audit**: ~30 seconds
- **Zipalign/Sign**: ~10 seconds
- Use 1800s (30 min) timeout for decode operations
- Process one APK at a time to manage RAM

## Error Handling

- Check exit codes after every command
- Log stdout/stderr to `logs/`
- On decode timeout: check for partial decode in `decoded/`
- On build failure: verify `apktool.yml` exists in source
- On sign failure: verify test keystore exists
- On verify failure: check certificate chain