# Contributing to AudAgent

Thank you for your interest in contributing to AudAgent! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/AudAgent.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`

## Development Setup

```bash
# Install in development mode
pip install -e .

# Run tests
python -m unittest tests.test_audagent -v

# Run examples to verify changes
python examples/basic_usage.py
python examples/advanced_usage.py
```

## How to Contribute

### Reporting Bugs

- Check if the bug has already been reported in Issues
- Include a clear description of the bug
- Provide steps to reproduce
- Include Python version and OS information
- Add code samples if applicable

### Suggesting Enhancements

- Clearly describe the enhancement
- Explain why it would be useful
- Provide examples of how it would work

### Pull Requests

1. **Make focused changes**: Each PR should address a single concern
2. **Write tests**: Add tests for new features or bug fixes
3. **Update documentation**: Update README.md if needed
4. **Follow code style**: Keep consistent with existing code
5. **Write clear commit messages**: Explain what and why

## Code Style Guidelines

- Follow PEP 8 Python style guide
- Use type hints where appropriate
- Write docstrings for all public methods
- Keep functions focused and single-purpose
- Use meaningful variable and function names

## Testing

- All tests must pass before submitting PR
- Add new tests for new features
- Maintain or improve code coverage
- Test edge cases

```bash
# Run all tests
python -m unittest tests.test_audagent -v

# Run specific test
python -m unittest tests.test_audagent.TestPrivacyAuditor.test_is_compliant
```

## Documentation

- Update README.md for user-facing changes
- Update docstrings for API changes
- Add examples for new features
- Keep QUICKSTART.md up to date

## Areas for Contribution

We welcome contributions in these areas:

### Core Features
- [ ] YAML policy file support
- [ ] Additional violation types
- [ ] Data retention tracking
- [ ] Consent management
- [ ] Policy versioning and migration

### Integrations
- [ ] Integration with popular AI frameworks (LangChain, etc.)
- [ ] API for remote monitoring
- [ ] Dashboard for visualization
- [ ] Export to different formats (PDF, HTML reports)

### Testing & Quality
- [ ] Increase test coverage
- [ ] Performance benchmarks
- [ ] Load testing
- [ ] Integration tests

### Documentation
- [ ] More examples and tutorials
- [ ] API reference documentation
- [ ] Video tutorials
- [ ] Blog posts and articles

### Tools
- [ ] CLI tool for policy validation
- [ ] Policy template generator
- [ ] Migration tools
- [ ] Debugging utilities

## Code Review Process

1. Maintainers will review your PR
2. Address any feedback or requested changes
3. Once approved, a maintainer will merge your PR

## Questions?

Feel free to open an issue for any questions about contributing.

## License

By contributing to AudAgent, you agree that your contributions will be licensed under the MIT License.
