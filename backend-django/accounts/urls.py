from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('google/', views.google, name='google'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.user_settings, name='user_settings'),
]
