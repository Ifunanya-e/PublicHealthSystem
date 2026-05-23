from django import forms
from .models import DiseaseRecord, HealthFacility

# 1. THE DATA ENTRY FORM
class DiseaseRecordForm(forms.ModelForm):
    class Meta:
        model = DiseaseRecord
        fields = ['facility', 'report_date', 'disease_name', 'cases', 'deaths']
        
        widgets = {
            'facility': forms.Select(attrs={'class': 'w-full p-3 border border-slate-300 rounded-lg bg-white outline-none focus:ring-2 focus:ring-blue-500'}),
            'report_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-3 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500'}),
            'disease_name': forms.Select(attrs={'class': 'w-full p-3 border border-slate-300 rounded-lg bg-white outline-none focus:ring-2 focus:ring-blue-500'}),
            'cases': forms.NumberInput(attrs={'class': 'w-full p-3 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500', 'min': '0'}),
            'deaths': forms.NumberInput(attrs={'class': 'w-full p-3 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500', 'min': '0'}),
        }

# Chapter 3 Validation Requirement: Ensure deaths do not exceed cases
    def clean(self):
        cleaned_data = super().clean()
        cases = cleaned_data.get('cases')
        deaths = cleaned_data.get('deaths')

        if cases is not None and deaths is not None:
            if deaths > cases:
                raise forms.ValidationError("Number of deaths cannot exceed the number of reported cases.")
        
        return cleaned_data

# 2. THE ADMIN FACILITY FORM
class HealthFacilityForm(forms.ModelForm):
    class Meta:
        model = HealthFacility
        fields = ['name', 'location']
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-3 border border-slate-300 rounded-lg bg-white outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'e.g. Lagos University Teaching Hospital'}),
            'location': forms.TextInput(attrs={'class': 'w-full p-3 border border-slate-300 rounded-lg bg-white outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'e.g. Lagos'}),
        }