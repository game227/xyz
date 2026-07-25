from django import forms
from django.forms import inlineformset_factory

from apps.education.models import Course, Lesson, Module, Subject, Topic
from apps.exam.constants import QUESTIONS_PER_LESSON
from apps.exam.models import Answer, ExamSettings, Question


def _style_fields(form):
    for name, field in form.fields.items():
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs['class'] = 'form-check-input'
        else:
            field.widget.attrs['class'] = 'form-control'


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ('name', 'description', 'image', 'is_active')
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_fields(self)


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('subject', 'title', 'description', 'image', 'order', 'is_active')
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subject'].queryset = Subject.objects.filter(is_active=True)
        _style_fields(self)


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ('course', 'title', 'description', 'order', 'is_active')
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.filter(is_active=True).select_related('subject')
        _style_fields(self)


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ('module', 'title', 'description', 'difficulty_level', 'order', 'is_active')
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['module'].queryset = Module.objects.filter(is_active=True).select_related(
            'course', 'course__subject'
        )
        _style_fields(self)


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = (
            'topic', 'title', 'description', 'video', 'pdf_material',
            'duration_minutes', 'order', 'is_active',
        )
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, topic_fixed=None, **kwargs):
        self.topic_fixed = topic_fixed
        super().__init__(*args, **kwargs)
        self.fields['topic'].queryset = Topic.objects.filter(is_active=True).select_related(
            'module', 'module__course'
        )
        if topic_fixed is not None:
            self.fields['topic'].initial = topic_fixed.pk
            self.fields['topic'].required = False
            self.fields['topic'].widget = forms.HiddenInput()
        if self.instance and self.instance.pk:
            self.fields['video'].required = False
        _style_fields(self)

    def clean_topic(self):
        if self.topic_fixed is not None:
            return self.topic_fixed
        return self.cleaned_data.get('topic')


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('text', 'explanation', 'difficulty', 'is_active')
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
            'explanation': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, lesson=None, **kwargs):
        self.lesson = lesson
        super().__init__(*args, **kwargs)
        _style_fields(self)

    def clean(self):
        cleaned = super().clean()
        lesson = self.lesson or (self.instance.lesson if self.instance.pk else None)
        if lesson and cleaned.get('is_active', True):
            count = Question.objects.filter(lesson=lesson, is_active=True)
            if self.instance.pk:
                count = count.exclude(pk=self.instance.pk)
            if count.count() >= QUESTIONS_PER_LESSON:
                raise forms.ValidationError(
                    f'Bu video uchun allaqachon {QUESTIONS_PER_LESSON} ta faol savol bor.'
                )
        return cleaned


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ('text', 'is_correct', 'order')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs['class'] = 'form-control'
        self.fields['order'].widget.attrs['class'] = 'form-control'
        self.fields['is_correct'].widget.attrs['class'] = 'form-check-input'


class BaseAnswerFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        valid = [
            form for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
        ]
        if len(valid) < 4:
            raise forms.ValidationError('Kamida 4 ta javob kerak.')
        correct = sum(1 for form in valid if form.cleaned_data.get('is_correct'))
        if correct != 1:
            raise forms.ValidationError("Aynan 1 ta javob to‘g‘ri bo‘lishi kerak.")


AnswerFormSet = inlineformset_factory(
    Question,
    Answer,
    form=AnswerForm,
    formset=BaseAnswerFormSet,
    extra=4,
    can_delete=True,
)


class ExamSettingsForm(forms.ModelForm):
    class Meta:
        model = ExamSettings
        fields = ('passing_score', 'time_limit_minutes')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_fields(self)
