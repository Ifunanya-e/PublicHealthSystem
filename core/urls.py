"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views # Add this import
from analytics.views import dashboard_view
from analytics.views import dashboard_view, data_entry_view, add_facility_view, bulk_upload_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. The base URL now loads the Login page
    path('', auth_views.LoginView.as_view(template_name='analytics/login.html'), name='login'),
    
    # 2. Add a logout URL that redirects back to the login page
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    # 3. Your dashboard stays here
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # 4. Add the new data entry route here:
    path('enter-data/', data_entry_view, name='data_entry'),
    
    # 5. New Admin Route:
    path('add-facility/', add_facility_view, name='add_facility'),
    
    # 6. Bulk Uploads
    path('bulk-upload/', bulk_upload_view, name='bulk_upload'),
]

