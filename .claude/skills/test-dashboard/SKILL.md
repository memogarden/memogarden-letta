# Testing Dashboard API

This skill covers best practices for testing the Jupyter Telemetry Dashboard (Flask API).

## When to Use

Use this skill when:
- Testing the dashboard API endpoints locally
- Verifying database connectivity
- Sending test events to the API
- Querying events and sessions from the database
- Debugging API issues

## Local Development Setup

### Starting the Dashboard

```bash
cd dashboard
./run.sh                    # Default: port 5005, Railway database
./run.sh --port 8000         # Custom port
./run.sh -d "postgres://..." # Local database
```

### Prerequisites
- Poetry dependencies installed (`poetry install`)
- Railway PostgreSQL database accessible
- Port 5005 available (or custom port)

## API Endpoints

### 1. Health Check
```bash
curl http://localhost:5005/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-08T...",
  "database": "connected"
}
```

### 2. Create Event (POST /api/events)
```bash
curl -X POST http://localhost:5005/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2026-01-08T08:00:00.000Z",
    "session": "550e8400-e29b-41d4-a716-446655440000",
    "actor": "test@student.edu.sg",
    "verb": "opened",
    "object": {
      "type": "notebook",
      "id": "test-notebook.ipynb",
      "context": {"assignment_count": 5}
    }
  }'
```

**Expected response:**
```json
{
  "status": "success",
  "event_id": 1
}
```

### 3. Query Events (GET /api/events)
```bash
# Get all events
curl http://localhost:5005/api/events

# Get events for specific actor
curl http://localhost:5005/api/events?actor=test@student.edu.sg

# Get limited number of events
curl http://localhost:5005/api/events?limit=10
```

### 4. Query Sessions (GET /api/sessions)
```bash
curl http://localhost:5005/api/sessions
```

**Expected response:**
```json
{
  "sessions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "student_id": "test@student.edu.sg",
      "started_at": "2026-01-08T08:00:00+00:00",
      "last_activity_at": "2026-01-08T08:00:00+00:00",
      "ended_at": null,
      "notebook_id": "test-notebook.ipynb"
    }
  ],
  "count": 1
}
```

## Event Payload Examples

### opened (notebook)
```json
{
  "timestamp": "2026-01-08T08:00:00.000Z",
  "session": "550e8400-e29b-41d4-a716-446655440000",
  "actor": "student@email.com",
  "verb": "opened",
  "object": {
    "type": "notebook",
    "id": "notebook-name.ipynb",
    "context": {"assignment_count": 5}
  }
}
```

### executed (cell)
```json
{
  "timestamp": "2026-01-08T08:05:00.000Z",
  "session": "550e8400-e29b-41d4-a716-446655440000",
  "actor": "student@email.com",
  "verb": "executed",
  "object": {
    "type": "cell",
    "id": "abc123",
    "context": {
      "notebook": "notebook-name.ipynb",
      "section": "Introduction",
      "code_hash": "7f3a2b1c"
    }
  }
}
```

### completed (assignment)
```json
{
  "timestamp": "2026-01-08T08:10:00.000Z",
  "session": "550e8400-e29b-41d4-a716-446655440000",
  "actor": "student@email.com",
  "verb": "completed",
  "object": {
    "type": "assignment",
    "id": "recursion-base",
    "context": {
      "notebook": "pip-03-recursion.ipynb",
      "section": "Recursion basics"
    }
  },
  "result": {
    "success": true
  }
}
```

### failed (cell with error)
```json
{
  "timestamp": "2026-01-08T08:15:00.000Z",
  "session": "550e8400-e29b-41d4-a716-446655440000",
  "actor": "student@email.com",
  "verb": "failed",
  "object": {
    "type": "cell",
    "id": "def456",
    "context": {
      "notebook": "pip-03-recursion.ipynb",
      "section": "Recursion basics",
      "same_code": true
    }
  },
  "result": {
    "success": false,
    "error": "RecursionError",
    "message": "maximum recursion depth exceeded"
  }
}
```

## Common Testing Workflows

### Test Complete Session Flow
```bash
# 1. Start dashboard
cd dashboard && ./run.sh

# 2. Open notebook (creates session)
curl -X POST http://localhost:5005/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "session": "550e8400-e29b-41d4-a716-446655440000",
    "actor": "alice@student.edu.sg",
    "verb": "opened",
    "object": {
      "type": "notebook",
      "id": "pip-01-intro.ipynb",
      "context": {"assignment_count": 3}
    }
  }'

# 3. Execute cell
curl -X POST http://localhost:5005/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "session": "550e8400-e29b-41d4-a716-446655440000",
    "actor": "alice@student.edu.sg",
    "verb": "executed",
    "object": {
      "type": "cell",
      "id": "cell-1",
      "context": {
        "notebook": "pip-01-intro.ipynb",
        "section": "Introduction"
      }
    }
  }'

# 4. Verify events
curl http://localhost:5005/api/events?actor=alice@student.edu.sg

# 5. Verify session
curl http://localhost:5005/api/sessions
```

### Test Multiple Students
```bash
# Student 1
curl -X POST http://localhost:5005/api/events \
  -H "Content-Type: application/json" \
  -d '{"timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'","session":"s1","actor":"alice@nyjc.edu.sg","verb":"opened","object":{"type":"notebook","id":"pip-01.ipynb"}}'

# Student 2
curl -X POST http://localhost:5005/api/events \
  -H "Content-Type: application/json" \
  -d '{"timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'","session":"s2","actor":"bob@nyjc.edu.sg","verb":"opened","object":{"type":"notebook","id":"pip-01.ipynb"}}'

# Student 3
curl -X POST http://localhost:5005/api/events \
  -H "Content-Type: application/json" \
  -d '{"timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'","session":"s3","actor":"carol@nyjc.edu.sg","verb":"opened","object":{"type":"notebook","id":"pip-02.ipynb"}}'

# Check all active sessions
curl http://localhost:5005/api/sessions
```

## Database Verification

### Direct Database Queries
```bash
# Connect to Railway database
export DATABASE_URL="postgresql://postgres:umPcfDBdgDRyXQALSkuihlzTLOokLsSg@switchyard.proxy.rlwy.net:38021/railway"
psql $DATABASE_URL

# In psql:
SELECT id, actor, verb, object_type, object_id, timestamp FROM events ORDER BY timestamp DESC LIMIT 10;
SELECT * FROM sessions WHERE ended_at IS NULL;
SELECT actor, COUNT(*) as event_count FROM events GROUP BY actor;
```

## Debugging

### Check Flask Logs
The dashboard outputs logs to stdout showing:
- Incoming requests (method, path, status code)
- Database connection status
- Error messages

### Common Issues

**Port already in use:**
```bash
# Find process using port
lsof -i :5005
# Kill process
kill <PID>
# Or use different port
./run.sh --port 8000
```

**Database connection failed:**
```bash
# Check DATABASE_URL in run.sh
# Test connection manually
psql $DATABASE_URL
```

**Event validation failed:**
- Check JSON syntax (use jq to validate)
- Verify required fields: timestamp, session, actor, verb, object
- Ensure object has type and id
- Timestamp must be ISO 8601 format

## Performance Testing

### Load Test with Multiple Events
```bash
# Send 100 events
for i in {1..100}; do
  curl -s -X POST http://localhost:5005/api/events \
    -H "Content-Type: application/json" \
    -d "{
      \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%S.000Z)\",
      \"session\": \"550e8400-e29b-41d4-a716-446655440000\",
      \"actor\": \"student$i@edu.sg\",
      \"verb\": \"executed\",
      \"object\": {
        \"type\": \"cell\",
        \"id\": \"cell-$i\",
        \"context\": {\"notebook\": \"test.ipynb\"}
      }
    }" &
done
wait

# Check count
curl http://localhost:5005/api/events | jq '.count'
```

## Railway Deployment

### Development vs Production

**Local Development** (uses Flask dev server):
```bash
cd dashboard
./run.sh  # Runs: python app.py
```

**Railway Production** (uses gunicorn):
- Railway start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4`
- Set via Railway dashboard or `railway set`
- Requires gunicorn in pyproject.toml dependencies

### Railway Configuration

When deployed to Railway, the dashboard will:
- Use PORT environment variable (set by Railway, typically 8000)
- Use DATABASE_URL from Railway environment variables
- Be accessible at `https://dashboard-service.up.railway.app`

**Setting start command in Railway:**
```bash
# Via CLI
railway variables --set "PYTHON_VERSION=/usr/bin/python3.11"
railway set  # Then set start command to: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4
```

Or set via Railway dashboard UI (Settings → Start Command).

### Testing Railway Deployment

```bash
# Get Railway dashboard URL
railway status

# Check service health
curl https://your-dashboard-url.up.railway.app/health

# Send test event
curl -X POST https://your-dashboard-url.up.railway.app/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.000Z)'",
    "session": "test-session-id",
    "actor": "railway-test@edu.sg",
    "verb": "opened",
    "object": {"type": "notebook", "id": "test.ipynb"}
  }'

# Verify event persisted
curl https://your-dashboard-url.up.railway.app/api/events
```

## Resources

- Implementation Plan: [plans/jupyter-telemetry-implementation-plan.md](../../../jupyter-telemetry/plans/jupyter-telemetry-implementation-plan.md)
- PRD: [plans/jupyter-telemetry-prd.md](../../../jupyter-telemetry/plans/jupyter-telemetry-prd.md)
- Dashboard code: [dashboard/app.py](../../../jupyter-telemetry/dashboard/app.py)
