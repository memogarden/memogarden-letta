---
name: railway
description: Railway CLI usage for managing cloud deployments, services, databases, and environment variables. Covers project setup, deployment workflows, database operations, and common troubleshooting.
---

# Railway CLI Skill

This skill provides comprehensive guidance for using the Railway CLI to manage cloud deployments, databases, and services.

## When to Use This Skill

Use this skill when:
- Deploying applications to Railway cloud platform
- Managing Railway services and databases
- Configuring environment variables for deployed services
- Troubleshooting Railway deployments
- Setting up PostgreSQL or other database services
- Viewing logs and deployment status

## Core Concepts

### Project Structure

Railway projects are organized as:
- **Project:** Top-level container (e.g., "computing-tnl")
- **Environment:** Isolated deployments (e.g., "production", "staging")
- **Service:** Individual applications or databases
- **Deployment:** Specific instances of deployed code

### Multi-Service Architecture

Best practice for complex applications:
- Separate services for different components (e.g., JupyterHub + Dashboard)
- Each service has its own environment variables
- Services communicate via Railway's internal network
- Independent scaling and deployment

### Internal vs External URLs

- **Internal URLs:** `postgres.railway.internal:5432` - for service-to-service communication
- **External URLs:** `switchyard.proxy.rlwy.net:38021` - for public/local access
- Always use internal URLs when services communicate within Railway

### Cross-Service Communication

When services need to communicate (e.g., JupyterHub sending telemetry to Dashboard):

**For server-to-server communication:**
- Use internal Railway URLs: `https://service-name.railway.internal`
- Example: Python backend calling another Python backend's API

**For browser-to-server communication (JavaScript):**
- Use public Railway URLs: `https://service-production-XXX.railway.app`
- Example: JavaScript in browser sending fetch() requests to API
- Browsers can't access internal Railway URLs (they're outside the Railway network)

**Getting the right URL:**
```bash
# For server-to-server: Use RAILWAY_PRIVATE_DOMAIN
railway variables --service <SERVICE_ID> | grep RAILWAY_PRIVATE_DOMAIN

# For browser-to-server: Use RAILWAY_PUBLIC_DOMAIN
railway variables --service <SERVICE_ID> | grep RAILWAY_PUBLIC_DOMAIN
```

**Common mistake: Setting TELEMETRY_ENDPOINT on wrong service**
- ❌ Setting env var on dashboard service (doesn't help, JupyterHub can't read it)
- ✅ Setting env var on JupyterHub service (so it can write to config files for browser)

## Essential Commands

### 1. Project Status & Information

```bash
# Show current project status
railway status

# Show status in JSON format (useful for parsing)
railway status --json

# Check which project you're logged into
railway whoami

# Open project dashboard in browser
railway open
```

**Key Information from `railway status`:**
- Project ID and name
- Environment(s) and their IDs
- Service instances with deployment status
- Service IDs (useful for referencing services)

### 2. Environment Variables

```bash
# List all variables for the active service
railway variables

# List variables for a specific service
railway variables --service <SERVICE_ID>

# List variables for a specific environment
railway variables --environment production

# Set a single variable
railway variables --set "DATABASE_URL=postgres://..."

# Set multiple variables at once
railway variables --set "KEY1=value1" --set "KEY2=value2"

# Set variables without triggering a redeployment
railway variables --set "KEY=value" --skip-deploys

# Output in JSON format
railway variables --json

# Output in KEY=VALUE format (useful for export)
railway variables -k
```

**Best Practices:**
- Use `--skip-deploys` when setting multiple variables to avoid multiple redeployments
- Set all variables first, then redeploy manually
- Always set DATABASE_URL on application services, not database services

**Important Environment Variables (Railway-provided):**
- `RAILWAY_ENVIRONMENT` - Environment name
- `RAILWAY_ENVIRONMENT_ID` - Unique environment ID
- `RAILWAY_PROJECT_ID` - Project ID
- `RAILWAY_SERVICE_ID` - Service ID
- `RAILWAY_PUBLIC_DOMAIN` - Public domain URL
- `RAILWAY_PRIVATE_DOMAIN` - Internal domain for service communication

### 3. Database Operations

```bash
# Connect to PostgreSQL database via psql
railway connect Postgres

# Connect to a specific database service
railway connect <SERVICE_NAME>

# Get database connection details
railway variables --service <SERVICE_ID>
```

**PostgreSQL Variables Set by Railway:**
- `DATABASE_URL` - Internal connection string
- `DATABASE_PUBLIC_URL` - Public connection string
- `PGHOST` - Database host
- `PGPORT` - Port number
- `PGDATABASE` - Database name
- `PGUSER` - Database user
- `PGPASSWORD` - Database password
- `POSTGRES_USER` - Same as PGUSER
- `POSTGRES_PASSWORD` - Same as PGPASSWORD
- `POSTGRES_DB` - Same as PGDATABASE

**Database Connection Pattern:**
1. Create PostgreSQL service in Railway dashboard
2. Get service ID from `railway status --json`
3. Extract DATABASE_URL from service variables
4. Add DATABASE_URL to application service variables
5. Use internal URL for Railway deployments, public URL for local development

### 4. Deployment

```bash
# Deploy current directory
railway up

# Deploy without attaching to logs
railway up --detach

# Deploy to specific service
railway up --service <SERVICE_ID>

# Deploy to specific environment
railway up --environment production

# Stream build logs only (CI mode)
railway up --ci

# Redeploy latest deployment without changes
railway redeploy

# Redeploy specific service
railway redeploy --service <SERVICE_ID>
```

**Deployment Workflow:**
1. Make code changes
2. Set environment variables (with `--skip-deploys`)
3. Deploy: `railway up`
4. Monitor logs for errors
5. Verify deployment status

### 5. Logs & Monitoring

```bash
# View logs for a service (BLOCKING - use background mode in Claude Code)
railway logs

# View logs for specific deployment
railway logs <DEPLOYMENT_ID>

# Follow logs (tail mode)
railway logs --follow

# View logs for specific service
railway logs --service <SERVICE_ID>

# View deployment list
railway deployment list

# Get deployment status
railway service status
```

**IMPORTANT: `railway logs` is a blocking command**

When using `railway logs` in Claude Code or any interactive shell, the command will block indefinitely. **Always run it in background mode:**

```bash
# In Claude Code - always use run_in_background parameter
# This applies to any blocking command like logs, watch, tail, etc.

# Correct: Run in background (Claude Code will handle it)
railway logs --service <SERVICE_ID> &

# Alternative: Use timeout to prevent indefinite blocking
timeout 30s railway logs --service <SERVICE_ID>
```

**Why this matters:**
- `railway logs` streams logs in real-time and never exits
- Running it in foreground will consume the context window and block other operations
- Background mode allows you to read logs later via TaskOutput tool
- Use `railway deployment list` first to find recent deployment IDs if needed

### 6. Project Management

```bash
# Link current directory to Railway project
railway link

# Link to specific project
railway link <PROJECT_ID>

# Create new project
railway init

# List all projects
railway list

# Unlink current directory
railway unlink

# Remove most recent deployment
railway down
```

## Common Workflows

### Workflow 1: Setting Up a New Service

```bash
# 1. Create project in Railway dashboard
# 2. Link project locally
railway link

# 3. Set environment variables
railway variables --set "PORT=8000" --skip-deploys
railway variables --set "DATABASE_URL=..." --skip-deploys

# 4. Deploy
railway up

# 5. Get service URL
railway status | grep RAILWAY_PUBLIC_DOMAIN
```

### Workflow 2: Adding a Database to Existing Service

```bash
# 1. Create PostgreSQL service in Railway dashboard
# 2. Get database service ID
railway status --json | jq '.services.edges[] | select(.node.name == "Postgres") | .node.id'

# 3. Get database connection string
railway variables --service <SERVICE_ID> | grep DATABASE_URL

# 4. Add DATABASE_URL to application service
railway variables --set "DATABASE_URL=postgres://..." --skip-deploys

# 5. Redeploy application
railway redeploy
```

### Workflow 3: Local Development with Railway Database

Use Railway's PostgreSQL database while developing locally.

```bash
# 1. Get public database URL (for local development)
railway variables --service <POSTGRES_SERVICE_ID> | grep DATABASE_PUBLIC_URL

# Output example:
# DATABASE_PUBLIC_URL | postgresql://postgres:password@switchyard.proxy.rlwy.net:38021/railway

# 2. Add to .env file (NEVER commit .env with real credentials)
echo "DATABASE_URL=postgresql://postgres:password@switchyard.proxy.rlwy.net:38021/railway" >> .env

# 3. Verify .env is in .gitignore
grep ".env" .gitignore
# Should see: .env

# 4. Run tests or application locally
./run_tests.sh           # Run tests
python app.py               # Run application
./run.sh                    # Or use project's run script
```

**Important Notes:**
- Use `DATABASE_PUBLIC_URL` for local development (external/public URL)
- Use `DATABASE_URL` (internal) for Railway-to-Railway communication
- Check .env.example for required variable format
- Projects using psycopg2 CANNOT use SQLite - must use PostgreSQL
- Keep .env file private (contains credentials)

**Alternative: Get service ID first**
```bash
# Find Postgres service ID
railway status --json | jq -r '.services.edges[] | select(.node.name == "Postgres") | .node.id'

# Then get its public URL
railway variables --service <SERVICE_ID> | grep DATABASE_PUBLIC_URL
```

### Workflow 4: Updating Environment Variables

```bash
# 1. Set all variables without triggering deploys
railway variables --set "KEY1=value1" --skip-deploys
railway variables --set "KEY2=value2" --skip-deploys

# 2. Manually trigger redeploy
railway redeploy
```

### Workflow 5: Multi-Service Architecture

```bash
# 1. Create multiple services in Railway dashboard
# 2. Get service IDs from railway status
railway status --json

# 3. Configure each service's environment variables
railway variables --service <SERVICE_1_ID> --set "PORT=8000"
railway variables --service <SERVICE_2_ID> --set "PORT=3000"

# 4. Deploy services from their respective directories
cd jupyterhub
railway up --service <SERVICE_1_ID>

cd ../dashboard
railway up --service <SERVICE_2_ID>

# 5. Verify services can communicate via internal network
# (e.g., jupyter-telemetry.railway.internal)
```

### Workflow 6: Database Connection Troubleshooting

```bash
# 1. Check database is running
railway status --json | jq '.environments.edges[].node.serviceInstances.edges[] | select(.node.serviceName == "Postgres") | .node.latestDeployment.status'

# 2. Verify database variables are set
railway variables --service <SERVICE_ID> | grep PG

# 3. Test database connection
railway connect Postgres

# 4. Check application service has DATABASE_URL
railway variables --service <APP_SERVICE_ID> | grep DATABASE_URL

# 5. If using internal URL, verify it's correct format:
# postgres.railway.internal:5432 (not localhost or 127.0.0.1)
```

## Configuration Files

### railway.toml

Example configuration for multi-service deployment:

```toml
[build]
builder = "DOCKERFILE"

[deploy]
healthcheckPath = "/"
healthcheckTimeout = 300
```

**Common configurations:**
- `builder`: DOCKERFILE, NIXPACKS, or RAILPACK
- `healthcheckPath`: Health check endpoint
- `healthcheckTimeout`: Timeout in seconds
- `numReplicas`: Number of instances
- `restartPolicyType`: ON_FAILURE, ALWAYS, or NEVER

### Dockerfile for Railway

Key requirements:
- Expose port (default 8000, must match PORT env var)
- Health check endpoint at configured path
- Handle PORT environment variable

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

## Anti-Patterns & Troubleshooting

### Common Mistakes

1. **Using localhost instead of internal URLs**
   - ❌ `DATABASE_URL=postgres://localhost:5432/db`
   - ✅ `DATABASE_URL=postgres://postgres.railway.internal:5432/db`

2. **Triggering multiple deploys when setting variables**
   - ❌ `railway variables --set "KEY1=value1"`
   - ❌ `railway variables --set "KEY2=value2"`
   - ✅ `railway variables --set "KEY1=value1" --skip-deploys`
   - ✅ `railway variables --set "KEY2=value2" --skip-deploys`
   - ✅ `railway redeploy`

3. **Not setting PORT environment variable**
   - Railway automatically assigns PORT
   - Application must listen on PORT, not hardcoded port
   - Example (Python): `port = int(os.getenv("PORT", 8000))`

4. **Using service name instead of service ID**
   - Some commands require service ID, not name
   - Get ID from `railway status --json`

5. **Forgetting to add DATABASE_URL to application service**
   - Database service has DATABASE_URL automatically
   - Application service needs it added manually
   - Use internal URL for Railway deployments

6. **Using SQLite with psycopg2**
   - ❌ `DATABASE_URL=sqlite:///dashboard.db` with psycopg2 installed
   - ✅ `DATABASE_URL=postgresql://...` (psycopg2 requires PostgreSQL)
   - **Error:** `psycopg2.ProgrammingError: invalid dsn: missing "="`
   - **Fix:** Always use PostgreSQL URL when codebase uses psycopg2
   - **Why:** psycopg2 is PostgreSQL-specific and cannot connect to SQLite

7. **Running blocking commands in Claude Code**
   - ❌ `railway logs` in foreground (blocks indefinitely, consumes context)
   - ✅ `railway logs &` with `run_in_background=true`
   - ❌ `tail -f` or `watch` without timeout
   - ✅ `timeout 30s tail -n 100` or use background mode
   - **Why:** Blocking commands prevent other operations and consume token limit

### Troubleshooting Commands

```bash
# Service not starting?
railway logs --follow

# Can't connect to database?
railway connect Postgres
# Try \conninfo in psql to see connection details

# Environment variables not working?
railway variables --json | jq .

# Wrong service deploying?
railway status
# Verify service name and ID match

# Health check failing?
curl https://your-service.railway.app/health
# Check path matches railway.toml config
```

### Integration Debugging Workflow

When debugging issues between services (e.g., "Service A isn't receiving data from Service B"), follow this systematic approach:

**Phase 1: Verify Services Are Running**
```bash
# Check all services are healthy
railway status --json | jq '.environments.edges[].node.serviceInstances.edges[] | {service: .node.serviceName, status: .node.latestDeployment.status}'

# Check recent logs for each service
railway logs --service <SERVICE_A_ID> --tail 50  # Use background mode in Claude Code!
railway logs --service <SERVICE_B_ID> --tail 50
```

**Phase 2: Verify Environment Variables**
```bash
# Check if required environment variables are set
railway variables --service <SERVICE_ID> | grep TELEMETRY_ENDPOINT

# Verify database connections
railway variables --service <APP_SERVICE_ID> | grep DATABASE_URL
```

**Phase 3: Test API Endpoints Directly**
```bash
# Test if endpoint is accessible
curl -X POST https://your-service.railway.app/api/events \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# Test health endpoint
curl https://your-service.railway.app/health
```

**Phase 4: Add Debug Logging**
```bash
# Add console.log statements to JavaScript/frontend code
# Add logging to Python/backend code
# Redeploy and check logs again
```

**Phase 5: Check Database State**
```bash
# Connect to Railway database
railway connect Postgres

# Check if data is being written
SELECT COUNT(*) FROM events;
SELECT * FROM events ORDER BY timestamp DESC LIMIT 10;
```

**Common Integration Issues:**

1. **Environment variables not passed to JavaScript**
   - Problem: Server-side env vars don't automatically become browser JavaScript globals
   - Fix: Create a config file that sets `window.VARIABLE_NAME` during server initialization
   - Example: Generate `00-config.js` with `window.API_ENDPOINT = process.env.API_ENDPOINT`

2. **CORS errors**
   - Problem: Browser blocks requests from different domains
   - Fix: Add `flask_cors.CORS(app, supports_credentials=True)` in Flask
   - Verify: Check browser console for CORS errors

3. **Old server still running**
   - Problem: Code changes don't take effect because old server process is running
   - Fix: User must log out/stop old server, new spawn gets updated code
   - Verify: Check logs for timestamp of when server started

4. **Wrong service URL**
   - Problem: Using internal URL (`service.railway.internal`) from external code
   - Fix: Use public Railway URL (`https://service-production.railway.app`)
   - Verify: `railway status` shows `RAILWAY_PUBLIC_DOMAIN`

## Advanced Usage

### JSON Output Parsing

```bash
# Get all service IDs
railway status --json | jq -r '.services.edges[].node.id'

# Get Postgres service ID
railway status --json | jq -r '.services.edges[] | select(.node.name == "Postgres") | .node.id'

# Get all environment variables as JSON
railway variables --json

# Get specific variable value
railway variables --json | jq -r '.DATABASE_URL'
```

### Service Status Monitoring

```bash
# Check deployment status of all services
railway status --json | jq '.environments.edges[].node.serviceInstances.edges[] | {service: .node.serviceName, status: .node.latestDeployment.status}'

# Get deployment URLs
railway status --json | jq -r '.environments.edges[].node.serviceInstances.edges[].node.domains.serviceDomains[].domain'
```

### Database Backup & Restore

```bash
# Backup database to file
railway connect Postgres -c "pg_dump -U postgres railway > backup.sql"

# Restore from backup
railway connect Postgres < backup.sql

# Or use psql directly with connection string
psql $DATABASE_URL < backup.sql
```

## Integration with Development Workflow

### Before Deployment

1. **Test locally:**
   ```bash
   docker-compose up
   ```

2. **Run tests:**
   ```bash
   pytest
   ```

3. **Check environment variables:**
   ```bash
   railway variables | grep -v "RAILWAY_"
   ```

### During Deployment

1. **Deploy:**
   ```bash
   railway up
   ```

2. **Monitor logs:**
   ```bash
   railway logs --follow
   ```

3. **Verify health:**
   ```bash
   curl https://your-app.railway.app/
   ```

### After Deployment

1. **Check status:**
   ```bash
   railway status
   ```

2. **Test functionality:**
   ```bash
   # Run smoke tests against deployed service
   ```

3. **Monitor error logs:**
   ```bash
   railway logs | grep -i error
   ```

## Railway MCP Server

If using Railway MCP server with Claude Code:
- MCP provides access to Railway API
- Useful for automating workflows
- Can manage projects, services, deployments
- See [mcp.json](../.vscode/mcp.json) for configuration

## Resources

- **Railway Documentation:** https://docs.railway.app/
- **CLI Reference:** https://docs.railway.app/reference/cli
- **PostgreSQL on Railway:** https://docs.railway.app/guides/postgresql
- **Environment Variables:** https://docs.railway.app/reference/variables
- **Project Status:** [plans/status.md](../../plans/status.md)
- **Session 5 Database Reference:** [plans/session5-database-reference.md](../../plans/session5-database-reference.md)

---

**Note:** This skill is based on hands-on experience with Railway CLI for the jupyter-telemetry project. Adapt commands and workflows based on your specific project structure and requirements.
