
from dataclasses import dataclass
import time

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


@dataclass(frozen=True)
class RateLimitCheck:
    policy: RateLimitPolicy
    identifier: str

    @property
    def key(self) -> str:
        return self.policy.build_key(self.identifier)


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
        window_seconds=settings.AGENT_SESSION_RATE_WINDOW_SECONDS,
    ),
    "agent_per_session_day": RateLimitPolicy(
        name="agent_per_session_day",
        scope="session",
        period="day",
        limit=settings.AGENT_SESSION_RATE_LIMIT_PER_DAY,
        window_seconds=settings.AGENT_SESSION_DAY_WINDOW_SECONDS,
    ),
    "agent_per_ip_hour": RateLimitPolicy(
        name="agent_per_ip_hour",
        scope="ip",
        period="agent_hour",
        limit=settings.AGENT_IP_RATE_LIMIT_PER_HOUR,
        window_seconds=settings.AGENT_IP_RATE_WINDOW_SECONDS,
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

local results = {1, 0, 0}

for i = 1, #KEYS do
    local window = tonumber(ARGV[(i - 1) * 2 + 2])
    local count = redis.call("INCR", KEYS[i])

    if count == 1 then
        redis.call("EXPIRE", KEYS[i], window)
    end

    table.insert(results, count)
    table.insert(results, redis.call("TTL", KEYS[i]))
end

return results
"""

def get_rate_limit_policy(name: str) -> RateLimitPolicy:
    try:
        return RATE_LIMIT_POLICIES[name]
    except KeyError:
        raise ValueError(f"Unknown rate-limit policy: {name}") from None


def policy_limit(
    policy_name: str,
    identifier: str,
) -> RateLimitCheck:
    return RateLimitCheck(
        policy=get_rate_limit_policy(policy_name),
        identifier=identifier,
    )



async def enforce_rate_limits(
    redis_client: Redis,
    limits: list[RateLimitCheck],
) -> dict[str, str]:
    """
    Atomically check and increment all supplied rate-limit policies.
    Return quota headers for successful requests.
    Rejected requests do not increment any supplied counters.
    """
    if not limits:
        return {}

    keys = [item.key for item in limits]
    args = [
        value
        for item in limits
        for value in (
            item.policy.limit,
            item.policy.window_seconds,
        )
    ]

    result = await redis_client.eval(
        RATE_LIMIT_SCRIPT,
        len(keys),
        *keys,
        *args,
    )

    if not int(result[0]):
        rejected_index = int(result[1]) - 1
        retry_after = max(1, int(result[2]))

        rejected = limits[rejected_index]
        policy = rejected.policy
        reset_timestamp = int(time.time()) + retry_after

        raise HTTPException(
            status_code=429,
            detail={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Rate limit exceeded. Try again later.",
                    "policy": policy.name,
                    "scope": policy.scope,
                    "limit": policy.limit,
                    "remaining": 0,
                    "reset_after_seconds": retry_after,
                }
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(policy.limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_timestamp),
            },
        )

    # Successful Lua result: [1, 0, 0, count1, ttl1, count2, ttl2, ...]
    best_index = 0
    best_remaining = limits[0].policy.limit - int(result[3])
    best_ratio = best_remaining / limits[0].policy.limit

    for index, item in enumerate(limits[1:], start=1):
        result_index = 3 + index * 2
        count = int(result[result_index])
        remaining = max(0, item.policy.limit - count)
        ratio = remaining / item.policy.limit

        if ratio < best_ratio:
            best_index = index
            best_remaining = remaining
            best_ratio = ratio

    selected = limits[best_index]
    selected_result_index = 3 + best_index * 2
    ttl = max(1, int(result[selected_result_index + 1]))

    return {
        "X-RateLimit-Limit": str(selected.policy.limit),
        "X-RateLimit-Remaining": str(max(0, best_remaining)),
        "X-RateLimit-Reset": str(int(time.time()) + ttl),
    }
