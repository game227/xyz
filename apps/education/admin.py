from django.contrib import admin
from django.db.models import Count

from apps.exam.constants import QUESTIONS_PER_LESSON
from apps.exam.models import Question

from .models import Course, Lesson, Module, Subject, Topic


class CourseInline(admin.TabularInline):
    model = Course
    extra = 0
    fields = ('title', 'order', 'is_active')
    show_change_link = True


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0
    fields = ('title', 'order', 'is_active')
    show_change_link = True


class TopicInline(admin.TabularInline):
    model = Topic
    extra = 0
    fields = ('title', 'difficulty_level', 'order', 'is_active')
    show_change_link = True


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ('title', 'video', 'duration_minutes', 'order', 'is_active', 'created_by')
    readonly_fields = ('created_by',)
    show_change_link = True


class LessonQuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ('text', 'difficulty', 'is_active')
    show_change_link = True
    verbose_name_plural = f'Test savollari (maksimal {QUESTIONS_PER_LESSON})'


@admin.action(description='Faollashtirish')
def make_active(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description='Nofaollashtirish')
def make_inactive(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'course_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    list_editable = ('is_active',)
    inlines = [CourseInline]
    actions = [make_active, make_inactive]
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('courses')

    @admin.display(description='Kurslar soni')
    def course_count(self, obj):
        return obj.courses.count()


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'order', 'is_active', 'created_at')
    list_filter = ('is_active', 'subject')
    search_fields = ('title', 'description')
    ordering = ('subject', 'order')
    list_select_related = ('subject',)
    list_editable = ('order', 'is_active')
    autocomplete_fields = ('subject',)
    inlines = [ModuleInline]
    actions = [make_active, make_inactive]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'is_active', 'created_at')
    list_filter = ('is_active', 'course__subject')
    search_fields = ('title', 'description')
    ordering = ('course', 'order')
    list_select_related = ('course', 'course__subject')
    list_editable = ('order', 'is_active')
    autocomplete_fields = ('course',)
    inlines = [TopicInline]
    actions = [make_active, make_inactive]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'difficulty_level', 'order', 'is_active', 'created_at')
    list_filter = ('is_active', 'difficulty_level', 'module__course__subject')
    search_fields = ('title', 'description')
    ordering = ('module', 'order')
    list_select_related = ('module',)
    list_editable = ('order', 'is_active', 'difficulty_level')
    autocomplete_fields = ('module',)
    inlines = [LessonInline]
    actions = [make_active, make_inactive]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'topic', 'duration_minutes', 'order', 'is_active',
        'question_bank', 'created_by', 'created_at',
    )
    list_filter = ('is_active', 'topic__module__course__subject', 'created_by')
    search_fields = ('title', 'description')
    ordering = ('topic', 'order')
    list_select_related = ('topic', 'created_by')
    list_editable = ('order', 'is_active', 'duration_minutes')
    autocomplete_fields = ('topic', 'created_by')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [LessonQuestionInline]
    actions = [make_active, make_inactive]
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _q_count=Count('questions', filter=Q(questions__is_active=True), distinct=True)
        )

    @admin.display(description='Test banki')
    def question_bank(self, obj):
        count = getattr(obj, '_q_count', obj.questions.filter(is_active=True).count())
        return f'{count}/{QUESTIONS_PER_LESSON}'
