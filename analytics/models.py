from django.db import models
from django.contrib.auth.models import User

# Facility Table
class HealthFacility(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

    def __str__(self):
        return self.name

# Disease Record Table
class DiseaseRecord(models.Model):
    DISEASE_CHOICES = [
        ('Malaria', 'Malaria'),
        ('Cholera', 'Cholera'),
        ('Lassa Fever', 'Lassa Fever'),
        ('COVID-19', 'COVID-19'),
        ('Measles', 'Measles'),
        ('Typhoid', 'Typhoid'),
    ]
    
    facility = models.ForeignKey(HealthFacility, on_delete=models.CASCADE)
    disease_name = models.CharField(max_length=100, choices=DISEASE_CHOICES)
    cases = models.PositiveIntegerField()
    deaths = models.PositiveIntegerField()
    report_date = models.DateField()
    
    # Links to the built-in Django User who submitted the data
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.disease_name} - {self.facility.name} ({self.report_date})"