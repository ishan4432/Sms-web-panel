#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
exec 9>/tmp/bench.lock
flock -w 30 9 || { echo "another bench is running"; exit 1; }
sudo -v
PY=$PWD/.venv/bin/python; UV=$PWD/.venv/bin/uvicorn
PAT='tests.loadtest|uvicorn|gateway.worker|multiprocessing.spawn'
pkill -9 -f "$PAT"; sleep 2
redis-cli flushdb >/dev/null; sleep 1
rm -rf /tmp/prom && mkdir -p /tmp/prom
PROMETHEUS_MULTIPROC_DIR=/tmp/prom taskset -c 0-3 $UV gateway.api:app --port 8001 \
  --workers 4 --loop uvloop --http httptools --no-access-log --log-level warning > /tmp/api.log 2>&1 9>&- &
for i in $(seq 1 20); do curl -sf localhost:8001/health >/dev/null && break; sleep 1; done
curl -sf localhost:8001/health >/dev/null || { echo "API did not start"; cat /tmp/api.log; exit 1; }
for i in 1 2 3; do
  WORKER_CONCURRENCY=100 taskset -c 4-6 $PY -m gateway.worker > /tmp/fo_worker$i.log 2>&1 9>&- &
done
sleep 2
( sleep 20; redis-cli hset chaos provider_a_ms 400 >/dev/null; echo "INJECT 400ms into provider_a at $(date +%T)" > /tmp/fo_events.txt
  sleep 20; redis-cli hset chaos provider_a_ms 0 >/dev/null; echo "CLEAR at $(date +%T)" >> /tmp/fo_events.txt ) 9>&- &
taskset -c 8 $PY -m tests.loadtest 500 60 | tee /tmp/fo_load.txt
for i in $(seq 1 120); do
  [ "$(redis-cli llen sms:queue)" = "0" ] && [ "$(redis-cli zcard sms:retry)" = "0" ] && break
  sleep 1
done
sleep 5
pkill -9 -f "$PAT"
TAG=$(grep -o 'tag=[0-9]*' /tmp/fo_load.txt | tail -1 | cut -d= -f2)
echo "--- events"; cat /tmp/fo_events.txt
echo "--- breaker transitions"; grep -h BREAKER /tmp/fo_worker*.log | sort
echo "--- deliveries per provider"
cat /tmp/fo_worker*.log | grep DELIVERED | grep -oP 'via \K\S+' | sort | uniq -c
PG=$(sudo docker ps -qf name=postgres)
sudo docker exec "$PG" psql -U sms -d sms -c "select status, count(*) from messages where body like 'load-${TAG}-%' group by 1;"
