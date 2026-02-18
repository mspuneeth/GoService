from django.urls import path, include # type: ignore
from django.contrib import admin # type: ignore
from . import views

urlpatterns = [
    # Customer
    path('signup/customer/', views.customer_signup_view, name='signup_customer'),
    path('login/customer/', views.customer_login_view, name='login_customer'),
    path('dashboard/customer/', views.customer_dashboard_view, name='customer_dashboard'),
    path('dashboard/customer/profile/', views.customer_profile_view, name='customer_profile'),
    path('dashboard/customer/services/', views.customer_services_view, name='customer_services'),
    path('dashboard/customer/services/<str:profession_name>/', views.customer_providers_by_service_view, name='customer_providers_by_service'),
    # Add this path
    path('booking/create/', views.create_booking_view, name='create_booking'),
    # Add under customer paths
    path('payment/<int:booking_id>/', views.payment_view, name='payment'),
    path('payment/success/<int:booking_id>/', views.payment_success_view, name='payment_success'),
    path('dashboard/customer/bookings/', views.customer_bookings_view, name='customer_bookings'),
    path('booking/cancel/', views.cancel_booking_view, name='cancel_booking'),
    path('payment/cod/<int:booking_id>/', views.cod_confirmation_view, name='cod_confirmation'),
    path('review/', views.customer_review_view, name='customer_review'),
    
    # Service Provider
    path('signup/provider/', views.provider_signup_view, name='signup_provider'),
    path('login/provider/', views.provider_login_view, name='login_provider'),
    path('dashboard/provider/bookings/', views.provider_view_bookings_view, name='provider_view_bookings'),
    path('dashboard/provider/bookings/update/<int:booking_id>/', views.update_booking_status, name='update_booking_status'),

    # Admin
    path('login/admin/', views.admin_login_view, name='login_admin'),
    path('dashboard/admin/', views.admin_dashboard_view, name='admin_dashboard'),  
    # Admin: View Service Providers
    path('dashboard/admin/providers/', views.admin_view_service_providers, name='admin_view_providers'),
    path('dashboard/admin/providers/delete/<int:provider_id>/', views.admin_delete_provider, name='admin_delete_provider'),
    # Admin: View Customers
    path('dashboard/admin/customers/', views.admin_view_customers, name='admin_view_customers'),
    path('dashboard/admin/customers/delete/<int:customer_id>/', views.admin_delete_customer, name='admin_delete_customer'),

    # Logout
    path('logout/', views.logout_view, name='logout'),
    # Service Provider Dashboard
    path('dashboard/provider/', views.provider_dashboard_view, name='provider_dashboard'),
    path('dashboard/provider/list/', views.list_service_view, name='list_service'),
    path('dashboard/provider/profile/', views.provider_profile_view, name='provider_profile'),


]
