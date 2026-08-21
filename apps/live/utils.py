"""YouTube havolalarini xavfsiz tahlil qilish uchun yordamchi funksiyalar."""
import re
from urllib.parse import parse_qs, urlparse

_ALLOWED_HOSTS = {
    'youtube.com', 'www.youtube.com', 'm.youtube.com',
    'youtube-nocookie.com', 'www.youtube-nocookie.com',
    'youtu.be',
}
_ID_RE = re.compile(r'^[a-zA-Z0-9_-]{6,20}$')


def extract_youtube_id(url):
    """Berilgan matndan YouTube video/efir ID sini ajratib oladi.

    Qo'llab-quvvatlanadigan formatlar:
    - https://www.youtube.com/watch?v=ID
    - https://www.youtube.com/live/ID
    - https://www.youtube.com/embed/ID
    - https://youtu.be/ID
    Noto'g'ri yoki tanilmagan manba bo'lsa — bo'sh satr qaytaradi.
    """
    if not url:
        return ''
    url = url.strip()
    if not url:
        return ''
    if '//' not in url:
        url = 'https://' + url

    try:
        parsed = urlparse(url)
    except ValueError:
        return ''

    host = (parsed.hostname or '').lower()
    if host not in _ALLOWED_HOSTS:
        return ''

    video_id = ''
    if host == 'youtu.be':
        video_id = parsed.path.lstrip('/').split('/')[0]
    else:
        path = parsed.path or ''
        if path == '/watch':
            qs = parse_qs(parsed.query or '')
            video_id = (qs.get('v') or [''])[0]
        else:
            for prefix in ('/live/', '/embed/', '/shorts/'):
                if path.startswith(prefix):
                    video_id = path[len(prefix):].split('/')[0]
                    break

    video_id = (video_id or '').strip()
    if not _ID_RE.match(video_id):
        return ''
    return video_id
