from django.contrib import admin

from .models import LessonProgress, TopicProgress


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'is_completed', 'completed_at', 'updated_at')
    list_filter = ('is_completed',)
    search_fields = ('user__username', 'lesson__title')
    list_select_related = ('user', 'lesson')
    autocomplete_fields = ('user', 'lesson')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'updated_at'


@admin.register(TopicProgress)
class TopicProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'is_completed', 'best_score', 'completed_at')
    list_filter = ('is_completed', 'topic__module__course__subject')
    search_fields = ('user__username', 'topic__title')
    list_select_related = ('user', 'topic')
    autocomplete_fields = ('user', 'topic')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'updated_at'
