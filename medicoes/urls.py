from django.urls import path
from .views import (
    LandingPageView, DashboardHubView, CompanyCreateView, DepartmentCreateView, 
    SectorCreateView, ProductionLineCreateView, ProductSKUCreateView,
    SKUConfigurationUpdateView, MeasurementDashboardView, AnalyzeLiveStreamView,
    MeasurementDetailJsonView, SKUAnalyticsJsonView
)

app_name = 'medicoes'

urlpatterns = [
    # B2B SaaS Public Storefront / Landing Page
    path('', LandingPageView.as_view(), name='index'),
    
    # Asset Tree Dashboard Hub
    path('dashboard/', DashboardHubView.as_view(), name='dashboard_hub'),
    
    # Hierarchical CRUD registration paths
    path('company/add/', CompanyCreateView.as_view(), name='company_add'),
    path('department/add/', DepartmentCreateView.as_view(), name='department_add'),
    path('sector/add/', SectorCreateView.as_view(), name='sector_add'),
    path('production-line/add/', ProductionLineCreateView.as_view(), name='line_add'),
    path('sku/add/', ProductSKUCreateView.as_view(), name='sku_add'),
    
    # SKU Configuration settings
    path('sku/<int:sku_id>/config/', SKUConfigurationUpdateView.as_view(), name='sku_config'),
    
    # Active Inspection Dashboards
    path('inspect/sku/<int:sku_id>/', MeasurementDashboardView.as_view(), name='dashboard'),
    
    # AJAX Real-time Frame Processing
    path('analyze-live/sku/<int:sku_id>/', AnalyzeLiveStreamView.as_view(), name='analyze_live'),
    
    # AJAX Historical Record Details
    path('record/<int:record_id>/details/', MeasurementDetailJsonView.as_view(), name='record_details'),
    
    # AJAX SKU Analytics Data for SPC Charts
    path('sku/<int:sku_id>/analytics/', SKUAnalyticsJsonView.as_view(), name='sku_analytics_data'),
]


