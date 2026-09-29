import re, urllib.request

txt = urllib.request.urlopen("http://localhost:8001/metrics").read().decode()
b = []
for line in txt.splitlines():
    if not line.startswith("http_request_duration_seconds_bucket"):
        continue
    if 'path="/sms/send"' not in line or 'status="202"' not in line:
        continue
    le = re.search(r'le="([^"]+)"', line).group(1)
    b.append((float("inf") if le == "+Inf" else float(le), float(line.rsplit(" ", 1)[1])))
b.sort()
total = b[-1][1]


def q(p):
    target, prev_le, prev_c = p * total, 0.0, 0.0
    for le, c in b:
        if c >= target:
            if le == float("inf"):
                return prev_le
            frac = (target - prev_c) / (c - prev_c) if c > prev_c else 0
            return prev_le + (le - prev_le) * frac
        prev_le, prev_c = le, c


print(f"server-side requests={int(total)} (includes 2000 warmup)")
for p in (0.5, 0.95, 0.99):
    print(f"server-side p{int(p*100)} ~ {q(p)*1000:.1f} ms")
