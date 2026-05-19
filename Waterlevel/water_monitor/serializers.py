from rest_framework import serializers
from .models import WaterSensorData

class WaterSensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterSensorData
        fields = '__all__'