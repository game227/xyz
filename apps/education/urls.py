from django.urls import path

from . import views

app_name = 'education'

urlpatterns = [
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/<int:pk>/', views.subject_detail, name='subject_detail'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('modules/<int:pk>/', views.module_detail, name='module_detail'),
    path('topics/<int:pk>/', views.topic_detail, name='topic_detail'),
    path('lessons/<int:pk>/', views.lesson_detail, name='lesson_detail'),
]
