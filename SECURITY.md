# SECURITY.md

## Security Guidelines

### 1. Authorized Use Only
This workbench is intended for analyzing and modifying **APKs you own or have explicit permission to modify**. Do not use for:
- Stealing data or intellectual property
- Bypassing authentication or license protections
- Intercepting communications or exfiltrating data
- Modifying apps without permission

### 2. Data Handling
- **Never** send APKs or their contents to external services
- **Never** use third-party signing keys (only use test keys)
- **Never** install APKs automatically without user consent
- **Always** preserve original APKs in `original/` directory

### 3. Test Signing
- Only use the test keystore at `build/keys/test_key.jks`
- Password: `testkey`
- Key alias: `test_key`
- Valid for 365 days

### 4. Build Verification
- Always run `apk-workbench verify` after signing
- Check certificate chain validity
- Confirm signature matches test keystore

### 5. Security Testing
- Use `apk-workbench audit` to check for suspicious permissions
- Review `patches/` directory for recorded changes
- Validate APK integrity before and after modification

### 6. Compliance
- Follow all applicable laws and regulations
- Respect software licenses and terms of service
- Do not use this tool for commercial redistribution without permission

## Emergency Protocol

If you detect suspicious behavior:
1. Stop all modification operations
2. Verify original APK integrity
3. Document findings in `reports/`
4. Consult security team if needed

**Remember**: With great power comes great responsibility.