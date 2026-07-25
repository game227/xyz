from django.urls import path

from . import views

app_name = 'exam'

urlpatterns = [
    path('lesson/<int:lesson_pk>/start/', views.exam_start, name='exam_start'),
    path('lesson/<int:lesson_pk>/take/', views.exam_take, name='exam_take'),
    path('lesson/<int:lesson_pk>/submit/', views.exam_submit, name='exam_submit'),
    path('lesson/<int:lesson_pk>/history/', views.exam_history, name='exam_history'),
    path('attempt/<int:pk>/result/', views.exam_result, name='exam_result'),
]
