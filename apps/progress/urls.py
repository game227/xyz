from django.urls import path

from . import views

app_name = 'progress'

urlpatterns = [
    path('lessons/<int:lesson_pk>/complete/', views.mark_lesson_complete_view, name='mark_lesson_complete'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
