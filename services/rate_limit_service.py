
from fastapi import HTTPException
from redis.asyncio import Redis


RATE_LIMIT_SCRIPT = """
for i = 1, #KEYS do
    local current = tonumber(redis.call("GET", KEYS[i]) or "0")
    local limit = tonumber(ARGV[(i - 1) * 2 + 1])

    if current >= limit then
        local ttl = redis.call("TTL", KEYS[i])
        if ttl < 1 then
            ttl = tonumber(ARGV[(i - 1) * 2 + 2])
        end
        return {0, i, ttl}
    end
end

for i = 1, #KEYS do
    local window = tonumber(ARGV[(i - 1) * 2 + 2])
    local count = redis.call("INCR", KEYS[i])

    if count == 1 then
        redis.call("EXPIRE", KEYS[i], window)
    end
end

return {1, 0, 0}
"""

def rate_limit_key(scope: str, identifier: str, period: str) -> str:
    return f"sql_agent:rate_limit:{scope}:{identifier}:{period}"

async def enforce_rate_limits(
    redis_client: Redis,
    limits: list[tuple[str, int, int]],
) -> None:
    """
    Atomically check and increment rate-limit counters.

    Each tuple contains (redis_key, maximum_requests, window_seconds).
    Rejected requests do not increment any of the supplied counters.
    """
    if not limits:
        return

    keys = [key for key, _, _ in limits]
    args = [
        value
        for _, maximum, window in limits
        for value in (maximum, window)
    ]

    result = await redis_client.eval(
        RATE_LIMIT_SCRIPT,
        len(keys),
        *keys,
        *args,
    )

    allowed = int(result[0])

    if not allowed:
        retry_after = max(1, int(result[2]))

        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )
