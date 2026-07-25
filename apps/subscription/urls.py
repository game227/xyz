from django.urls import path

from . import views

app_name = 'subscription'

urlpatterns = [
    path('info/', views.subscription_info_view, name='info'),
]
