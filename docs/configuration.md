# ⚙️ Configuration

nbpull reads configuration from environment variables or a `.env`
file in your working directory.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `NETBOX_URL` | ✅ | — | Base URL of your NetBox instance |
| `NETBOX_TOKEN` | ✅ | — | API token (read-only recommended) |
| `NETBOX_PAGE_SIZE` | ❌ | `100` | Results per API page |
| `NETBOX_TIMEOUT` | ❌ | `30` | HTTP request timeout in seconds |
| `NETBOX_VERIFY_SSL` | ❌ | `true` | Verify TLS certificates |

## Getting an API Token

1. Log into your NetBox instance
2. Navigate to **your profile** → **API Tokens**
3. Click **Add a token**
4. **Uncheck "Write enabled"** for safety — nbpull only reads data
5. Copy the token value

## Using a `.env` File

```bash
cp .env.example .env
```

Then edit `.env`:

```dotenv
NETBOX_URL=https://netbox.example.com
NETBOX_TOKEN=your_read_only_token_here

# Optional overrides
# NETBOX_PAGE_SIZE=50
# NETBOX_TIMEOUT=60
# NETBOX_VERIFY_SSL=false
```

The `.env` file is loaded automatically when you run `nbpull`.
It is listed in `.gitignore` to prevent accidental credential leaks.

## SSL Verification

If your NetBox instance uses a self-signed certificate, set:

```dotenv
NETBOX_VERIFY_SSL=false
```

> ⚠️ **Warning:** Disabling SSL verification is not recommended for
> production environments.

## Precedence

Environment variables take precedence over `.env` file values. This
lets you override settings per-session:

```bash
NETBOX_URL=https://staging-netbox.example.com nbpull prefixes
```
