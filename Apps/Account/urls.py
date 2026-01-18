from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = 'Account'

password_reset_pattern = [
    path('password-reset/', views.AsyncPasswordResetView.as_view(), name='password_reset'),

    # Email sent page
    path('password-reset/done/',auth_views.PasswordResetDoneView.as_view(
            template_name='Account/password_reset/password_reset_done.html'
        ), name='password_reset_done' ),

    # Link from email → password reset form
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
            template_name='Account/password_reset/password_reset_confirm.html',
            success_url=reverse_lazy('Account:password_reset_complete')),name='password_reset_confirm'),

    # Password successfully changed page
    path('reset/done/',auth_views.PasswordResetCompleteView.as_view(
            template_name='Account/password_reset/password_reset_complete.html'
            ),name='password_reset_complete'),
]
urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("send-otp/", views.SendOTPView.as_view(), name="send_otp"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("profile/", views.ProfileView.as_view(), name="profile"),

    *password_reset_pattern,

]
