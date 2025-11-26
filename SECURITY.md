# Security Policy

## 🔒 Reporting Security Vulnerabilities

**Please do NOT report security vulnerabilities through public GitHub issues.**

### For Security Issues:

If you discover a security vulnerability in OMHC, please report it privately:

1. **Email**: [Your email or create a security@yourdomain.com]
2. **Subject**: `[SECURITY] Brief description`
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will acknowledge your email within 48 hours and provide a detailed response within 7 days.

## 🚨 Critical Safety Issues

Given the sensitive nature of mental health support, we treat the following as **critical security issues**:

### High Priority:
- Bypassing safety ceiling mechanisms
- Incorrect risk classification that could endanger users
- Exposure of user conversations or personal data
- Injection attacks that could produce harmful content
- Authentication/authorization bypasses

### Medium Priority:
- Information disclosure
- Denial of service vulnerabilities
- Dependency vulnerabilities

## 🛡️ Security Best Practices

### For Users:
- Never share API keys or credentials
- Use environment variables for secrets (`.env` file)
- Keep dependencies updated
- Review logs for suspicious activity

### For Contributors:
- Never commit secrets to the repository
- Use `.env.example` for configuration templates
- Run security scans before submitting PRs
- Follow the principle of least privilege

## 📦 Dependency Security

We monitor dependencies for known vulnerabilities:
- Regular updates via Dependabot
- Security advisories reviewed promptly
- Critical patches applied immediately

## 🔐 Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## 🏆 Responsible Disclosure

We follow responsible disclosure practices:

1. **Report received**: We acknowledge within 48 hours
2. **Investigation**: We investigate and validate the issue
3. **Fix development**: We develop and test a fix
4. **Coordinated disclosure**: We coordinate public disclosure with the reporter
5. **Credit**: We credit the reporter (unless they prefer anonymity)

## 📝 Security Updates

Security updates will be:
- Released as patch versions
- Documented in release notes
- Announced via GitHub Security Advisories

## ⚠️ Disclaimer

OMHC is a **research prototype** for educational purposes. It is:
- **NOT** a clinical system
- **NOT** suitable for production use without extensive additional safety measures
- **NOT** a replacement for professional mental health care
- **NOT** designed for emergency situations

Users should:
- Contact emergency services (911, 988, etc.) for immediate danger
- Seek professional help for mental health concerns
- Understand the limitations of AI-based support

## 🤝 Security Acknowledgments

We thank the following researchers for responsibly disclosing security issues:
- [To be added as issues are reported and resolved]

---

**Last Updated**: 2025-01-25
