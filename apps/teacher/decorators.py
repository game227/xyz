"""Decorators for teacher / content-manager access."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def teacher_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not (user.is_authenticated and user.can_manage_content):
            messages.error(request, "Bu bo‘lim faqat o‘qituvchi va admin uchun.")
            return redirect('core:home')
        return view_func(request, *args, **kwargs)

    return _wrapped
