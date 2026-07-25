from django.contrib import admin
from django.utils.html import format_html

from .models import ContactChannel, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'start_date', 'end_date', 'duration_days',
        'status_badge', 'activated_by', 'created_at',
    )
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('user__username', 'user__email')
    ordering = ('-created_at',)
    list_select_related = ('user', 'activated_by')
    autocomplete_fields = ('user', 'activated_by')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    actions = ['mark_expired']

    @admin.display(description='Holat')
    def status_badge(self, obj):
        obj.refresh_status()
        color = '#1f8a64' if obj.status == Subscription.Status.ACTIVE else '#9a3412'
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:999px;font-size:11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    def save_model(self, request, obj, form, change):
        if not change and not obj.activated_by:
            obj.activated_by = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description='Tanlanganlarni EXPIRED qilish')
    def mark_expired(self, request, queryset):
        updated = queryset.update(status=Subscription.Status.EXPIRED)
        self.message_user(request, f'{updated} obuna muddati tugagan deb belgilandi.')


@admin.register(ContactChannel)
class ContactChannelAdmin(admin.ModelAdmin):
    list_display = ('label', 'channel_type', 'value', 'order', 'is_active', 'preview')
    list_editable = ('order', 'is_active')
    list_filter = ('channel_type', 'is_active')
    search_fields = ('label', 'value', 'note')
    ordering = ('order', 'id')

    @admin.display(description='Ko‘rinish')
    def preview(self, obj):
        href = obj.href
        if href:
            return format_html('<a href="{}" target="_blank" rel="noopener">{}</a>', href, obj.value)
        return obj.value
