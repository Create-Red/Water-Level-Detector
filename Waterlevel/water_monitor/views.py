from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import WaterSensorData
from .serializers import WaterSensorDataSerializer
from django.db.models import Avg, Max, Min
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import WaterLevelReading
import json

# ==================== SENSOR DATA ENDPOINTS ====================

@api_view(['POST'])
def add_sensor_data(request):
    serializer = WaterSensorDataSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"status": "success", "data": serializer.data}, status=201)
    return Response(serializer.errors, status=400)

@api_view(['GET'])
def get_latest_data(request):
    latest = WaterLevelReading.objects.last()
    if latest:
        data = {
            'id': latest.id,
            'water_level': latest.water_level,
            'timestamp': latest.timestamp,
            'device_id': latest.device_id,
            'battery_level': latest.battery_level,
            'signal_strength': latest.signal_strength,
        }
        return Response(data)
    return Response({"error": "No data found"}, status=404)

@api_view(['GET'])
def get_all_data(request):
    data = WaterLevelReading.objects.all()
    serialized = []
    for item in data:
        serialized.append({
            'id': item.id,
            'water_level': item.water_level,
            'timestamp': item.timestamp,
            'device_id': item.device_id,
            'battery_level': item.battery_level,
            'signal_strength': item.signal_strength,
        })
    return Response(serialized)

@api_view(['GET'])
def get_stats(request):
    last_24h = timezone.now() - timedelta(hours=24)
    recent_data = WaterLevelReading.objects.filter(timestamp__gte=last_24h)
    
    stats = recent_data.aggregate(
        avg_level=Avg('water_level'),
        max_level=Max('water_level'),
        min_level=Min('water_level')
    )
    
    return Response({
        'average': stats['avg_level'] or 0,
        'maximum': stats['max_level'] or 0,
        'minimum': stats['min_level'] or 0,
        'readings_count': recent_data.count()
    })

# ==================== ESP8266 ENDPOINT ====================

@csrf_exempt
@require_http_methods(["POST"])
def water_level_api(request):
    """
    Endpoint for ESP8266 to send water level data
    Expected JSON format:
    {
        "water_level_cm": 45.5,
        "percentage": 45.5,
        "device_id": "ESP8266_CANAL_01",
        "battery_level": 100,
        "rssi": -65
    }
    """
    try:
        # Parse the incoming data
        data = json.loads(request.body)
        
        # Extract water level (supports both cm and percentage)
        water_level_cm = data.get('water_level_cm')
        percentage = data.get('percentage')
        
        # If percentage is sent, convert to cm (assuming max 100cm range)
        if percentage is not None and water_level_cm is None:
            water_level_cm = percentage
        
        # Validate water level
        if water_level_cm is None:
            return JsonResponse({'error': 'water_level_cm or percentage is required'}, status=400)
        
        # Get optional fields
        device_id = data.get('device_id', 'ESP8266_01')
        battery_level = data.get('battery_level')
        signal_strength = data.get('rssi')
        
        # Save to WaterLevelReading model (create this model first)
        # If you don't have this model, use WaterSensorData instead:
        reading = WaterLevelReading.objects.create(
            water_level=water_level_cm,
            device_id=device_id,
            battery_level=battery_level,
            signal_strength=signal_strength,
            timestamp=timezone.now()
        )
        
        # Check for critical levels and determine alert
        alert = None
        alert_message = None
        
        if water_level_cm > 85:
            alert = "CRITICAL_FLOOD"
            alert_message = "🚨 CRITICAL FLOOD! EVACUATE IMMEDIATELY!"
        elif water_level_cm > 70:
            alert = "SEVERE_WARNING"
            alert_message = "⚠️ SEVERE FLOOD WARNING! Prepare to evacuate!"
        elif water_level_cm > 50:
            alert = "FLOOD_WATCH"
            alert_message = "📢 FLOOD WATCH! Monitor water levels closely!"
        
        return JsonResponse({
            'status': 'success',
            'id': reading.id,
            'water_level': water_level_cm,
            'alert': alert,
            'alert_message': alert_message,
            'message': 'Data received successfully'
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



# ==================== ALTERNATIVE: Use WaterSensorData model if WaterLevelReading doesn't exist ====================

@csrf_exempt
@require_http_methods(["POST"])
def water_level_api_alternative(request):
    """
    Alternative endpoint using WaterSensorData model instead of WaterLevelReading
    Use this if you haven't created the WaterLevelReading model yet
    """
    try:
        data = json.loads(request.body)
        
        # Extract water level
        water_level_cm = data.get('water_level_cm') or data.get('percentage')
        
        if water_level_cm is None:
            return JsonResponse({'error': 'water_level_cm or percentage is required'}, status=400)
        
        # Save to WaterSensorData model
        reading = WaterSensorData.objects.create(
            water_level=water_level_cm,
            device_id=data.get('device_id', 'ESP8266_01'),
            timestamp=timezone.now()
        )
        
        # Determine alert level
        alert = None
        if water_level_cm > 85:
            alert = "CRITICAL_FLOOD"
        elif water_level_cm > 70:
            alert = "SEVERE_WARNING"
        elif water_level_cm > 50:
            alert = "FLOOD_WATCH"
        
        return JsonResponse({
            'status': 'success',
            'id': reading.id,
            'water_level': water_level_cm,
            'alert': alert,
            'message': 'Data received successfully'
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ==================== AUTHENTICATION ENDPOINTS ====================

@api_view(['POST'])
def register(request):
    data = request.data
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')

    if not username or not email or not password:
        return Response({'message': 'username, email and password are required'}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({'message': 'Username already exists'}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({'message': 'Email already registered'}, status=400)

    try:
        validate_password(password)
    except ValidationError as e:
        return Response({'message': ' '.join(e.messages)}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password,
                                    first_name=first_name, last_name=last_name)
    token, _ = Token.objects.get_or_create(user=user)

    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }

    return Response({'user': user_data, 'token': token.key}, status=201)

@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'message': 'username and password are required'}, status=400)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({'message': 'Invalid credentials'}, status=400)

    token, _ = Token.objects.get_or_create(user=user)
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }

    return Response({'user': user_data, 'token': token.key}, status=200)