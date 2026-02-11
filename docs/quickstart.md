# MemoGarden Quickstart Guide

**Last Updated:** 2026-02-11

Get started with MemoGarden in 5 minutes.

## What is MemoGarden?

MemoGarden is a personal memory system for financial transactions. It's not traditional budgeting software—it's a **belief-based transaction capture and reconciliation system** designed for both human users and AI agents.

**Key Concepts:**
- **Transactions Are Beliefs** - A transaction represents your understanding at the time of payment
- **Single Source of Truth** - All transactions flow through MemoGarden Core API
- **Immutable Memory** - Current state can change, but all changes are logged via deltas
- **Document-Centric** - Transactions link to immutable artifacts (emails, invoices, receipts)

---

## Quick Start (Development)

### 1. Install Dependencies

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install Python 3.13 (if not already installed)
sudo apt install python3.13 python3.13-venv
```

### 2. Clone Repositories

```bash
# System package (Soil + Core layers)
git clone https://github.com/memogarden/memogarden-system.git
cd memogarden-system
poetry install

# API package (Flask server)
cd ..
git clone https://github.com/memogarden/memogarden-api.git
cd memogarden-api
poetry install
```

### 3. Run the Server

```bash
cd memogarden-api
./scripts/run.sh
```

The API will be available at `http://localhost:5000`

---

## Your First Transaction

### Create an Admin User

```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "changeme",
    "is_admin": true
  }'
```

**Response:**
```json
{
  "user_id": "core_abc123...",
  "username": "admin",
  "is_admin": true
}
```

### Login and Get Token

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "changeme"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 2592000
}
```

Save the `access_token` for subsequent requests.

### Create Your First Transaction

```bash
export TOKEN="your_access_token_here"

curl -X POST http://localhost:5000/api/v1/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100.00,
    "currency": "SGD",
    "description": "Grocery shopping at NTUC"
  }'
```

**Response:**
```json
{
  "uuid": "core_def456...",
  "version": 1,
  "amount": 100.00,
  "currency": "SGD",
  "description": "Grocery shopping at NTUC",
  "created_at": "2026-02-11T10:30:00Z"
}
```

---

## Semantic API: The MemoGarden Way

While the REST API (`/api/v1/`) works for traditional CRUD operations, the **Semantic API** (`/mg`) is the primary interface for AI agents and advanced integrations.

### Create a Transaction (Semantic API)

```bash
curl -X POST http://localhost:5000/mg \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "op": "create",
    "type": "Transaction",
    "data": {
      "amount": 50.00,
      "currency": "SGD",
      "description": "Coffee at Cafe"
    }
  }'
```

**Response:**
```json
{
  "ok": true,
  "actor": "core_abc123...",
  "timestamp": "2026-02-11T10:35:00Z",
  "result": {
    "uuid": "core_ghi789...",
    "type": "Transaction",
    "version": 1,
    "hash": "sha256...",
    "created_at": "2026-02-11T10:35:00Z",
    "data": {
      "amount": 50.00,
      "currency": "SGD",
      "description": "Coffee at Cafe"
    }
  }
}
```

### Query Transactions

```bash
curl -X POST http://localhost:5000/mg \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "op": "query",
    "filters": {
      "type": "Transaction"
    },
    "limit": 10
  }'
```

### Search Transactions

```bash
curl -X POST http://localhost:5000/mg \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "op": "search",
    "query": "coffee",
    "target_type": "entity",
    "coverage": "content"
  }'
```

---

## Common Workflows

### Add an Invoice as Supporting Document

```bash
curl -X POST http://localhost:5000/mg \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "op": "add",
    "params": {
      "_type": "Artifact",
      "data": {
        "name": "Invoice_2025_02_11.pdf",
        "amount": 150.00,
        "vendor": "ABC Company"
      }
    }
  }'
```

### Link Transaction to Invoice

```bash
curl -X POST http://localhost:5000/mg \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "op": "link",
    "source": "core_transaction_uuid",
    "target": "soil_artifact_uuid",
    "kind": "cites",
    "metadata": {
      "purpose": "Supporting documentation"
    }
  }'
```

### Trace Transaction History

```bash
curl -X POST http://localhost:5000/mg \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "op": "track",
    "target": "core_transaction_uuid"
  }'
```

---

## Next Steps

1. **Read the API Documentation:** See [API Reference](api.md) for all endpoints
2. **Explore Semantic API:** See `/mg` endpoint for advanced operations
3. **Set Up Deployment:** See [Deployment Guide](deployment.md) for production setup
4. **Review RFCs:** See `plan/` directory for architecture decisions

---

## Quick Reference

### REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register user |
| `/api/v1/auth/login` | POST | Login and get token |
| `/api/v1/transactions` | POST | Create transaction |
| `/api/v1/transactions` | GET | List transactions |
| `/api/v1/transactions/{uuid}` | GET | Get single transaction |
| `/api/v1/transactions/{uuid}` | PATCH | Edit transaction |
| `/api/v1/transactions/{uuid}` | DELETE | Delete transaction |
| `/health` | GET | Health check |

### Semantic API Operations

| Operation | Description |
|-----------|-------------|
| `create` | Create entity |
| `get` | Get entity by UUID |
| `edit` | Edit entity |
| `forget` | Soft delete entity |
| `query` | Query with filters |
| `search` | Semantic search |
| `track` | Trace causal chain |
| `link` | Create relation |
| `explore` | Graph traversal |
| `add` | Add fact (Soil) |
| `amend` | Amend fact (Soil) |

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `MEMOGARDEN_SOIL_DB` | Soil database path | `./soil.db` |
| `MEMOGARDEN_CORE_DB` | Core database path | `./core.db` |
| `MEMOGARDEN_DATA_DIR` | Data directory | (current dir) |
| `FLASK_SECRET_KEY` | Session signing | (auto-generated) |
| `JWT_SECRET_KEY` | JWT signing | (auto-generated) |

---

## Need Help?

- **Documentation:** `docs/` directory
- **Issues:** https://github.com/memogarden/memogarden/issues
- **RFCs:** `plan/` directory
- **Tests:** `memogarden-api/tests/` for examples
