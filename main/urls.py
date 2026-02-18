from django.urls import path # type: ignore
from . import views

urlpatterns = [
    # Custom Admin Pages
    path('dashboard/add-service/', views.add_service_view, name='add_service'),
    path('dashboard/view-services/', views.view_services_view, name='view_services'),
    path('dashboard/view-services/<str:profession_name>/', views.providers_by_profession_view, name='providers_by_profession'),

    # Delete Service Route
    path('dashboard/delete-service/<int:service_id>/', views.delete_service_view, name='delete_service'),

    # Home Page
    path('', views.home, name='home'),
]
