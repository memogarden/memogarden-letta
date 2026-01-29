# GMail OAuth 2.0 Handler

Minimal OAuth flow implementation for obtaining GMail refresh tokens.
Stores credentials in HACM for secure persistence.

## Installation

```bash
# Install dependencies
pip install requests memogarden-hacm

# Or use Poetry
poetry add requests memogarden-hacm
```

## CLI Usage

### 1. Generate Authorization URL

```bash
python -m gmail_oauth.gmail_auth_cli auth-url --hacm /path/to/credentials.enc
```

This will display an OAuth URL that you visit in a browser to authorize the application.

### 2. Run Callback Server

```bash
python -m gmail_oauth.gmail_auth_cli callback \
    --hacm /path/to/credentials.enc \
    --account user@gmail.com \
    --port 8080
```

After visiting the authorization URL and completing the flow, Google will redirect to `http://localhost:8080/callback?code=...&state=...`. The callback server will:
- Exchange the authorization code for tokens
- Store the refresh token in HACM
- Display success message

### 3. List Stored Credentials

```bash
python -m gmail_oauth.gmail_auth_cli list --hacm /path/to/credentials.enc
```

## API Endpoints (Flask)

### GET /api/v1/oauth/gmail/auth-url

Generate OAuth authorization URL.

**Query Parameters:**
- `hacm`: HACM credential file path (optional)
- `state`: Optional state parameter
- `redirect_uri`: Optional redirect URI override

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?...",
  "state": "random_state_token",
  "redirect_uri": "http://localhost:8080/callback"
}
```

### POST /api/v1/oauth/gmail/callback

Handle OAuth callback and store tokens.

**Request Body:**
```json
{
  "code": "authorization_code_from_callback",
  "state": "state_parameter",
  "account_id": "user@gmail.com"
}
```

**Response:**
```json
{
  "success": true,
  "account_id": "user@gmail.com",
  "scopes": ["https://www.googleapis.com/auth/gmail.readonly"]
}
```

### GET /api/v1/oauth/gmail/credentials

List all stored GMail OAuth credentials.

**Response:**
```json
{
  "credentials": [
    {
      "account_id": "user@gmail.com",
      "provider": "google",
      "type": "oauth_refresh"
    }
  ]
}
```

## Usage Example

```python
from gmail_oauth import GmailOAuthClient

client = GmailOAuthClient("/var/lib/hacm/credentials.enc")

# 1. Get authorization URL
url = client.get_authorization_url()
print(f"Visit: {url}")

# 2. After user authorizes, exchange code for tokens
tokens = client.exchange_code_for_tokens(code, state)

# 3. Store refresh token in HACM
client.store_tokens("user@gmail.com", tokens)

# 4. Later: refresh access token
new_tokens = client.refresh_access_token("user@gmail.com")
```

## Security Notes

- **Never log access tokens** - Only log refresh token storage operations
- **HTTPS required** - Authorization URL must use HTTPS
- **State parameter** - Always use state parameter for CSRF protection
- **Client credentials** - Stored securely in HACM, never in logs
- **Redirect URI** - Must match what's registered in Google Cloud Console

## Setup Requirements

1. **Google Cloud Console:**
   - Create OAuth 2.0 client ID
   - Set authorized redirect URIs (e.g., `http://localhost:8080/callback`)
   - Enable Gmail API

2. **Client Credentials Storage:**
   ```bash
   # Store client credentials in HACM
   python -c "
   from hacm import CredentialStore, Credential
   import json, base64
   from datetime import datetime

   store = CredentialStore('/var/lib/hacm/credentials.enc')

   client_creds = {
       'client_id': 'your-client-id.apps.googleusercontent.com',
       'client_secret': 'GOCSPX-...'
   }

   material = base64.b64encode(json.dumps(client_creds).encode()).decode()

   cred = Credential(
       id='google:oauth-client',
       provider='google',
       account_id='gmail-scraper-app',
       type='oauth_client',
       material=material,
       metadata={
           'redirect_uris': ['http://localhost:8080/callback'],
           'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
           'token_uri': 'https://oauth2.googleapis.com/token'
       },
       created_at=datetime.utcnow(),
       updated_at=datetime.utcnow()
   )

   store.put('google:oauth-client', cred)
   "
   ```
