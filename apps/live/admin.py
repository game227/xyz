from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import LiveChatMessage, LiveSession


class LiveChatMessageInline(admin.TabularInline):
    model = LiveChatMessage
    extra = 0
    readonly_fields = ('user', 'text', 'is_from_teacher', 'created_at')
    can_delete = True


STATUS_COLORS = {
    'SCHEDULED': '#8a94a8',
    'LIVE': '#22c55e',
    'ENDED': '#64748b',
}


@admin.register(LiveSession)
class LiveSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'host', 'platform', 'status_badge', 'started_at', 'ended_at', 'watch_link')
    list_filter = ('status', 'platform')
    search_fields = ('title', 'host__username')
    autocomplete_fields = ('host',)
    inlines = [LiveChatMessageInline]
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    list_select_related = ('host',)

    @admin.display(description='Holat')
    def status_badge(self, obj):
        color = STATUS_COLORS.get(obj.status, '#8a94a8')
        return format_html(
            '<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
            'font-size:12px;font-weight:700;color:#0b1024;background:{}">{}</span>',
            color, obj.get_status_display(),
        )

    @admin.display(description='Havola')
    def watch_link(self, obj):
        try:
            url = reverse('live:watch')
        except Exception:
            return '—'
        return format_html('<a href="{}" target="_blank">Ko‘rish →</a>', url)


@admin.register(LiveChatMessage)
class LiveChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'user', 'text', 'is_from_teacher', 'created_at')
    list_filter = ('is_from_teacher', 'created_at')
    search_fields = ('text', 'user__username', 'session__title')
    autocomplete_fields = ('session', 'user')
