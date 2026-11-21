# Contributing to ARM64 APK Workbench

Thank you for your interest in contributing! This project is maintained by **arifstia** and welcomes contributions from the community.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

1. Check existing issues first
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - System info (OS, architecture, tool versions)
   - Relevant logs from `logs/`

### Suggesting Features

1. Check existing issues and roadmap
2. Create a feature request issue with:
   - Clear use case
   - Proposed solution
   - Any alternatives considered

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes following the coding standards
4. Test your changes thoroughly
5. Submit a PR with clear description

## Development Setup

```bash
# Clone the repository
git clone https://github.com/arifstia/arm64-apk-workbench.git
cd arm64-apk-workbench

# Run installer
./install.sh

# Verify installation
apk-workbench doctor
```

## Coding Standards

### Python
- Follow PEP 8
- Use type hints
- Write docstrings for public functions
- Maximum line length: 100 characters
- Use `pathlib` for path operations

### Shell Scripts
- Use `set -euo pipefail`
- Quote all variables
- Use functions for repeated logic
- Add comments for complex operations

### Documentation
- Use clear, concise English
- Include code examples
- Update relevant docs when changing features

## Testing

Before submitting a PR:
1. Run `apk-workbench doctor` - all checks must pass
2. Test with a sample APK:
   ```bash
   apk-workbench audit input/test.apk
   apk-workbench decode input/test.apk
   apk-workbench build decoded/decoded_test_*
   apk-workbench verify build/rebuild_*.apk
   ```
3. Check for regressions in existing functionality

## Project Structure

```
arm64-apk-workbench/
├── apk-workbench          # Main CLI executable
├── install.sh             # Installer
├── uninstall.sh           # Uninstaller
├── scripts/               # Python engine scripts
│   ├── apk_workbench.py   # Main CLI
│   ├── apk_audit.py       # APK audit engine
│   └── apk_build.py       # APK build/decode engine
├── config/                # Configuration files
├── docs/                  # Documentation
├── examples/              # Example APKs and workflows
├── tests/                 # Test scripts
├── tools/                 # Tool binaries (if bundled)
└── .venv/                 # Python virtual environment
```

## ARM64 Considerations

- All binaries must be ARM64 compatible
- Test on ARM64 hardware or emulation
- Avoid x86_64 only dependencies
- Monitor memory usage (10GB RAM typical)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Contact

- Maintainer: arifstia
- GitHub: https://github.com/arifstia
- Repository: https://github.com/arifstia/arm64-apk-workbench