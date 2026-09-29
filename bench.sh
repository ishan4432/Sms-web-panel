#!/usr/bin/env bash
# Usage: [RATE=1000] [DUR=50] [PROBE=1] bash bench.sh full | api-only | burst
set -u
cd "$(dirname "$0")"
exec 9>/tmp/bench.lock
flock -w 30 9 || { echo "another bench.sh is running"; exit 1; }
sudo -v

PY=$PWD/.venv/bin/python
UV=$PWD/.venv/bin/uvicorn
MODE=${1:-full}
RATE=${RATE:-1000}
DUR=${DUR:-50}
PAT='tests.loadtest|uvicorn|gateway.worker|multiprocessing.spawn'

stop_all() { pkill -9 -f "$PAT"; sleep 2; }

stop_all
if pgrep -f "$PAT" >/dev/null; then
  echo "leftover processes:"; pgrep -af "$PAT"; exit 1
fi
rm -f /tmp/probe.txt

redis-cli config set slowlog-log-slower-than 2000 >/dev/null
redis-cli flushdb >/dev/null
sleep 1
[ "$(redis-cli llen sms:queue)" = "0" ] || { echo "queue not empty after flush"; exit 1; }
rm -rf /tmp/prom && mkdir -p /tmp/prom

PROMETHEUS_MULTIPROC_DIR=/tmp/prom taskset -c 0-3 $UV gateway.api:app --port 8001 \
  --workers 4 --loop uvloop --http httptools --no-access-log --log-level warning > /tmp/api.log 2>&1 9>&- &
for i in $(seq 1 20); do curl -sf localhost:8001/health >/dev/null && break; sleep 1; done
curl -sf localhost:8001/health >/dev/null || { echo "API did not start:"; cat /tmp/api.log; exit 1; }

if [ "$MODE" = burst ]; then
  taskset -c 8-9 $PY -m tests.loadtest 2500 2 1 | tee /tmp/run_burst.txt
  stop_all; exit 0
fi

if [ "$MODE" = full ]; then
  for i in 1 2 3; do
    WORKER_CONCURRENCY=100 taskset -c 4-6 $PY -m gateway.worker > /tmp/worker$i.log 2>&1 9>&- &
  done
  sleep 2
fi

taskset -c 8-9 $PY -m tests.loadtest 200 10 > /dev/null
sleep 3
redis-cli slowlog reset >/dev/null
( for i in $(seq 1 150); do echo "$(date +%T) queue=$(redis-cli llen sms:queue) retry=$(redis-cli zcard sms:retry)"; sleep 1; done > /tmp/queue_depth.log ) 9>&- &
QD=$!

taskset -c 8 $PY -m tests.loadtest $RATE $DUR > /tmp/run_$MODE.txt &
LT=$!
PR=""
if [ "${PROBE:-0}" = 1 ]; then
  # starts 1.2 s later so its tag differs, and ends early so it only samples loaded time
  ( sleep 1.2; taskset -c 9 $PY -m tests.loadtest 50 $((DUR-3)) 1 > /tmp/probe.txt 2>&1 ) 9>&- &
  PR=$!
fi
sleep 25
top -b -n 1 -o %CPU | head -15 > /tmp/top_$MODE.txt
wait $LT
[ -n "$PR" ] && wait $PR

$PY -m tests.hist_quantile >> /tmp/run_$MODE.txt
echo "queue length right after load: $(redis-cli llen sms:queue)" >> /tmp/run_$MODE.txt
redis-cli slowlog get 5 > /tmp/slowlog_$MODE.txt
echo "redis commands slower than 2 ms during load: $(redis-cli slowlog len)" >> /tmp/run_$MODE.txt

if [ "$MODE" = full ]; then
  for i in $(seq 1 120); do
    [ "$(redis-cli llen sms:queue)" = "0" ] && [ "$(redis-cli zcard sms:retry)" = "0" ] && break
    sleep 1
  done
  echo "seconds to drain after load ended: $i" >> /tmp/run_$MODE.txt
  sleep 5
fi
kill $QD 2>/dev/null
stop_all

TAG=$(grep -o 'tag=[0-9]*' /tmp/run_$MODE.txt | tail -1 | cut -d= -f2)
cat /tmp/run_$MODE.txt
[ -f /tmp/probe.txt ] && { echo "--- probe: 50 req/s, separate process and core"; grep -E "status codes|latency ms" /tmp/probe.txt; }
echo "--- redis slowlog (worst 5 commands over 2 ms)"; cat /tmp/slowlog_$MODE.txt
echo "--- queue depth (every 5 s)"; awk 'NR%5==1' /tmp/queue_depth.log
echo "--- top, mid-run"; cat /tmp/top_$MODE.txt
echo "SQL tag: $TAG"

if [ "$MODE" = full ]; then
  PG=$(sudo docker ps -qf name=postgres)
  sudo docker exec "$PG" psql -U sms -d sms -c "select status, count(*) from messages where body like 'load-${TAG}-%' group by 1;"
  sudo docker exec "$PG" psql -U sms -d sms -c "select count(*) as total, percentile_cont(0.50) within group (order by extract(epoch from finished_at - created_at)) as p50_s, percentile_cont(0.99) within group (order by extract(epoch from finished_at - created_at)) as p99_s from messages where body like 'load-${TAG}-%';"
fi
