from datetime import timedelta
from django.utils import timezone
import json
from django.http import HttpResponse
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
            
    # 4. PREPARE DATA FOR CHART.JS
    chart_labels = list(disease_stats.keys())
    chart_data = list(disease_stats.values())

    # 4. Send all this data to the HTML template
    context = {
        'records': records,
        'facilities_count': facilities.count(),
        'total_cases': total_cases,
        'total_deaths': total_deaths,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
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

@login_required(login_url='/')
def reports_view(request):
    # 1. Start by fetching ALL records
    records = DiseaseRecord.objects.all().order_by('-report_date')
    facilities = HealthFacility.objects.all()
    
    # Get a list of unique diseases for our dropdown filter
    diseases = DiseaseRecord.objects.values_list('disease_name', flat=True).distinct()

    # 2. Get the search filters typed by the user
    facility_id = request.GET.get('facility')
    disease = request.GET.get('disease')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # 3. Apply the filters to our data
    if facility_id:
        records = records.filter(facility_id=facility_id)
    if disease:
        records = records.filter(disease_name=disease)
    if start_date:
        records = records.filter(report_date__gte=start_date)
    if end_date:
        records = records.filter(report_date__lte=end_date)

    # 4. The MAGIC: If they clicked "Export", generate a CSV instead of a webpage
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="custom_health_report.csv"'
        
        writer = csv.writer(response)
        # Write the header row
        writer.writerow(['Date', 'Facility', 'Disease', 'Cases', 'Deaths'])
        
        # Write the actual data
        for record in records:
            writer.writerow([record.report_date, record.facility.name, record.disease_name, record.cases, record.deaths])
            
        return response

    # 5. If they didn't click export, just show the normal web page
    context = {
        'records': records,
        'facilities': facilities,
        'diseases': diseases,
    }
    return render(request, 'analytics/reports.html', context)

@login_required(login_url='/')
def forecast_view(request):
    # 1. Set our timelines
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    sixty_days_ago = today - timedelta(days=60)

    # 2. Get Historical Data
    recent_records = DiseaseRecord.objects.filter(report_date__gte=thirty_days_ago)
    past_records = DiseaseRecord.objects.filter(report_date__gte=sixty_days_ago, report_date__lt=thirty_days_ago)

    recent_cases = recent_records.aggregate(Sum('cases'))['cases__sum'] or 0
    past_cases = past_records.aggregate(Sum('cases'))['cases__sum'] or 0

    # 3. Calculate the Trend Percentage
    if past_cases == 0:
        trend_percent = 0 if recent_cases == 0 else 100
    else:
        trend_percent = round(((recent_cases - past_cases) / past_cases) * 100, 1)

    # 4. Identify the Hotspots (Get the Top 3 instead of just 1)
    top_diseases = recent_records.values('disease_name').annotate(total=Sum('cases')).order_by('-total')[:3]
    top_facilities = recent_records.values('facility__name').annotate(total=Sum('cases')).order_by('-total')[:3]

    # Extract just the names into a list so we can display them easily
    disease_list = [d['disease_name'] for d in top_diseases] if top_diseases else ["Unknown"]
    facility_list = [f['facility__name'] for f in top_facilities] if top_facilities else ["Unknown"]

    # 5. THE RISK ENGINE: Generate Automated Text Summaries
    if trend_percent > 15:
        risk_level = "HIGH RISK / OUTBREAK WARNING"
        risk_color = "red"
        insight_text = f"Critical alert: Overall cases have spiked by {trend_percent}% in the last 30 days. The primary drivers of this surge are {', '.join(disease_list)}."
        recommendation = f"Immediate resource deployment recommended for {', '.join(facility_list)}. Initiate emergency containment protocols."
    elif trend_percent > 0:
        risk_level = "MODERATE RISK"
        risk_color = "yellow"
        insight_text = f"Warning: Cases are trending upward by {trend_percent}% compared to the previous month. Most frequently reported: {', '.join(disease_list)}."
        recommendation = f"Increase active surveillance at {', '.join(facility_list)} and prepare relevant diagnostic kits."
    else:
        risk_level = "LOW RISK"
        risk_color = "green"
        insight_text = f"Stable: Epidemic curve is flattening. Cases have decreased by {abs(trend_percent)}% in the last 30 days."
        recommendation = "Maintain standard monitoring and reporting protocols across all facilities."
        
    # 6. Generate Chart Data (Next 30 Days Forecast)
    daily_avg = recent_cases / 30 if recent_cases > 0 else 0
    future_labels = []
    future_data = []
    
    current_projected = daily_avg
    for i in range(1, 31):
        future_date = today + timedelta(days=i)
        future_labels.append(future_date.strftime("%b %d"))
        # Add a tiny bit of compounding daily growth/decline based on the trend
        current_projected *= (1 + ((trend_percent/100)/30)) 
        future_data.append(round(current_projected))

    context = {
        'risk_level': risk_level,
        'risk_color': risk_color,
        'insight_text': insight_text,
        'recommendation': recommendation,
        'top_diseases': top_diseases,
        'top_facilities': top_facilities,
        'chart_labels': json.dumps(future_labels),
        'chart_data': json.dumps(future_data),
    }
    
    return render(request, 'analytics/forecasts.html', context)