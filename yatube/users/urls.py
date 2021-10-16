from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'users'

urlpatterns = [
    path(
        'logout/',
        LogoutView.as_view(template_name='users/logged_out.html'),
        name='logout'),
    path(
        'signup/',
        views.SignUp.as_view(template_name='users/signup.html'),
        name='signup'),
    path(
        'login/',
        LoginView.as_view(template_name='users/login.html'),
        name='login'),
    path(
        'password_reset_form/',
        TemplateView.as_view(template_name='users/password_reset_form.html'),
        name='password_reset_form'),
]