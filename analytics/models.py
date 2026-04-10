from django.db import models

# Create your models here.
#  Table for Health Facilities (where vaccines are given)
class HealthFacility(models.Model):
    facility_name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    
    # ADD THIS LINES BELOW FOR PLURALITY:
    class Meta:
        verbose_name_plural = "Health Facilities"

    def __str__(self):
        return self.facility_name

#  Table for the actual Vaccine/Disease data
class DiseaseRecord(models.Model):
    facility = models.ForeignKey(HealthFacility, on_delete=models.CASCADE)
    disease_name = models.CharField(max_length=100) # e.g., 'BCG Vaccine'
    cases = models.IntegerField(default=0) # Number of people vaccinated
    deaths = models.IntegerField(default=0) # Adverse reactions or related deaths
    report_date = models.DateField()

    def __str__(self):
        return f"{self.disease_name} - {self.report_date}"