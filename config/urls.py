"""Root URL configuration.

Each phase appends its own app's urls.py here via include().
Kept intentionally short — routing detail lives inside each app.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('education/', include('apps.education.urls')),
    path('exam/', include('apps.exam.urls')),
    path('progress/', include('apps.progress.urls')),
    path('subscription/', include('apps.subscription.urls')),
    path('teacher/', include('apps.teacher.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'apps.core.views.error_404'
handler403 = 'apps.core.views.error_403'
handler500 = 'apps.core.views.error_500'
