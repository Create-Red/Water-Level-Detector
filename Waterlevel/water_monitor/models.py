from django.db import models

class WaterSensorData(models.Model):
    water_level = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.water_level} cm at {self.timestamp}"


class WaterLevelReading(models.Model):
    """
    Model for ESP8266 water level sensor data
    Includes additional fields for device monitoring
    """
    water_level = models.FloatField(help_text="Water level in cm")
    timestamp = models.DateTimeField(auto_now_add=True)
    device_id = models.CharField(max_length=50, default='ESP8266_01', help_text="Device identifier")
    battery_level = models.FloatField(null=True, blank=True, help_text="Battery percentage (0-100)")
    signal_strength = models.IntegerField(null=True, blank=True, help_text="WiFi RSSI signal strength")
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Water Level Reading"
        verbose_name_plural = "Water Level Readings"
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['device_id']),
            models.Index(fields=['water_level']),
        ]
    
    def __str__(self):
        return f"{self.device_id}: {self.water_level} cm at {self.timestamp}"
    
    def get_status(self):
        """Get flood status based on water level"""
        if self.water_level > 85:
            return "CRITICAL_FLOOD"
        elif self.water_level > 70:
            return "SEVERE_WARNING"
        elif self.water_level > 50:
            return "FLOOD_WATCH"
        elif self.water_level > 30:
            return "NORMAL"
        else:
            return "LOW_WATER"