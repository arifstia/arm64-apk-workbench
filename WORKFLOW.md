# APK Workbench Workflow

## Standard Modification Pipeline

### Phase 1: Audit
```bash
apk-workbench doctor          # Verify environment
apk-workbench audit input/app.apk    # Full audit
```

### Phase 2: Backup
```bash
apk-workbench backup input/app.apk  # Timestamped backup
```

### Phase 3: Decode
```bash
apk-workbench decode input/app.apk  # ~15 min on ARM64
```

### Phase 4: Modify
```bash
# Edit files in decoded/<source>/
# - AndroidManifest.xml
# - smali/ directory
# - res/ directory

# Record changes in patches/
```

### Phase 5: Build
```bash
apk-workbench build -s decoded/decoded_app_timestamp
```

### Phase 6: Align & Sign
```bash
zipalign -v 4 build/output.apk signed.apk
apksigner sign --ks build/keys/test_key.jks -ks-pass pass:testkey \
    --out signed.apk build/output.apk
```

### Phase 7: Verify
```bash
apk-workbench verify signed.apk
```

### Phase 8: Report
- Generate final report in `reports/FINAL_REPORT.md`
- Save audit JSON/Markdown to `analysis/`
- Save build artifacts to `output/`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Decode timeout | Increase timeout to 1800s; check partial decode |
| Missing apktool.yml | Re-run full decode; ensure no failures |
| Build failure | Verify decoded directory contains apktool.yml |
| Sign failure | Generate test keystore with keytool |
| Verify failure | Check certificate validity |

## Safety

- Always backup before modifications
- Always verify after build
- Always use test signing keys
- Never modify original APKs
- Follow security guidelines in SECURITY.md
