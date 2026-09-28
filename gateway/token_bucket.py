import redis.asyncio as redis

# KEYS[1] = bucket key; ARGV = capacity, refill rate (tokens/sec), cost
LUA_TOKEN_BUCKET = """
local capacity = tonumber(ARGV[1])
local rate     = tonumber(ARGV[2])
local cost     = tonumber(ARGV[3])

local t = redis.call('TIME')
local now_ms = t[1] * 1000 + math.floor(t[2] / 1000)

local data   = redis.call('HMGET', KEYS[1], 'tokens', 'ts')
local tokens = tonumber(data[1])
local ts     = tonumber(data[2])

if tokens == nil then
  tokens = capacity
  ts = now_ms
end

local elapsed = math.max(0, now_ms - ts)
tokens = math.min(capacity, tokens + elapsed * rate / 1000)

local allowed = 0
local retry_after_ms = 0
if tokens >= cost then
  tokens = tokens - cost
  allowed = 1
else
  retry_after_ms = math.ceil((cost - tokens) * 1000 / rate)
end

redis.call('HSET', KEYS[1], 'tokens', tokens, 'ts', now_ms)
redis.call('PEXPIRE', KEYS[1], math.ceil(capacity / rate * 1000) * 2)

return {allowed, math.floor(tokens), retry_after_ms}
"""


class TokenBucket:
    def __init__(self, client: redis.Redis, capacity=2000, refill_rate=1000):
        self.client = client
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._script = client.register_script(LUA_TOKEN_BUCKET)

    async def allow(self, client_id: str, cost: int = 1):
        allowed, remaining, retry_ms = await self._script(
            keys=[f"rl:{client_id}"],
            args=[self.capacity, self.refill_rate, cost],
        )
        return bool(allowed), int(remaining), int(retry_ms)
