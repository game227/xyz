from django.contrib import admin
from django.utils.html import format_html

from .models import Founder, StudentOfTheMonth


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
