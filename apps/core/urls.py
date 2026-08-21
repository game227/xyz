from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('reyting/', views.rating, name='rating'),
    path('reyting/oqituvchilar/', views.teacher_rating_list, name='teacher_rating_list'),
    path('reyting/oqituvchi/<int:teacher_id>/baho/', views.rate_teacher, name='rate_teacher'),
    path('asoschi/<int:pk>/', views.founder_detail, name='founder_detail'),
    path('oqituvchi/<int:pk>/', views.teacher_detail, name='teacher_detail'),
    path('platforma-haqida/', views.about, name='about'),
    path('bildirishnomalar/', views.notifications_list, name='notifications'),
    path('bildirishnomalar/<int:pk>/oqish/', views.notification_read, name='notification_read'),
]
