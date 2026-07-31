from django.contrib import admin

from .models import LiveChatMessage, LiveSession


class LiveChatMessageInline(admin.TabularInline):
    model = LiveChatMessage
    extra = 0
    readonly_fields = ('user', 'text', 'is_from_teacher', 'created_at')
    can_delete = True


@admin.register(LiveSession)
class LiveSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'host', 'status', 'started_at', 'ended_at', 'created_at')
    list_filter = ('status',)
    search_fields = ('title', 'host__username')
    autocomplete_fields = ('host',)
    inlines = [LiveChatMessageInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(LiveChatMessage)
class LiveChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'user', 'text', 'is_from_teacher', 'created_at')
    list_filter = ('is_from_teacher', 'created_at')
    search_fields = ('text', 'user__username', 'session__title')
    autocomplete_fields = ('session', 'user')
