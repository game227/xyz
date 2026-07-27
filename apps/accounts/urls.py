from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('password-reset/', views.PasswordResetViewUz.as_view(), name='password_reset'),
    path('password-reset/done/', views.PasswordResetDoneViewUz.as_view(), name='password_reset_done'),
    path(
        'password-reset/<uidb64>/<token>/',
        views.PasswordResetConfirmViewUz.as_view(),
        name='password_reset_confirm',
    ),
    path(
        'password-reset/complete/',
        views.PasswordResetCompleteViewUz.as_view(),
        name='password_reset_complete',
    ),
]
