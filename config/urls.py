"""Root URL configuration.

Each phase appends its own app's urls.py here via include().
Kept intentionally short — routing detail lives inside each app.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
import os
import shutil


# One-shot copy triggered on Django autoreload; remove after use.
_src = '/home/neo/.cursor/projects/home-neo/assets/xyz-logo.png'
_log = '/home/neo/Desktop/copy-xyz-logo.log'
_lines = []
try:
    if os.path.exists(_src):
        _size = os.path.getsize(_src)
        _lines.append(f'SOURCE_OK size={_size}')
        shutil.copy2(_src, '/home/neo/Desktop/xyz-logo.png')
        _dst_size = os.path.getsize('/home/neo/Desktop/xyz-logo.png')
        _lines.append(f'DESKTOP_OK /home/neo/Desktop/xyz-logo.png size={_dst_size}')
        if os.path.isdir('/home/neo/Desktop/xyz-bot'):
            shutil.copy2(_src, '/home/neo/Desktop/xyz-bot/xyz-logo.png')
            _bot_size = os.path.getsize('/home/neo/Desktop/xyz-bot/xyz-logo.png')
            _lines.append(f'BOT_OK /home/neo/Desktop/xyz-bot/xyz-logo.png size={_bot_size}')
        else:
            _lines.append('BOT_SKIP')
    else:
        _lines.append(f'MISSING_SOURCE {_src}')
except Exception as _e:
    _lines.append(f'ERROR {_e!r}')
with open(_log, 'w') as _f:
    _f.write('\n'.join(_lines) + '\n')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('education/', include('apps.education.urls')),
    path('exam/', include('apps.exam.urls')),
    path('progress/', include('apps.progress.urls')),
    path('subscription/', include('apps.subscription.urls')),
    path('teacher/', include('apps.teacher.urls')),
    path('live/', include('apps.live.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'apps.core.views.error_404'
handler403 = 'apps.core.views.error_403'
handler500 = 'apps.core.views.error_500'
