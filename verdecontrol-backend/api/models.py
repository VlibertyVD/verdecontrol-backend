from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    
    ROLE_CHOICES = (
        ('manager', 'Facility Manager'),
        ('operator', 'Operador en campo'),
    )
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='operator'
    )
        
    def __str__(self):
        return self.username


class Company(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class GreenZone(models.Model):
    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='green_zones')
    weed_level = models.CharField(max_length=50, default='Normal')
    is_active = models.BooleanField(default=True)
    needs_attention = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # --- NUEVOS CAMPOS PARA EL TIMER ---
    location_details = models.CharField(max_length=255, blank=True, null=True) # Ej: "Headquarters, Block A"
    timer_status = models.CharField(max_length=50, default='Scheduled') # Ej: "Needs cutting", "Scheduled"
    next_maintenance = models.DateField(null=True, blank=True)
    
    FREQUENCY_CHOICES = (
        ('Weekly', 'Weekly'),
        ('Fortnightly', 'Fortnightly'),
        ('Monthly', 'Monthly'),
    )
    reminder_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='Weekly')

    def __str__(self):
        return f"{self.name} - {self.company.name}"