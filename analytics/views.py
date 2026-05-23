import csv
import io
from django.shortcuts import render, redirect
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from .models import DiseaseRecord, HealthFacility
from django.contrib import messages
from .forms import DiseaseRecordForm, HealthFacilityForm

@login_required(login_url='/')
def dashboard_view(request):
    # 1. Fetch all records from the database
    records = DiseaseRecord.objects.all().order_by('-report_date')
    facilities = HealthFacility.objects.all()

    # 2. Perform Analytics (Sum of all cases and deaths)
    total_cases = records.aggregate(Sum('cases'))['cases__sum'] or 0
    total_deaths = records.aggregate(Sum('deaths'))['deaths__sum'] or 0

    # 3. Group data by disease for the chart
    disease_stats = {}
    for record in records:
        if record.disease_name in disease_stats:
            disease_stats[record.disease_name] += record.cases
        else:
            disease_stats[record.disease_name] = record.cases

    # 4. Send all this data to the HTML template
    context = {
        'records': records,
        'facilities_count': facilities.count(),
        'total_cases': total_cases,
        'total_deaths': total_deaths,
        'disease_stats': disease_stats,
    }
    
    return render(request, 'analytics/dashboard.html', context)

@login_required(login_url='/')
def data_entry_view(request):
    if request.method == 'POST':
        form = DiseaseRecordForm(request.POST)
        if form.is_valid():
            # Save the form but don't hit the database just yet
            record = form.save(commit=False)
            
            # Attach the currently logged-in user to the record
            record.recorded_by = request.user
            
            # Now save it permanently to the database
            record.save()
            
            # Send a success message and refresh the page for the next entry
            messages.success(request, 'Data submitted and validated successfully.')
            return redirect('data_entry')
        else:
            # If the validation fails (like deaths > cases), show an error
            messages.error(request, 'Validation failed. Please correct the errors below.')
    else:
        # If they are just opening the page for the first time, show a blank form
        form = DiseaseRecordForm()

    return render(request, 'analytics/data_entry.html', {'form': form})

@login_required(login_url='/')
def add_facility_view(request):
    # ROLE-BASED SECURITY CHECK: Is this user an Administrator?
    if not request.user.is_superuser:
        messages.error(request, 'Access Denied: Only Administrators can add new health facilities.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = HealthFacilityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'New Health Facility added to the system successfully.')
            return redirect('add_facility')
    else:
        form = HealthFacilityForm()

    return render(request, 'analytics/add_facility.html', {'form': form})

@login_required(login_url='/')
def bulk_upload_view(request):
    if request.method == 'POST':
        # 1. Get the uploaded file
        csv_file = request.FILES.get('csv_file')

        # 2. Check if a file was actually uploaded and is a CSV
        if not csv_file:
            messages.error(request, 'Please select a file to upload.')
            return redirect('bulk_upload')
            
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Invalid format. Please upload a .csv file.')
            return redirect('bulk_upload')

        try:
            # 3. Read and decode the CSV data
            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            
            # 4. Parse the CSV using DictReader (reads the top row as column headers)
            reader = csv.DictReader(io_string)
            records_created = 0

            # 5. Loop through every single row and save it to the database
            for row in reader:
                # Find the facility, or create it if it's completely new
                facility_name = row.get('Facility')
                facility_obj, created = HealthFacility.objects.get_or_create(
                    name=facility_name, 
                    defaults={'location': 'Imported from CSV'}
                )

                # Create the disease record
                DiseaseRecord.objects.create(
                    facility=facility_obj,
                    report_date=row.get('Date'),
                    disease_name=row.get('Disease'),
                    cases=int(row.get('Cases', 0)),
                    deaths=int(row.get('Deaths', 0)),
                    recorded_by=request.user
                )
                records_created += 1

            # 6. Success! Send them to the dashboard to see the new data
            messages.success(request, f'Successfully uploaded {records_created} records to the database!')
            return redirect('dashboard')

        except Exception as e:
            messages.error(request, f'Error reading file. Ensure headers exactly match: Facility, Date, Disease, Cases, Deaths. Error: {e}')
            return redirect('bulk_upload')

    return render(request, 'analytics/bulk_upload.html')