from django.db import models

class WaterSensorData(models.Model):
    water_level = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.water_level} cm at {self.timestamp}"