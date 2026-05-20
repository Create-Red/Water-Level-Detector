from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_sensor_data, name='add_sensor_data'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('latest/', views.get_latest_data, name='latest'),
    path('all/', views.get_all_data, name='all'),
    path('stats/', views.get_stats, name='stats'),
    path('api/water-level/', views.water_level_api, name='water_level_api'),
    path('api/latest/', views.get_latest, name='get_latest'),
    path('api/all/', views.get_all, name='get_all'),
    path('api/stats/', views.get_stats, name='get_stats'),
]