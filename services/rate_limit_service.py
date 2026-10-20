from dataclasses import dataclass

from fastapi import HTTPException
from redis.asyncio import Redis

from config import settings

@dataclass(frozen=True)
class RateLimitPolicy:
    name: str
    scope: str
    period: str
    limit: int
    window_seconds: int

    def build_key(self, identifier: str) -> str:
        return (
            f"sql_agent:rate_limit:"
            f"{self.scope}:{identifier}:{self.period}"
        )


RATE_LIMIT_POLICIES = {
    "session_create_per_ip": RateLimitPolicy(
        name="session_create_per_ip",
        scope="ip",
        period="session_create_hour",
        limit=settings.SESSION_CREATE_RATE_LIMIT,
        window_seconds=settings.SESSION_CREATE_RATE_WINDOW_SECONDS,
    ),
    "agent_per_session_minute": RateLimitPolicy(
        name="agent_per_session_minute",
        scope="session",
        period="minute",
        limit=settings.AGENT_SESSION_RATE_LIMIT_PER_MINUTE,
        window_seconds=60,
    ),
    "agent_per_session_day": RateLimitPolicy(
        name="agent_per_session_day",
        scope="session",
        period="day",
        limit=settings.AGENT_SESSION_RATE_LIMIT_PER_DAY,
        window_seconds=86400,
    ),
    "agent_per_ip_hour": RateLimitPolicy(
        name="agent_per_ip_hour",
        scope="ip",
        period="agent_hour",
        limit=settings.AGENT_IP_RATE_LIMIT_PER_HOUR,
        window_seconds=3600,
    ),
}

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


def rate_limit_key(
    scope: str,
    identifier: str,
    period: str,
) -> str:
    return f"sql_agent:rate_limit:{scope}:{identifier}:{period}"


def get_rate_limit_policy(name: str) -> RateLimitPolicy:
    try:
        return RATE_LIMIT_POLICIES[name]
    except KeyError:
        raise ValueError(f"Unknown rate-limit policy: {name}") from None


def policy_limit(
    policy_name: str,
    identifier: str,
) -> tuple[str, int, int]:
    policy = get_rate_limit_policy(policy_name)

    return (
        policy.build_key(identifier),
        policy.limit,
        policy.window_seconds,
    )


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
