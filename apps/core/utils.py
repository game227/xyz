"""Small, framework-level helpers reused by multiple apps.

Keep this file free of business logic — it's for generic, dependency-free
helpers only (IP extraction, logger factory, etc). Business logic belongs
in each app's own services.py.
"""
import logging


def get_logger(name):
    """Return a module-level logger, so every app logs consistently."""
    return logging.getLogger(name)


def get_client_ip(request):
    """Best-effort client IP extraction (handles reverse-proxy/Nginx setups)."""
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
