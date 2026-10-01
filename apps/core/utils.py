"""Small, framework-level helpers reused by multiple apps.

Keep this file free of business logic — it's for generic, dependency-free
helpers only (IP extraction, logger factory, etc). Business logic belongs
in each app's own services.py.
"""
import logging

from django.core.cache import cache


def get_logger(name):
    """Return a module-level logger, so every app logs consistently."""
    return logging.getLogger(name)


def get_client_ip(request):
    """Best-effort client IP extraction (handles reverse-proxy/Nginx setups)."""
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def is_rate_limited(key, limit, period_seconds):
    """Fixed-window rate limiter backed by the default cache.

    Returns True (and does NOT count this call) once `key` has already hit
    `limit` calls within the current `period_seconds` window — callers
    should short-circuit on True. Otherwise records the call and returns
    False. Good enough for login/register throttling; not exact under
    heavy concurrency on LocMemCache, but Redis (CACHE_URL) makes it atomic.
    """
    cache_key = f'ratelimit:{key}'
    if cache.add(cache_key, 1, timeout=period_seconds):
        return False
    try:
        count = cache.incr(cache_key)
    except ValueError:
        cache.set(cache_key, 1, timeout=period_seconds)
        return False
    return count > limit
