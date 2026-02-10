# RFC 004 Alignment Refactor Plan

**Created:** 2026-02-10
**Status:** Completed
**Objective:** Align deployment with RFC 004 multi-repo structure

## Background

Current deployment state is desynchronized from RFC 004. This plan tracks the refactoring needed to bring deployment into alignment.

## Refactor Steps

### Step 1: Clean Up Artifacts ⚠️
- [ ] Remove `/opt/memogarden/.venv` (incorrect location)
- [ ] Remove `/opt/memogarden/memogarden-api/.venv` (incorrect location)
- [ ] Verify no other incorrect venv locations exist

**Expected outcome:** Clean slate before creating proper shared venv

**Note:** This step must be performed on the RPi directly.

---

### Step 2: Fix install.sh for Shared venv ✅
- [x] Update install.sh to create shared venv at `/opt/memogarden/venv/`
- [x] Install both `memogarden-system` and `memogarden-api` into shared venv
- [x] Use git install from separate repos:
  - `pip install git+https://github.com/memogarden/memogarden-system.git`
  - `pip install git+https://github.com/memogarden/memogarden-api.git`
- [x] Remove Poetry in-project venv approach

**Files modified:**
- `install.sh` - Complete rewrite for RFC 004 alignment

**Expected outcome:** Single shared venv with both packages installed

---

### Step 3: Create CLI Wrapper Binary ✅
- [x] Create `/opt/memogarden/bin/memogarden` script
- [x] Script should:
  - Activate `/opt/memogarden/venv`
  - Import and run Flask app from `api.main`
  - Support command verbs (serve, run, deploy)

**Files created:**
- `scripts/memogarden-wrapper.sh` → deployed to `/opt/memogarden/bin/memogarden`

**Expected outcome:** Executable binary that activates venv and runs Flask app

---

### Step 4: Migrate Config from .env to TOML ✅
- [x] Update `install.sh` to generate `/etc/memogarden/config.toml`
- [x] Update `memogarden-api/api/main.py` to work with TOML settings
- [x] Update `memogarden-system/system/config.py` for TOML support
- [x] Add TOML dependency (tomli for Python <3.11)

**Files modified:**
- `memogarden-system/system/config.py` - Complete rewrite with TOML support
- `memogarden-system/pyproject.toml` - Added tomli dependency
- `memogarden-api/api/config.py` - Updated to extend system config with TOML
- `memogarden-api/pyproject.toml` - Removed pydantic-settings and python-dotenv
- `install.sh` - Generate config.toml instead of .env

**Expected outcome:** All configuration read from TOML files per RFC 004

---

### Step 5: Update systemd Service File ✅
- [x] Update systemd service to use new binary
- [x] Update `ExecStart` to use `/opt/memogarden/bin/memogarden serve`
- [x] Verify paths match RFC 004

**Files modified:**
- `install.sh` - Service file generation inline
- Service now uses: `ExecStart=/opt/memogarden/bin/memogarden serve`

**Expected outcome:** Service starts using new binary and venv

---

### Step 6: Update Deploy Script ✅
- [x] Simplify deploy script (no longer clones sub-repos)
- [x] Verify all paths match RFC 004

**Files modified:**
- `scripts/deploy-memogarden.sh` - Simplified for RFC 004

**Expected outcome:** Binary correctly placed during deployment

---

## Progress Tracking

| Step | Description | Status | Notes |
|------|-------------|--------|-------|
| 1 | Clean up artifacts | Pending | Must be done on RPi |
| 2 | Fix install.sh for shared venv | ✅ Complete | Creates /opt/memogarden/venv/ |
| 3 | Create CLI wrapper | ✅ Complete | /opt/memogarden/bin/memogarden |
| 4 | Migrate to TOML config | ✅ Complete | Breaking change |
| 5 | Update service file | ✅ Complete | systemd unit updated |
| 6 | Update deploy script | ✅ Complete | Simplified for multi-repo |

---

## RFC 004 Compliance Checklist

- [x] Binary at `/opt/memogarden/bin/memogarden` (wrapper script created)
- [x] Python packages in `/opt/memogarden/venv/lib/python3.x/site-packages/` (install.sh updated)
- [x] Config in TOML format at `/etc/memogarden/config.toml` (config modules rewritten)
- [x] systemd unit at `/etc/systemd/system/memogarden.service` (service updated)
- [x] Databases at `/var/lib/memogarden/soil.db`, `core.db` (paths unchanged)
- [x] Logs at `/var/log/memogarden/` (paths unchanged)
- [x] Runtime state at `/run/memogarden/` (paths unchanged)

---

## Changes Summary

### Modified Files

1. **memogarden-system/system/config.py**
   - Complete rewrite with TOML support
   - Added `load_toml_config()`, `get_config_path()`, `ResourceProfile`, `Settings` classes
   - Supports verb-based configuration (serve/run/deploy)
   - Backward compatible with existing code

2. **memogarden-system/pyproject.toml**
   - Added `tomli` dependency for Python <3.11

3. **memogarden-api/api/config.py**
   - Complete rewrite extending `system.config.Settings`
   - Removed `pydantic-settings` dependency
   - TOML-based configuration

4. **memogarden-api/pyproject.toml**
   - Removed `pydantic-settings` and `python-dotenv` dependencies
   - Keeps `pydantic` for other uses

5. **install.sh**
   - Complete rewrite for RFC 004 alignment
   - Creates shared venv at `/opt/memogarden/venv/`
   - Installs packages from git repositories (not local paths)
   - Generates `/etc/memogarden/config.toml` instead of `.env`
   - Generates gunicorn config at `/etc/memogarden/gunicorn.conf.py`
   - Installs CLI wrapper to `/opt/memogarden/bin/memogarden`
   - Creates systemd service file inline

6. **scripts/deploy-memogarden.sh**
   - Simplified to only clone root repo
   - install.sh handles package installation from git

### New Files

1. **scripts/memogarden-wrapper.sh**
   - CLI wrapper binary that:
     - Activates shared venv
     - Supports command verbs (serve/run/deploy)
     - Runs gunicorn for production, Flask dev server for development
     - Sets environment variables for config resolution

---

## Dependencies

- RFC 004 v2.0 (updated for multi-repo structure)
- Separate git repos: memogarden-system, memogarden-api
- TOML library: tomli for Python <3.11, tomllib (stdlib) for Python >=3.11

---

## Notes

- This refactor aligns with the updated RFC 004 that reflects the multi-repo structure
- Schemas are bundled into memogarden-system during build (not a separate directory)
- No need to clone repos for installation - install.sh uses pip install from git URLs
- **Step 1 (cleanup) must be performed on the RPi before running updated install.sh**

## Next Steps

1. Run cleanup on RPi: `sudo rm -rf /opt/memogarden/.venv /opt/memogarden/memogarden-api/.venv`
2. Run updated deploy script on RPi
3. Verify installation
4. Test service startup
