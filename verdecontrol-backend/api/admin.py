from django.contrib import admin
from .models import Company, GreenZone

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company_code', 'email')

    search_fields = ('name', 'company_code') 

@admin.register(GreenZone)
class GreenZoneAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company', 'area_size', 'timer_status')

    list_filter = ('timer_status', 'company')
    search_fields = ('name',)