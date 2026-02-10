#!/bin/bash
#
# MemoGarden Debugging Script
#
# Run this on the RPi to diagnose installation issues

set -euo pipefail

INSTALL_DIR="/opt/memogarden"
MEMOGARDEN_USER="memogarden"

echo "=================================="
echo "  MemoGarden Installation Debug"
echo "=================================="
echo ""

echo "=== 1. Poetry Configuration ==="
if [ -f "$INSTALL_DIR/.local/poetry/bin/poetry" ]; then
    echo "✓ Poetry installed at: $INSTALL_DIR/.local/poetry/bin/poetry"
    sudo -u "$MEMOGARDEN_USER" "$INSTALL_DIR/.local/poetry/bin/poetry" config --list
else
    echo "✗ Poetry NOT found at: $INSTALL_DIR/.local/poetry/bin/poetry"
fi
echo ""

echo "=== 2. Virtual Environment Location ==="
if [ -d "$INSTALL_DIR/memogarden-api/.venv" ]; then
    echo "✓ .venv exists at: $INSTALL_DIR/memogarden-api/.venv"
else
    echo "✗ .venv NOT found at: $INSTALL_DIR/memogarden-api/.venv"
fi

if [ -d "$INSTALL_DIR/.venv" ]; then
    echo "⚠ Old .venv exists at root: $INSTALL_DIR/.venv"
fi

if [ -d "$INSTALL_DIR/.cache/pypoetry/virtualenvs" ]; then
    echo "⚠ Poetry cache venvs exist at: $INSTALL_DIR/.cache/pypoetry/virtualenvs"
    ls -la "$INSTALL_DIR/.cache/pypoetry/virtualenvs"
fi
echo ""

echo "=== 3. Gunicorn Location ==="
echo "Checking for gunicorn in:"
echo "  - $INSTALL_DIR/memogarden-api/.venv/bin/gunicorn"
if [ -f "$INSTALL_DIR/memogarden-api/.venv/bin/gunicorn" ]; then
    echo "    ✓ FOUND"
    "$INSTALL_DIR/memogarden-api/.venv/bin/gunicorn" --version
else
    echo "    ✗ NOT FOUND"
fi

echo "  - $INSTALL_DIR/.venv/bin/gunicorn"
if [ -f "$INSTALL_DIR/.venv/bin/gunicorn" ]; then
    echo "    ✓ FOUND (old location)"
    "$INSTALL_DIR/.venv/bin/gunicorn" --version
else
    echo "    ✗ NOT FOUND"
fi

echo "  - Poetry cache location:"
find "$INSTALL_DIR/.cache/pypoetry/virtualenvs" -name "gunicorn" -type f 2>/dev/null || echo "    Not found in cache"
echo ""

echo "=== 4. systemd Service Configuration ==="
echo "ExecStart:"
grep "ExecStart=" /etc/systemd/system/memogarden.service || echo "  ✗ Service file not found"
echo ""
echo "Detected gunicorn for systemd:"
if [ -f "$INSTALL_DIR/memogarden-api/.venv/bin/gunicorn" ]; then
    echo "  → Will use: $INSTALL_DIR/memogarden-api/.venv/bin/gunicorn (in-project)"
elif [ -d "$INSTALL_DIR/.cache/pypoetry/virtualenvs" ]; then
    local cache_venv=$(find "$INSTALL_DIR/.cache/pypoetry/virtualenvs" -name "gunicorn" -type f 2>/dev/null | head -1)
    if [ -n "$cache_venv" ]; then
        echo "  → Will use: $cache_venv (Poetry cache)"
        echo "  → Bin dir: $(dirname "$cache_venv")"
    fi
fi
echo ""

echo "=== 5. Service Status ==="
systemctl status memogarden --no-pager -l || echo "  ✗ Service not found"
echo ""

echo "=== 6. Recent Error Logs ==="
echo "Application log (last 20 lines):"
if [ -f "/var/log/memogarden/memogarden.error" ]; then
    sudo tail -20 /var/log/memogarden/memogarden.error
else
    echo "  ✗ Log file not found"
fi
echo ""

echo "Systemd journal (last 20 lines):"
sudo journalctl -u memogarden -n 20 --no-pager || echo "  ✗ No journal entries"
echo ""

echo "=== 7. File Permissions ==="
echo "Important directories:"
ls -ld "$INSTALL_DIR"
ls -ld "$INSTALL_DIR/memogarden-api"
ls -ld "$INSTALL_DIR/.local/poetry" 2>/dev/null || echo "  Poetry dir not found"
echo ""

echo "=================================="
echo "  End of Debug Output"
echo "=================================="
