# Contributing to Open Mental Health Collective (OMHC)

Thank you for your interest in contributing to OMHC! This project aims to provide safe, ethical mental health support through AI agents.

## 🎯 Project Goals

- Provide low-intensity mental health support for adults with mild-to-moderate distress
- Maintain the highest safety and ethical standards
- Create an auditable, testable multi-agent architecture
- Serve as a research prototype for responsible AI in healthcare

## 🚨 Important Disclaimers

This is a **research prototype**, not a clinical system. All contributions must:
- Prioritize user safety above all else
- Maintain conservative risk assessment
- Never claim to replace professional care
- Include appropriate disclaimers

## 🤝 How to Contribute

### Reporting Bugs

1. Check if the issue already exists in [Issues](../../issues)
2. Create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version, OS, and relevant environment details
   - Logs or error messages (redact any sensitive info)

### Suggesting Enhancements

1. Open an issue with the `enhancement` label
2. Describe the feature and its benefits
3. Explain how it aligns with project goals
4. Consider safety implications

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**:
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed
4. **Run tests**: `pytest`
5. **Commit with clear messages**: 
   ```
   Add feature: Brief description
   
   - Detailed point 1
   - Detailed point 2
   ```
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Open a Pull Request**

## 📝 Code Standards

### Python Style
- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters (Black default)
- Docstrings for public functions and classes

### Testing
- All new features must include tests
- Maintain or improve test coverage
- Safety-critical code requires comprehensive tests
- Run `pytest -vv` before submitting

### Safety Requirements
- **Never** encourage self-harm or violence
- **Always** include appropriate disclaimers
- **Conservative** risk classification
- **Clear** escalation pathways to human support

## 🔒 Security

- Never commit API keys, credentials, or secrets
- Use `.env.example` for configuration templates
- Report security vulnerabilities privately (see [SECURITY.md](SECURITY.md))

## 📚 Documentation

- Update README.md for user-facing changes
- Add inline comments for complex logic
- Update docstrings when changing function signatures
- Include examples for new features

## 🧪 Testing Guidelines

### Required Tests
- Unit tests for new functions
- Integration tests for agent interactions
- Safety tests for risk-related changes
- E2E tests for major features

### Test Organization
```
tests/
├── pytests/
│   ├── test_*.py          # Unit and integration tests
│   └── test_e2e_*.py      # End-to-end tests
```

## 🎨 Commit Message Guidelines

Use clear, descriptive commit messages:

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `style`: Formatting changes
- `chore`: Maintenance tasks

**Example:**
```
feat: Add crisis escalation channel selection

- Implement escalation_channel field in SafetyDecisionV2
- Add validation for channel selection
- Update tests for new safety logic

Closes #42
```

## 🌟 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions

## ❓ Questions?

- Open a [Discussion](../../discussions)
- Review existing [Issues](../../issues)
- Check the [README](README.md) for documentation

## 📜 License

By contributing, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE)).

---

**Thank you for helping make mental health support more accessible and safe!** 🙏
