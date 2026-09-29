#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"

echo "=== 1. where does gateway.provider actually load from ==="
.venv/bin/python -c "import gateway.provider as p; print('LOADED FROM:', p.__file__); print('has breaker:', hasattr(p, 'PRIMARY'))"

echo "=== 2. is this package installed elsewhere (shadowing the repo copy) ==="
INSTALLED=$(.venv/bin/pip show sms-web-panel 2>/dev/null | grep -i location || true)
echo "pip show: $INSTALLED"
find / -path "*/site-packages/gateway/provider.py" 2>/dev/null

echo "=== 3. worker.py patch status ==="
grep -n "DELIVERED" gateway/worker.py

echo "=== 4. force-fix: remove any shadow copy, ensure worker.py patch applied ==="
SHADOW=$(find / -path "*/site-packages/gateway/provider.py" 2>/dev/null | grep -v "^$(pwd)")
if [ -n "$SHADOW" ]; then
  echo "REMOVING shadow install: $SHADOW"
  pip uninstall -y sms-web-panel 2>/dev/null || true
  rm -rf "$(dirname "$SHADOW")"
fi

if ! grep -q "via %s" gateway/worker.py; then
  echo "worker.py missing patch, applying now"
  python3 - <<'PYEOF'
p = "gateway/worker.py"
s = open(p).read()
old = 'log.info("DELIVERED %s (retries=%d)", msg["id"][:8], msg["retry_count"])'
if old in s:
    s = s.replace(old, 'log.info("DELIVERED %s via %s (retries=%d)", msg["id"][:8], provider, msg["retry_count"])')
    open(p, "w").write(s)
    print("patched worker.py")
else:
    print("WARNING: could not find expected DELIVERED line to patch")
PYEOF
fi

find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete

echo "=== 5. re-verify import ==="
.venv/bin/python -c "import gateway.provider as p; print('LOADED FROM:', p.__file__); print('has breaker:', hasattr(p, 'PRIMARY'))"
grep -n "via %s" gateway/worker.py

echo "=== 6. rerun failover proof ==="
bash failover.sh 2>&1 | tee /tmp/failover_out2.txt
