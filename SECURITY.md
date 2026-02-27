# 🔒 Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in nbpull, please report it
responsibly:

1. **Do NOT open a public issue**
2. Email **adityapatel0905@gmail.com** with details
3. Include steps to reproduce if possible
4. You will receive a response within 48 hours

## Security Design

nbpull is designed with security as a core principle:

- **Read-only by design** — the HTTP client only exposes `GET` methods.
  No `POST`, `PUT`, `PATCH`, or `DELETE` operations exist in the
  codebase.
- **No credential storage** — API tokens are loaded from environment
  variables or `.env` files, never persisted by the tool.
- **SSL verification on by default** — `NETBOX_VERIFY_SSL=true` is the
  default. Disabling it requires an explicit opt-out.
- **No shell injection surface** — all API parameters are passed as
  typed values through httpx, never interpolated into strings.

## Supported Versions

| Version | Supported |
|---|---|
| 0.1.x  | ✅ |
