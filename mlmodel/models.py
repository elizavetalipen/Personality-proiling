from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

# модель для данных, отображаемых на странице пользователя
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField(blank=True, null=True)
    avatar = models.ImageField(upload_to='images/userdata', blank=True)
    about = models.CharField(max_length=500)
    # количество проведенных вычислений
    count = models.IntegerField()

class Prediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    prediction_date = models.DateTimeField(default=datetime.now)
    final_result = models.CharField(max_length=4, default='infp')
    description = models.TextField(max_length=500, blank=True, default="")
    
    def __str__(self):
        return f"{self.user} - {self.final_result} - {self.prediction_date}"


    






