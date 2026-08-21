from django.contrib import admin
from django.utils.html import format_html

from .models import Founder, Notification, SiteSettings, StudentOfTheMonth


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'site_name', 'logo_preview', 'hero_video_active', 'updated_at')
    readonly_fields = ('created_at', 'updated_at', 'logo_preview', 'favicon_preview')
    fieldsets = (
        ('Brending', {
            'fields': (
                'site_name', 'tagline',
                'logo', 'logo_preview',
                'favicon', 'favicon_preview',
            ),
            'description': 'Logo navbar va admin paneldа chiqadi. PNG (shaffof fon) tavsiya etiladi.',
        }),
        ('Bosh sahifa video', {
            'fields': ('hero_video', 'hero_video_active'),
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='Logo')
    def logo_preview(self, obj):
        if obj and obj.logo:
            return format_html(
                '<img src="{}" style="max-height:48px;max-width:160px;object-fit:contain;'
                'background:#0b1024;padding:6px;border-radius:10px;" />',
                obj.logo.url,
            )
        return '—'

    @admin.display(description='Favicon')
    def favicon_preview(self, obj):
        if obj and obj.favicon:
            return format_html(
                '<img src="{}" style="height:32px;width:32px;object-fit:contain;" />',
                obj.favicon.url,
            )
        return '—'


@admin.register(Founder)
class FounderAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'role_title', 'order', 'is_active', 'photo_preview', 'updated_at')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('full_name', 'role_title', 'bio')
    ordering = ('order', 'id')
    readonly_fields = ('created_at', 'updated_at', 'photo_preview')
    fieldsets = (
        (None, {
            'fields': ('full_name', 'role_title', 'bio', 'photo', 'photo_preview'),
            'description': 'Qisqa bio kartochkada; to‘liq maʼlumot batafsil sahifada.',
        }),
        ("To‘liq profil", {
            'fields': ('full_bio', 'education', 'achievements'),
        }),
        ('Aloqa', {
            'fields': ('email', 'telegram', 'linkedin_url'),
        }),
        ('Ko‘rinish', {
            'fields': ('order', 'is_active', 'created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Rasm')
    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="height:48px;width:48px;object-fit:cover;border-radius:12px;" />',
                obj.photo.url,
            )
        return '—'


@admin.register(StudentOfTheMonth)
class StudentOfTheMonthAdmin(admin.ModelAdmin):
    list_display = ('user', 'year', 'month', 'is_published', 'highlight', 'created_at')
    list_filter = ('year', 'month', 'is_published')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'highlight')
    autocomplete_fields = ('user',)
    ordering = ('-year', '-month')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'ntype', 'title', 'is_read', 'created_at')
    list_filter = ('ntype', 'is_read')
    search_fields = ('user__username', 'title', 'message')
    autocomplete_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
