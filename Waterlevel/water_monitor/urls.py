from django.urls import path
from . import views

urlpatterns = [
    # ESP8266 endpoint
    path('water-level/', views.water_level_api, name='water_level_api'),
    
    # Existing sensor data endpoints
    path('add-sensor-data/', views.add_sensor_data, name='add_sensor_data'),
    path('latest/', views.get_latest_data, name='get_latest_data'),
    path('all/', views.get_all_data, name='get_all_data'),
    path('stats/', views.get_stats, name='get_stats'),
    
    # Authentication endpoints
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
]