from django import forms
from django.contrib import admin

from apps.exam.constants import QUESTIONS_PER_LESSON

from .models import Answer, ExamAttempt, ExamAttemptQuestion, ExamSettings, Question


class AnswerInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        valid_forms = [
            f for f in self.forms
            if f.cleaned_data and not f.cleaned_data.get('DELETE', False)
        ]
        if len(valid_forms) < 4:
            raise forms.ValidationError("Har bir savolda kamida 4 ta javob bo'lishi kerak.")
        correct_count = sum(1 for f in valid_forms if f.cleaned_data.get('is_correct'))
        if correct_count != 1:
            raise forms.ValidationError(
                "Aynan bitta javob to'g'ri deb belgilanishi kerak (hozir: %d)." % correct_count
            )


class AnswerInline(admin.TabularInline):
    model = Answer
    formset = AnswerInlineFormSet
    extra = 4
    fields = ('text', 'is_correct', 'order')


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ('text', 'difficulty', 'is_active', 'created_by')
    show_change_link = True
    readonly_fields = ('created_by',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'short_text', 'lesson', 'topic', 'difficulty', 'is_active',
        'answer_count', 'created_by', 'created_at',
    )
    list_filter = ('is_active', 'difficulty', 'lesson__topic__module__course__subject', 'created_by')
    search_fields = ('text', 'explanation', 'lesson__title')
    ordering = ('lesson', 'id')
    list_select_related = ('lesson', 'topic', 'created_by')
    list_editable = ('is_active', 'difficulty')
    autocomplete_fields = ('lesson', 'topic', 'created_by')
    inlines = [AnswerInline]
    date_hierarchy = 'created_at'

    @admin.display(description='Savol')
    def short_text(self, obj):
        return obj.text[:70]

    @admin.display(description='Javoblar')
    def answer_count(self, obj):
        return obj.answers.count()


@admin.register(ExamSettings)
class ExamSettingsAdmin(admin.ModelAdmin):
    list_display = ('topic', 'question_count', 'passing_score', 'time_limit_minutes')
    search_fields = ('topic__title',)
    list_select_related = ('topic',)
    autocomplete_fields = ('topic',)
    list_editable = ('passing_score', 'time_limit_minutes')
    readonly_fields = ('question_count',)

    def save_model(self, request, obj, form, change):
        obj.question_count = QUESTIONS_PER_LESSON
        super().save_model(request, obj, form, change)


class ExamAttemptQuestionInline(admin.TabularInline):
    model = ExamAttemptQuestion
    extra = 0
    readonly_fields = ('question', 'selected_answer', 'is_correct', 'order')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'lesson', 'topic', 'score', 'is_passed', 'correct_answers',
        'total_questions', 'duration_seconds', 'created_at',
    )
    list_filter = ('is_passed', 'topic__module__course__subject', 'created_at')
    search_fields = ('user__username', 'user__email', 'lesson__title', 'topic__title')
    ordering = ('-created_at',)
    list_select_related = ('user', 'lesson', 'topic')
    readonly_fields = (
        'user', 'lesson', 'topic', 'total_questions', 'correct_answers', 'wrong_answers',
        'score', 'is_passed', 'duration_seconds', 'created_at', 'updated_at',
    )
    inlines = [ExamAttemptQuestionInline]
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False
