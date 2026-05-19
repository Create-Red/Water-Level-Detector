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

@api_view(['POST'])
def add_sensor_data(request):
    serializer = WaterSensorDataSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"status": "success", "data": serializer.data}, status=201)
    return Response(serializer.errors, status=400)

@api_view(['GET'])
def get_latest_data(request):
    latest = WaterSensorData.objects.last()
    if latest:
        serializer = WaterSensorDataSerializer(latest)
        return Response(serializer.data)
    return Response({"error": "No data found"}, status=404)

@api_view(['GET'])
def get_all_data(request):
    data = WaterSensorData.objects.all().order_by('-timestamp')
    serializer = WaterSensorDataSerializer(data, many=True)
    return Response(serializer.data)

# Add this new view function AFTER your existing views
@api_view(['GET'])
def get_stats(request):
    last_24h = timezone.now() - timedelta(hours=24)
    recent_data = WaterSensorData.objects.filter(timestamp__gte=last_24h)
    
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