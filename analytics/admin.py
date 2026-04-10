from django.contrib import admin
from .models import HealthFacility, DiseaseRecord

# Register your models here so they show up in the Admin Panel
admin.site.register(HealthFacility)
admin.site.register(DiseaseRecord)