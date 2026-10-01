"""Accounts views.

Kept thin on purpose — form validation lives in forms.py, business logic
(auth logging) lives in services.py. Views only orchestrate.
"""
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy

from apps.core.utils import get_client_ip, is_rate_limited

from .forms import LoginForm, ProfileForm, RegisterForm
from .services import log_auth_event

# IP boshiga chegaralar — brute-force / spam-registratsiyaning oldini oladi.
LOGIN_ATTEMPT_LIMIT = 10
LOGIN_ATTEMPT_WINDOW_SECONDS = 15 * 60
REGISTER_LIMIT = 10
REGISTER_WINDOW_SECONDS = 60 * 60


def register_view(request):
    if request.user.is_authenticated:
        return redirect('progress:dashboard')

    if request.method == 'POST':
        if is_rate_limited(
            f'register:{get_client_ip(request)}', REGISTER_LIMIT, REGISTER_WINDOW_SECONDS
        ):
            messages.error(
                request, 'Juda ko‘p urinish. Bir soatdan so‘ng qayta urinib ko‘ring.'
            )
            return render(request, 'accounts/register.html', {'form': RegisterForm()})

        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            log_auth_event(request, user, 'register')
            messages.success(request, 'Ro‘yxatdan muvaffaqiyatli o‘tdingiz! Xush kelibsiz.')
            from apps.subscription.access import get_freemium_lesson
            free = get_freemium_lesson()
            if free:
                return redirect('education:lesson_detail', pk=free.pk)
            return redirect('progress:dashboard')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


class LoginView(DjangoLoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        ip_key = f'login:{get_client_ip(request)}'
        if is_rate_limited(ip_key, LOGIN_ATTEMPT_LIMIT, LOGIN_ATTEMPT_WINDOW_SECONDS):
            log_auth_event(request, None, 'login_rate_limited')
            messages.error(
                request,
                'Juda ko‘p noto‘g‘ri urinish. 15 daqiqadan so‘ng qayta urinib ko‘ring.',
            )
            return HttpResponse(status=429)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        log_auth_event(self.request, self.request.user, 'login')
        return response

    def form_invalid(self, form):
        log_auth_event(self.request, None, 'login_failed')
        messages.error(self.request, 'Login yoki parol noto‘g‘ri.')
        return super().form_invalid(form)

    def get_success_url(self):
        user = self.request.user
        next_url = self.get_redirect_url()
        if next_url:
            return next_url
        if user.is_teacher:
            return reverse('teacher:dashboard')
        if user.is_admin_role or user.is_superuser:
            return reverse('admin:index')
        return reverse('progress:dashboard')


class LogoutView(DjangoLogoutView):
    next_page = reverse_lazy('core:home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            log_auth_event(request, request.user, 'logout')
        return super().dispatch(request, *args, **kwargs)


def password_help_view(request):
    """Parol tiklash — email o‘rniga admin kontaktlari."""
    return render(request, 'accounts/password_reset.html')


def password_help_redirect(request, uidb64=None, token=None):
    """Eski email havolalari shu yerga yo‘naltiriladi."""
    return redirect('accounts:password_reset')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil yangilandi.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)

    from apps.core.services import get_leaderboard, get_student_of_the_month
    from apps.progress.services import get_dashboard_context
    from apps.subscription.services import get_active_subscription

    board = get_leaderboard(limit=100, period='month')
    my_rank = next((row for row in board['entries'] if row['user'].pk == request.user.pk), None)
    dash = get_dashboard_context(request.user) if request.user.is_student else {}

    return render(request, 'accounts/profile.html', {
        'form': form,
        'subscription': get_active_subscription(request.user),
        'my_rank': my_rank,
        'student_of_month': get_student_of_the_month(),
        'overall_progress': dash.get('overall_progress'),
        'completed_topics_count': dash.get('completed_topics_count'),
    })
