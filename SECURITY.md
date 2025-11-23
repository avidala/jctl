# Security Policy

## Supported Versions

The following versions of jctl are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Features

### Authentication & Authorization

jctl implements multiple layers of security for authentication:

1. **OAuth 2.0 with PKCE** - Okta SSO integration using industry-standard OAuth 2.0 flow with PKCE (Proof Key for Code Exchange) for enhanced security
2. **API Token Support** - Alternative authentication using Jenkins API tokens for automation scenarios
3. **Secure Credential Storage** - Multiple storage mechanisms:
   - **OS-Native Keystore** (Primary): macOS Keychain, Linux SecretService, Windows Credential Manager
   - **Encrypted Fallback**: Fernet encryption with machine-derived keys when OS keystore unavailable
4. **Token Management** - Automatic token refresh and validation

### Data Protection

- **No Hardcoded Credentials** - All credentials are stored securely in OS keystore or encrypted storage
- **Machine-Derived Encryption Keys** - Fallback encryption uses PBKDF2 with machine-specific identifiers
- **SSL/TLS Verification** - All API calls use HTTPS with certificate verification (configurable)
- **No Secrets in Logs** - Sensitive data is never logged even in debug mode
- **Secure Token Storage** - OAuth tokens stored separately from configuration files

### Network Security

- **HTTPS Only** - All Jenkins API communication over secure HTTPS
- **Certificate Verification** - SSL certificate validation enabled by default
- **Retry Logic** - Exponential backoff prevents overwhelming Jenkins server
- **Timeout Configuration** - Separate connect (10s) and read (30s) timeouts

### Code Security

- **Security Scanning** - Codebase scanned with Bandit (0 vulnerabilities)
- **Dependency Scanning** - All dependencies checked with Safety (0 vulnerabilities)
- **No Code Injection** - Input validation and sanitization throughout
- **Type Safety** - Pydantic models for configuration validation

## Reporting a Vulnerability

### Where to Report

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly:

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please report security issues to:
- **Email**: avnervidal27@gmail.com
- **Slack**: avnervidal27@gmail.com () - DM a team member
- **Subject Line**: "SECURITY: [Brief Description]"

### What to Include

When reporting a vulnerability, please include:

1. **Description** - Clear description of the vulnerability
2. **Impact** - What could an attacker accomplish?
3. **Steps to Reproduce** - Detailed steps to reproduce the issue
4. **Proof of Concept** - Code or commands demonstrating the vulnerability (if applicable)
5. **Suggested Fix** - If you have ideas for remediation
6. **Environment Details**:
   - jctl version
   - Python version
   - Operating system
   - Jenkins version (if relevant)

### Response Timeline

We aim to respond to security reports according to the following timeline:

- **Initial Response**: Within 48 hours of report
- **Assessment**: Within 5 business days
- **Fix Development**: Varies by severity
  - Critical: 7 days
  - High: 14 days
  - Medium: 30 days
  - Low: Next release cycle
- **Release**: As soon as fix is tested and validated
- **Disclosure**: After fix is released (coordinated disclosure)

### Security Update Process

1. **Vulnerability Reported** - Team is notified
2. **Acknowledgment** - Reporter receives confirmation
3. **Assessment** - Team evaluates severity and impact
4. **Fix Development** - Patch is developed and tested
5. **Security Release** - Fix is released with security advisory
6. **Public Disclosure** - Details published after users have time to update

## Security Best Practices

### For Users

When using jctl, follow these security best practices:

#### Credential Management
- **Use OAuth** - Prefer Okta SSO over API tokens when possible
- **Rotate Tokens** - Regularly rotate API tokens if using token authentication
- **Limit Token Scope** - Use least-privilege principle for API tokens
- **Logout When Done** - Use `jctl auth logout` when finished with authenticated sessions

#### Configuration Security
- **Protect Config Files** - Ensure `~/.jctl/config.yaml` has appropriate permissions (0600)
- **Review Profiles** - Regularly audit configured profiles
- **Use Per-Environment Profiles** - Separate profiles for prod, staging, dev
- **SSL Verification** - Keep SSL verification enabled (`verify_ssl: true`)

#### Environment Security
- **Update Regularly** - Keep jctl updated to latest version
- **Secure Your Machine** - Use disk encryption and screen locks
- **Network Security** - Use VPN when accessing Jenkins on untrusted networks
- **Audit Logs** - Review Jenkins audit logs for unexpected activity

#### CI/CD Usage
- **Use API Tokens** - Not OAuth for automation
- **Secret Management** - Store tokens in CI/CD secrets manager
- **Limit Permissions** - Grant minimal required Jenkins permissions
- **Rotate Regularly** - Automate token rotation in CI/CD

### For Developers

If you're contributing to jctl:

#### Code Security
- **Input Validation** - Validate all user input
- **No Secrets in Code** - Never commit credentials or tokens
- **Dependency Updates** - Keep dependencies up-to-date
- **Security Testing** - Run bandit and safety before commits
- **Code Review** - All changes require review

#### Testing Security Features
- **Mock Credentials** - Use mock credentials in tests
- **Isolated Testing** - Test against test Jenkins instance
- **Secret Scanning** - Use pre-commit hooks to prevent secret commits
- **Security Tests** - Include security-specific test cases

## Known Security Considerations

### Keystore Fallback

When OS keystore is unavailable, jctl falls back to Fernet encryption:
- **Key Derivation**: Uses PBKDF2 with machine identifier
- **Storage**: Encrypted credentials in `~/.jctl/keystore.enc`
- **Limitation**: If machine identifier changes, credentials must be re-entered
- **Recommendation**: Use OS keystore when possible

### File Permissions

Configuration and credential files should have restricted permissions:
```bash
chmod 600 ~/.jctl/config.yaml
chmod 600 ~/.jctl/keystore.enc
```

jctl attempts to set these automatically but cannot enforce them.

### SSL Certificate Verification

While jctl allows disabling SSL verification (`--no-verify-ssl`):
- **NOT RECOMMENDED** for production use
- Only for testing with self-signed certificates
- Exposes traffic to man-in-the-middle attacks
- Use proper CA-signed certificates instead

### Debug Mode

Debug mode (`--debug`) outputs detailed logging:
- **Does NOT** log sensitive data (tokens, passwords)
- **May log** API endpoints and parameters
- **Review logs** before sharing publicly

## Security Audit History

### 2025-01-20 - Initial Beta Release (v0.1.0-beta.1)

**Security Scanning Results**:
- **Bandit**: 0 security vulnerabilities detected
- **Safety**: 0 vulnerabilities in dependencies
- **Code Review**: Manual security review completed
- **Credential Handling**: Verified secure storage mechanisms

**Security Features Implemented**:
- OS-native keystore integration
- Encrypted credential fallback
- OAuth 2.0 with PKCE
- Proper exception handling
- Retry logic with rate limiting
- SSL/TLS certificate verification

## Compliance

### Data Handling

jctl handles the following sensitive data:
- **OAuth Tokens** - Stored in OS keystore or encrypted storage
- **API Tokens** - Stored in OS keystore or encrypted storage
- **Configuration** - Plain text but no secrets (in `~/.jctl/config.yaml`)
- **Credentials** - Never stored in plain text
- **Logs** - Sensitive data redacted even in debug mode

### Privacy

jctl does not:
- Collect telemetry or analytics
- Send data to third parties
- Store credentials in plain text
- Log sensitive information
- Transmit data outside Jenkins/Okta APIs

## References

### Security Standards & Frameworks
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [PKCE RFC 7636](https://tools.ietf.org/html/rfc7636)
- [Fernet Encryption](https://cryptography.io/en/latest/fernet/)

### Related Security Documentation
- [Jenkins Security](https://www.jenkins.io/doc/book/security/)
- [Okta Security](https://www.okta.com/security/)
- [Python Keyring](https://keyring.readthedocs.io/)

## Contact

For security-related questions or concerns:
- **Email**: avnervidal27@gmail.com
- **Slack**: avnervidal27@gmail.com
- **GitHub Issues**: For non-security bugs only

---

**Last Updated**: 2025-01-20
**Version**: 0.1.0-beta.1
