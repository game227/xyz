from django.urls import path

from . import views

app_name = 'live'

urlpatterns = [
    path('', views.live_watch, name='watch'),
    path('host/', views.live_host, name='host'),
]
