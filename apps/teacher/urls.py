from django.urls import path

from . import views

app_name = 'teacher'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/new/', views.subject_create, name='subject_create'),
    path('subjects/<int:pk>/edit/', views.subject_edit, name='subject_edit'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),
    path('courses/new/', views.course_create, name='course_create'),
    path('courses/<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),
    path('modules/new/', views.module_create, name='module_create'),
    path('modules/<int:pk>/edit/', views.module_edit, name='module_edit'),
    path('modules/<int:pk>/delete/', views.module_delete, name='module_delete'),

    path('topics/', views.topic_list, name='topic_list'),
    path('topics/new/', views.topic_create, name='topic_create'),
    path('topics/<int:pk>/', views.topic_detail, name='topic_detail'),
    path('topics/<int:pk>/edit/', views.topic_edit, name='topic_edit'),
    path('topics/<int:pk>/delete/', views.topic_delete, name='topic_delete'),
    path('topics/<int:topic_pk>/exam-settings/', views.exam_settings_edit, name='exam_settings'),

    path('lessons/', views.lesson_list, name='lesson_list'),
    path('lessons/new/', views.lesson_create, name='lesson_create'),
    path('topics/<int:topic_pk>/lessons/new/', views.lesson_create, name='lesson_create_for_topic'),
    path('lessons/<int:pk>/', views.lesson_detail, name='lesson_detail'),
    path('lessons/<int:pk>/edit/', views.lesson_edit, name='lesson_edit'),
    path('lessons/<int:pk>/delete/', views.lesson_delete, name='lesson_delete'),

    path('lessons/<int:lesson_pk>/questions/new/', views.question_create, name='question_create'),
    path('questions/<int:pk>/edit/', views.question_edit, name='question_edit'),
    path('questions/<int:pk>/delete/', views.question_delete, name='question_delete'),
]
