from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html

from .models import ContactChannel, Subscription, SubscriptionPricing, SubscriptionRequest
from .services import activate_subscription


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


@admin.register(SubscriptionPricing)
class SubscriptionPricingAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'price_uzs', 'duration_days', 'is_popular', 'is_active', 'order', 'updated_at',
    )
    list_editable = ('price_uzs', 'duration_days', 'is_popular', 'is_active', 'order')
    list_filter = ('is_active', 'is_popular')
    search_fields = ('title', 'description')
    ordering = ('order', 'duration_days')


@admin.register(SubscriptionRequest)
class SubscriptionRequestAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'phone', 'telegram', 'plan_days', 'status',
        'user_linked', 'user', 'created_at',
    )
    list_filter = ('status', 'plan_days', 'created_at')
    search_fields = ('full_name', 'phone', 'telegram', 'user__username')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_select_related = ('user',)
    actions = ['approve_and_activate', 'reject_requests']

    @admin.display(description='Foydalanuvchi', boolean=True)
    def user_linked(self, obj):
        return bool(obj.user_id)

    @admin.action(description='So‘rovni tasdiqlab obuna berish')
    def approve_and_activate(self, request, queryset):
        activated = 0
        skipped = 0
        for req in queryset.select_related('user'):
            if not req.user_id:
                skipped += 1
                continue
            activate_subscription(req.user, req.plan_days, request.user)
            req.status = SubscriptionRequest.Status.DONE
            req.save(update_fields=['status', 'updated_at'])
            activated += 1
        if activated:
            self.message_user(
                request,
                f'{activated} ta so‘rov tasdiqlandi va obuna berildi.',
                messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                f'{skipped} ta so‘rovda foydalanuvchi bog‘lanmagan — o‘tkazib yuborildi.',
                messages.WARNING,
            )

    @admin.action(description='Rad etish')
    def reject_requests(self, request, queryset):
        updated = queryset.update(status=SubscriptionRequest.Status.REJECTED)
        self.message_user(request, f'{updated} ta so‘rov rad etildi.')
