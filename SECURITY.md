# Security Policy

## Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them responsibly by:

1. **Email**: Send details to the project maintainers (check repository for contact)
2. **GitHub Security Advisories**: Use the "Security" tab in the GitHub repository

### What to Include

Please include the following information:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Varies by severity (see below)

### Severity Levels

| Severity | Description | Response Time |
|----------|-------------|---------------|
| Critical | Remote code execution, data breach | 1-3 days |
| High | Authentication bypass, privilege escalation | 3-7 days |
| Medium | XSS, CSRF, information disclosure | 7-14 days |
| Low | Minor information leaks | 14-30 days |

## Security Best Practices

### For Developers

1. **Never commit secrets**
   - Use `.env` files (already in `.gitignore`)
   - Use environment variables for sensitive data
   - Use `detect-secrets` pre-commit hook

2. **Input Validation**
   - Validate all user inputs
   - Use Pydantic models for request validation
   - Sanitize data before database queries

3. **Authentication & Authorization**
   - Implement proper authentication for production
   - Use JWT tokens or OAuth2
   - Validate all API requests

4. **Dependencies**
   - Keep dependencies up to date
   - Run `npm audit` and `safety check` regularly
   - Review security advisories

5. **API Security**
   - Use HTTPS in production
   - Implement rate limiting (already enabled)
   - Add authentication to sensitive endpoints

### For Deployment

1. **Environment Configuration**
```bash
# Production settings
ENVIRONMENT=production
DEBUG=False
RATE_LIMIT_ENABLED=True
```

2. **Database Security**
```bash
# Use strong passwords
DB_PASSWORD=<strong_random_password>

# Restrict database access
DB_HOST=localhost  # Only accessible from backend
```

3. **HTTPS/TLS**
```bash
# Use reverse proxy (nginx) with SSL
# Let's Encrypt for free certificates
```

4. **Firewall Rules**
```bash
# Only expose necessary ports
# Backend: 8080 (via reverse proxy)
# Database: Not exposed externally
```

## Security Features

### Current Implementations

✅ **Rate Limiting**
- 60 requests/minute for general endpoints
- 30 requests/minute for task ingestion
- Configurable via environment variables

✅ **Security Headers**
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security
- Content-Security-Policy

✅ **Input Validation**
- Pydantic model validation
- Field length limits
- Type checking

✅ **CORS Protection**
- Configurable allowed origins
- Credentials support
- Restricted methods

✅ **GZip Compression**
- Reduces bandwidth usage
- Improves performance

✅ **Docker Security**
- Non-root user
- Minimal base images
- Health checks

### Planned Implementations

⏳ **Authentication**
- JWT token-based authentication
- OAuth2 integration
- API key management

⏳ **Audit Logging**
- Log all security events
- Track authentication attempts
- Monitor suspicious activity

⏳ **Data Encryption**
- Encrypt sensitive data at rest
- Use encrypted connections
- Secure backup encryption

## Dependency Security

### Python Dependencies

Check for vulnerabilities:
```bash
pip install safety
safety check --file requirements.txt
```

Update dependencies:
```bash
pip-review --auto
```

### JavaScript Dependencies

Check for vulnerabilities:
```bash
cd frontend
npm audit
npm audit fix
```

## Known Security Considerations

### Current Limitations

1. **In-Memory Task Storage**
   - Tasks are stored in memory (not persistent)
   - Production should use database storage
   - Implement data backup strategy

2. **No Authentication**
   - Current version has no authentication
   - Add authentication before production deployment
   - Use OAuth2 or JWT tokens

3. **API Keys in Environment**
   - Sensitive API keys in .env file
   - Consider using secret management (AWS Secrets Manager, HashiCorp Vault)
   - Rotate keys regularly

### Recommendations for Production

1. **Enable Authentication**
```python
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

2. **Use Secrets Manager**
```python
import boto3
secrets_manager = boto3.client('secretsmanager')
```

3. **Implement Audit Logging**
```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    return response
```

4. **Add HTTPS**
```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
}
```

## Compliance

### Data Privacy

- Follow GDPR guidelines for EU users
- Implement data retention policies
- Provide data export/deletion capabilities
- Anonymize sensitive data in logs

### Legal Data Handling

- Ensure secure transmission of legal documents
- Implement access controls
- Maintain audit trails
- Comply with legal professional privilege requirements

## Security Checklist for Production

- [ ] Enable HTTPS/TLS
- [ ] Implement authentication
- [ ] Configure firewall rules
- [ ] Use strong database passwords
- [ ] Enable audit logging
- [ ] Set up monitoring and alerts
- [ ] Configure backups
- [ ] Rotate API keys and secrets
- [ ] Review and update dependencies
- [ ] Conduct security audit
- [ ] Set DEBUG=False
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Use secret management system
- [ ] Implement data encryption
- [ ] Set up intrusion detection
- [ ] Configure security headers
- [ ] Test disaster recovery

## Contact

For security concerns, please contact the maintainers through:
- GitHub Security Advisories
- Email (check repository for contact information)

---

**Last Updated**: 2025-10-26
**Version**: 2.0.0
