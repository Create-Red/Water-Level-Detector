from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_sensor_data, name='add_sensor_data'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('latest/', views.get_latest_data, name='latest'),
    path('all/', views.get_all_data, name='all'),
    path('stats/', views.get_stats, name='stats'),
]