from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('reyting/', views.rating, name='rating'),
    path('asoschi/<int:pk>/', views.founder_detail, name='founder_detail'),
    path('oqituvchi/<int:pk>/', views.teacher_detail, name='teacher_detail'),
]
