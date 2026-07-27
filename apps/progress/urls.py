from django.urls import path

from . import views

app_name = 'progress'

urlpatterns = [
    path('lessons/<int:lesson_pk>/complete/', views.mark_lesson_complete_view, name='mark_lesson_complete'),
    path('lessons/<int:lesson_pk>/watch/', views.save_watch_progress_view, name='save_watch_progress'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
