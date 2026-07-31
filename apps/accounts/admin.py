from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import CustomUser, TeacherRating


@admin.register(TeacherRating)
class TeacherRatingAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'student', 'stars', 'lesson', 'created_at')
    list_filter = ('stars', 'created_at')
    search_fields = ('teacher__username', 'student__username', 'comment')
    autocomplete_fields = ('teacher', 'student', 'lesson')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 'get_full_name', 'email', 'role_badge', 'avatar_preview',
        'show_on_homepage', 'is_active', 'is_staff', 'created_at',
    )
    list_filter = ('role', 'is_active', 'is_staff', 'show_on_homepage', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined', 'avatar_preview')
    list_per_page = 40
    date_hierarchy = 'created_at'
    list_editable = ('show_on_homepage',)

    fieldsets = UserAdmin.fieldsets + (
        ("Platforma ma'lumotlari", {
            'fields': (
                'role', 'phone_number', 'avatar', 'avatar_preview',
                'specialty', 'bio', 'show_on_homepage', 'homepage_order',
            ),
            'description': 'O‘qituvchi: Avatar + to‘liq profil — bosh sahifa va batafsil sahifa.',
        }),
        ("To‘liq profil (o‘qituvchi)", {
            'fields': ('full_bio', 'education', 'achievements', 'telegram'),
        }),
        ('Vaqt belgilari', {'fields': ('created_at', 'updated_at')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Platforma ma'lumotlari", {'fields': ('email', 'role', 'phone_number')}),
    )

    @admin.display(description="To'liq ism")
    def get_full_name(self, obj):
        return obj.get_full_name() or '—'

    @admin.display(description='Rasm')
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="height:48px;width:48px;object-fit:cover;border-radius:12px;" />',
                obj.avatar.url,
            )
        return '—'

    @admin.display(description='Rol')
    def role_badge(self, obj):
        colors = {
            'ADMIN': '#0c1f1a',
            'TEACHER': '#1f8a64',
            'STUDENT': '#5f6f68',
            'MODERATOR': '#0b4f71',
        }
        color = colors.get(obj.role, '#5f6f68')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:999px;font-size:11px;">{}</span>',
            color,
            obj.get_role_display(),
        )

    actions = [
        'activate_subscription_30',
        'activate_subscription_90',
        'activate_subscription_180',
        'make_teacher',
        'make_student',
    ]

    def _activate_for_selected(self, request, queryset, days):
        from apps.subscription.services import activate_subscription
        for user in queryset:
            activate_subscription(user, duration_days=days, activated_by=request.user)
        self.message_user(request, f'{queryset.count()} foydalanuvchiga {days} kunlik obuna berildi.')

    @admin.action(description="Tanlanganlarga 30 kunlik obuna berish")
    def activate_subscription_30(self, request, queryset):
        self._activate_for_selected(request, queryset, 30)

    @admin.action(description="Tanlanganlarga 90 kunlik obuna berish")
    def activate_subscription_90(self, request, queryset):
        self._activate_for_selected(request, queryset, 90)

    @admin.action(description="Tanlanganlarga 180 kunlik obuna berish")
    def activate_subscription_180(self, request, queryset):
        self._activate_for_selected(request, queryset, 180)

    @admin.action(description="Tanlanganlarni TEACHER qilish")
    def make_teacher(self, request, queryset):
        updated = queryset.update(role=CustomUser.Role.TEACHER)
        self.message_user(request, f'{updated} foydalanuvchi o‘qituvchi qilindi.')

    @admin.action(description="Tanlanganlarni STUDENT qilish")
    def make_student(self, request, queryset):
        updated = queryset.update(role=CustomUser.Role.STUDENT)
        self.message_user(request, f'{updated} foydalanuvchi student qilindi.')
