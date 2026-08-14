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
        default='manager'
    )
    
    use_this_company = models.ForeignKey(
        'Company', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='active_users'
    )

    def __str__(self):
        return self.username


class Company(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    company_code = models.CharField(max_length=20, default='COMP-0000')
    zone = models.CharField(max_length=100, default='Zone North')
    status = models.CharField(max_length=50, default='Up to date')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_companies', null=True, blank=True)
    
    operators = models.ManyToManyField(User, related_name='operated_companies', blank=True)
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
    
    area_size = models.CharField(max_length=50, default='100 m²')
    image_url = models.URLField(blank=True, null=True)
    current_metric = models.CharField(max_length=50, default='85% Humidity')
    polygon_coordinates = models.JSONField(null=True, blank=True)
    
    FREQUENCY_CHOICES = (
        ('Weekly', 'Weekly'),
        ('Fortnightly', 'Fortnightly'),
        ('Monthly', 'Monthly'),
    )
    reminder_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='Weekly')

    def __str__(self):
        return f"{self.name} - {self.company.name}"

class Personnel(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='personnel')
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=100)
    email = models.EmailField()
    avatar_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.full_name