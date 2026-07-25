"""Accounts services.

Business logic (beyond simple form.save()) lives here, not in views.
Currently: auth event logging, used by login/logout/register views.
"""
from apps.core.utils import get_client_ip, get_logger

logger = get_logger('accounts')


def log_auth_event(request, user, event):
    """Log a login/logout/register event with username + IP.

    event: one of 'register', 'login', 'logout', 'login_failed'
    """
    logger.info(
        '%s: user=%s ip=%s',
        event.upper(),
        getattr(user, 'username', 'unknown'),
        get_client_ip(request),
    )
