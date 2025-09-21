from django.urls import path
from . import views


urlpatterns = [
path('login/', views.login_view, name='login'),
path('logout/', views.logout_view, name='logout'),
path('', views.dashboard, name='dashboard'),


path('check-in/', views.check_in, name='check_in'),
path('check-out/', views.check_out, name='check_out'),


path('logs/', views.logs_list, name='logs_list'),


path('users/', views.users_list, name='users_list'),
path('users/create/', views.user_create, name='user_create'),

path("users/<int:user_id>/edit/", views.user_edit, name="user_edit"),
path("users/<int:user_id>/delete/", views.user_delete, name="user_delete"),
path("change-password/", views.change_password, name="change_password"),


]
