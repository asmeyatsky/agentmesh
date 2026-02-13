"""
Rate Limiting and API Versioning Middleware

Provides comprehensive rate limiting with Redis backend and API versioning.

Architectural Intent:
- Configurable rate limiting per tenant, user, or IP
- Multiple rate limiting strategies (sliding window, token bucket)
- API versioning with backward compatibility
- Rate limit headers for clients
- Distributed rate limiting support
"""

import time
import asyncio
from typing import Dict, Optional, Callable, Any, List
from dataclasses import dataclass
from enum import Enum
import json
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import hashlib
import redis.asyncio as redis
from loguru import logger


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies"""

    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""

    requests: int  # Max requests per window
    window_seconds: int  # Time window in seconds
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    key_extractor: Optional[Callable[[Request], str]] = None
    skip_successful_requests: bool = False  # Don't count successful requests
    headers: bool = True  # Add rate limit headers


@dataclass
class RateLimitInfo:
    """Rate limit information"""

    limit: int
    remaining: int
    reset_time: int
    retry_after: int
    strategy: RateLimitStrategy


class MemoryRateLimiter:
    """In-memory rate limiter for testing/small deployments"""

    def __init__(self):
        self.requests: Dict[str, List[float]] = {}

    async def is_allowed(self, key: str, config: RateLimitConfig) -> RateLimitInfo:
        now = time.time()

        if key not in self.requests:
            self.requests[key] = []

        # Remove old requests outside window
        window_start = now - config.window_seconds
        self.requests[key] = [
            req_time for req_time in self.requests[key] if req_time > window_start
        ]

        request_count = len(self.requests[key])

        if request_count >= config.requests:
            # Find oldest request to calculate reset time
            oldest_request = min(self.requests[key])
            reset_time = int(oldest_request + config.window_seconds)

            return RateLimitInfo(
                limit=config.requests,
                remaining=0,
                reset_time=reset_time,
                retry_after=config.window_seconds,
                strategy=config.strategy,
            )

        # Add current request
        self.requests[key].append(now)

        return RateLimitInfo(
            limit=config.requests,
            remaining=config.requests - request_count,
            reset_time=int(now + config.window_seconds),
            retry_after=max(1, config.window_seconds // request_count),
            strategy=config.strategy,
        )


class RedisRateLimiter:
    """Redis-based distributed rate limiter"""

    def __init__(self, redis_url: str):
        self.redis = None
        self.redis_url = redis_url

    async def _get_redis(self):
        """Get Redis connection"""
        if self.redis is None:
            self.redis = await redis.from_url(self.redis_url)
        return self.redis

    async def is_allowed(self, key: str, config: RateLimitConfig) -> RateLimitInfo:
        """Check if request is allowed using Redis sliding window"""
        redis_client = await self._get_redis()
        now = time.time()

        # Redis key for this rate limiter
        redis_key = f"rate_limit:{key}"

        # Use Redis pipeline for atomic operations
        pipe = redis_client.pipeline()

        try:
            # Remove old entries
            pipe.zremrangebyscore(redis_key, 0, now - config.window_seconds)

            # Add current request
            pipe.zadd(redis_key, {str(now): now})

            # Clean up old entries
            pipe.zremrangebyscore(redis_key, 0, now - config.window_seconds)

            # Get current count
            pipe.zcard(redis_key)

            # Set expiration
            pipe.expire(redis_key, config.window_seconds + 60)  # Extra buffer time

            results = await pipe.execute()
            request_count = results[3]  # zcard result

            if request_count >= config.requests:
                # Get oldest request for reset time
                oldest_results = await redis_client.zrange(
                    redis_key, 0, 1, withscores=True
                )
                if oldest_results:
                    reset_time = int(
                        float(oldest_results[0][1]) + config.window_seconds
                    )
                else:
                    reset_time = int(now + config.window_seconds)

                return RateLimitInfo(
                    limit=config.requests,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=config.window_seconds,
                    strategy=config.strategy,
                )

            # Calculate remaining requests
            remaining = max(0, config.requests - request_count)
            retry_after = max(1, config.window_seconds // max(1, request_count))

            return RateLimitInfo(
                limit=config.requests,
                remaining=remaining,
                reset_time=int(now + config.window_seconds),
                retry_after=retry_after,
                strategy=config.strategy,
            )

        except Exception as e:
            logger.error(f"Rate limiter Redis error: {e}")
            # Fail open - allow request but log error
            return RateLimitInfo(
                limit=config.requests,
                remaining=config.requests,
                reset_time=int(now + config.window_seconds),
                retry_after=config.window_seconds,
                strategy=config.strategy,
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""

    def __init__(
        self,
        app,
        config: RateLimitConfig,
        limiter_type: str = "memory",  # memory or redis
        redis_url: Optional[str] = None,
    ):
        super().__init__(app)
        self.config = config
        if limiter_type == "redis" and redis_url:
            self.limiter = RedisRateLimiter(redis_url)
        else:
            self.limiter = MemoryRateLimiter()

    def _get_key(self, request: Request) -> str:
        """Extract rate limit key from request"""
        if self.config.key_extractor:
            return self.config.key_extractor(request)

        # Default key extraction
        # Priority: API Key > User ID > IP Address
        key_parts = []

        # Try API key from header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            key_parts.append(f"api_key:{hashlib.md5(api_key.encode()).hexdigest()}")

        # Try user ID from header
        user_id = request.headers.get("X-User-ID")
        if user_id:
            key_parts.append(f"user:{user_id}")

        # Use IP address as fallback
        client_host = request.client.host if request.client else "unknown"
        key_parts.append(f"ip:{client_host}")

        # Add tenant if available
        if "tenant_id" in request.path_params:
            key_parts.append(f"tenant:{request.path_params['tenant_id']}")

        return ":".join(key_parts)

    def _create_rate_limit_response(self, rate_info: RateLimitInfo) -> Response:
        """Create rate limit response"""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "code": "RATE_LIMIT_EXCEEDED",
                "details": {
                    "limit": rate_info.limit,
                    "remaining": rate_info.remaining,
                    "reset_time": rate_info.reset_time,
                    "retry_after": rate_info.retry_after,
                    "strategy": rate_info.strategy,
                },
            },
        )

    def _add_rate_limit_headers(self, response: Response, rate_info: RateLimitInfo):
        """Add rate limit headers to response"""
        if not self.config.headers:
            return

        response.headers["X-RateLimit-Limit"] = str(rate_info.limit)
        response.headers["X-RateLimit-Remaining"] = str(rate_info.remaining)
        response.headers["X-RateLimit-Reset"] = str(rate_info.reset_time)
        response.headers["X-RateLimit-Retry-After"] = str(rate_info.retry_after)
        response.headers["X-RateLimit-Strategy"] = rate_info.strategy.value

    async def dispatch(self, request: Request, call_next: Callable):
        """Middleware dispatch method"""
        # Skip rate limiting for certain paths
        skip_paths = ["/health", "/metrics", "/docs", "/openapi.json", "/redoc"]
        if request.url.path in skip_paths:
            return await call_next(request)

        # Get rate limit key
        key = self._get_key(request)

        # Check rate limit
        rate_info = await self.limiter.is_allowed(key, self.config)

        if rate_info.remaining >= 0:
            # Rate limit exceeded
            logger.warning(f"Rate limit exceeded for key: {key}")
            response = self._create_rate_limit_response(rate_info)
            self._add_rate_limit_headers(response, rate_info)
            return response

        # Request allowed
        response = await call_next(request)
        self._add_rate_limit_headers(response, rate_info)

        return response


class APIVersionMiddleware(BaseHTTPMiddleware):
    """API versioning middleware"""

    def __init__(
        self,
        app,
        supported_versions: List[str] = ["1.0", "1.1"],
        default_version: str = "1.0",
        version_header: str = "X-API-Version",
        version_query_param: str = "api_version",
    ):
        super().__init__(app)
        self.supported_versions = supported_versions
        self.default_version = default_version
        self.version_header = version_header
        self.version_query_param = version_query_param

    def _get_requested_version(self, request: Request) -> str:
        """Get API version from client"""
        # Priority: Header > Query Param > Default
        version = request.headers.get(self.version_header)

        if not version:
            # Try query parameter
            query_params = dict(request.query_params)
            version = query_params.get(self.version_query_param)

        # Use default if no version specified
        if not version:
            version = self.default_version

        return version

    def _validate_version(self, version: str) -> bool:
        """Validate if version is supported"""
        return version in self.supported_versions

    async def dispatch(self, request: Request, call_next: Callable):
        """Middleware dispatch method"""
        # Skip versioning for certain paths
        skip_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
        if request.url.path in skip_paths:
            return await call_next(request)

        requested_version = self._get_requested_version(request)

        if not self._validate_version(requested_version):
            logger.warning(f"Unsupported API version requested: {requested_version}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Unsupported API version",
                    "code": "UNSUPPORTED_VERSION",
                    "details": {
                        "requested_version": requested_version,
                        "supported_versions": self.supported_versions,
                        "default_version": self.default_version,
                    },
                },
            )

        # Add version to request state
        request.state.api_version = requested_version

        response = await call_next(request)

        # Add version headers
        response.headers["X-API-Version"] = requested_version
        response.headers["X-API-Supported-Versions"] = ",".join(self.supported_versions)

        return response


# Rate limiting configuration presets
RATE_LIMIT_PRESETS = {
    "conservative": RateLimitConfig(
        requests=10, window_seconds=60, strategy=RateLimitStrategy.SLIDING_WINDOW
    ),
    "moderate": RateLimitConfig(
        requests=100, window_seconds=60, strategy=RateLimitStrategy.SLIDING_WINDOW
    ),
    "aggressive": RateLimitConfig(
        requests=1000, window_seconds=60, strategy=RateLimitStrategy.SLIDING_WINDOW
    ),
    "per_user": RateLimitConfig(
        requests=100,
        window_seconds=60,
        strategy=RateLimitStrategy.TOKEN_BUCKET,
        key_extractor=lambda req: req.headers.get("X-User-ID", f"ip:{req.client.host}"),
    ),
    "per_api_key": RateLimitConfig(
        requests=1000,
        window_seconds=60,
        strategy=RateLimitStrategy.TOKEN_BUCKET,
        key_extractor=lambda req: req.headers.get("X-API-Key", f"ip:{req.client.host}"),
    ),
    "premium": RateLimitConfig(
        requests=10000, window_seconds=60, strategy=RateLimitStrategy.LEAKY_BUCKET
    ),
}
