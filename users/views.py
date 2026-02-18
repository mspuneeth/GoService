from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
from django.contrib.auth import authenticate, login, logout # type: ignore
from django.contrib import messages # type: ignore
from django.contrib.auth.decorators import login_required, user_passes_test # type: ignore
from .forms import CustomerSignupForm, ProviderSignupForm, AdminLoginForm, ProviderServiceForm
from .models import Customer, ServiceProvider, ProviderService, ProviderEarning
from main.models import Service
from django.db.models import Sum # type: ignore
from django.http import JsonResponse # type: ignore
from .models import Booking, Review
from django.views.decorators.csrf import csrf_exempt # type: ignore
from django.views.decorators.http import require_POST # type: ignore
import json
from decimal import Decimal

# -------------------------
# Customer Views
# -------------------------
def customer_signup_view(request):
    if request.method == 'POST':
        form = CustomerSignupForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer account created successfully!')
            return redirect('login_customer')  
    else:
        form = CustomerSignupForm()
    return render(request, 'users/signup.html', {'form': form, 'role': 'Customer'})




def customer_login_view(request):
    # Clear old session messages (from previous users)
    list(messages.get_messages(request))

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.role == 'customer':
            login(request, user)
            return redirect('customer_dashboard')  
        else:
            messages.error(request, 'Invalid credentials or not a customer account.')
    return render(request, 'users/login.html', {'role': 'Customer'})




# -------------------------
# Service Provider Views
# -------------------------
def provider_signup_view(request):
    if request.method == 'POST':
        form = ProviderSignupForm(request.POST, request.FILES)  
        if form.is_valid():
            form.save()
            messages.success(request, 'Service Provider account created successfully!')
            return redirect('login_provider')  
        else:
            # debug form errors temporarily to console
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProviderSignupForm()

    context = {
        'form': form,
        'role': 'Service Provider'
    }
    return render(request, 'users/signup.html', context)

# Helper: check if user is provider
def is_provider(user):
    return user.is_authenticated and user.role == 'provider'

def provider_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.role == 'provider':
            login(request, user)
            return redirect('provider_dashboard')  
        else:
            messages.error(request, 'Invalid credentials or not a provider account.')
    return render(request, 'users/login.html', {'role': 'Service Provider'})

# -------------------------
# Provider - View Bookings
# -------------------------
@login_required(login_url='login_provider')
def provider_view_bookings_view(request):
    if request.user.role != 'provider':
        return redirect('login_provider')

    provider = get_object_or_404(ServiceProvider, user=request.user)
    bookings = Booking.objects.filter(provider=provider).order_by('-created_at')

    context = {
        'bookings': bookings,
    }
    return render(request, 'users/provider_view_bookings.html', context)


# -------------------------
# Provider - Update Booking Status (Accept/Reject/Dropdown)
# -------------------------
@csrf_exempt
@login_required(login_url='login_provider')
def update_booking_status(request, booking_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        new_status = data.get('status')
        booking = get_object_or_404(Booking, id=booking_id)

        booking.status = new_status
        booking.save()

        # If provider confirms the booking — credit earnings
        if new_status == 'confirmed':
            provider = booking.provider
            amount = booking.service.price or Decimal('0.00')

            provider_earning, created = ProviderEarning.objects.get_or_create(provider=provider)
            provider_earning.total_earnings += amount
            provider_earning.save()

        # If provider cancels or rejects — do not add earnings
        if new_status in ['cancelled', 'rejected']:
            # (optional) You can handle refund logic here if needed
            pass

        # Generate dynamic updated HTML
        if new_status in ['accepted', 'confirmed', 'arriving', 'arrived']:
            html = f"""
                <select class='form-select form-select-sm' onchange="updateStatus({booking.id}, this.value)">
                    <option value=''>Select Status</option>
                    <option value='confirmed'>Confirmed</option>
                    <option value='arriving'>Arriving</option>
                    <option value='arrived'>Arrived</option>
                    <option value='completed'>Completed</option>
                </select>
            """
        elif new_status in ['cancelled', 'rejected']:
            html = "<span class='badge bg-danger'>Cancelled</span>"
        elif new_status == 'completed':
            html = "<span class='badge bg-success'>Completed</span>"
        else:
            html = ""

        return JsonResponse({'success': True, 'new_status': new_status, 'updated_html': html})

    return JsonResponse({'success': False})


# -------------------------
# Admin Login View
# -------------------------
def admin_login_view(request):
    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            # Check if user exists and is admin or superuser
            if user is not None and (user.role == 'admin' or user.is_superuser):
                login(request, user)
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Invalid admin credentials.')
    else:
        form = AdminLoginForm()
    return render(request, 'users/admin_login.html', {'form': form})



# -------------------------
# Admin Dashboard View
# -------------------------
def is_admin(user):
    return user.role == 'admin' or user.is_superuser


@login_required(login_url='login_admin')
@user_passes_test(is_admin, login_url='login_admin')
def admin_dashboard_view(request):
    customers = Customer.objects.all()
    providers = ServiceProvider.objects.all()

    # total earnings across all providers
    total_earnings = ProviderEarning.objects.aggregate(total=Sum('total_earnings'))['total'] or 0.0

    context = {
        'customers': customers,
        'providers': providers,
        'total_earnings': total_earnings,
    }
    return render(request, 'users/admin_dashboard.html', context)


@login_required(login_url='login_admin')
@user_passes_test(is_admin, login_url='login_admin')
def admin_view_service_providers(request):
    # Fetch only providers who have at least one service listed
    providers_with_services = ServiceProvider.objects.filter(
        providerservice__isnull=False
    ).distinct()

    # Prepare data: latest service for each provider
    providers_data = []
    for provider in providers_with_services:
        latest_service = ProviderService.objects.filter(provider=provider).order_by('-created_at').first()
        providers_data.append({
            'provider': provider,
            'service': latest_service
        })

    context = {
        'providers_data': providers_data
    }
    return render(request, 'users/admin_providers.html', context)


@login_required(login_url='login_admin')
@user_passes_test(is_admin, login_url='login_admin')
def admin_delete_provider(request, provider_id):
    provider = get_object_or_404(ServiceProvider, id=provider_id)
    provider.user.delete()  # Delete the associated user also
    messages.success(request, f'Provider {provider.user.username} deleted successfully!')
    return redirect('admin_view_providers')

@login_required(login_url='login_admin')
@user_passes_test(is_admin, login_url='login_admin')
def admin_view_customers(request):
    # Fetch only customers who have filled profile (phone or address)
    customers = Customer.objects.filter(
        phone__isnull=False
    ).exclude(phone='')  # ensure phone is not empty

    context = {
        'customers': customers
    }
    return render(request, 'users/admin_customers.html', context)


@login_required(login_url='login_admin')
@user_passes_test(is_admin, login_url='login_admin')
def admin_delete_customer(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    customer.user.delete()  # delete associated user as well
    messages.success(request, f'Customer {customer.user.username} deleted successfully!')
    return redirect('admin_view_customers')

# -------------------------
# Logout View
# -------------------------

def logout_view(request):
    #  Clear all pending messages for this session
    list(messages.get_messages(request))  # this consumes & removes all queued messages

    # Log out the user and clear session data
    logout(request)
    request.session.flush()  # ensures session data (including message storage) is wiped

    #  Redirect to home
    return redirect('home')

 


@login_required(login_url='login_provider')
@user_passes_test(is_provider)
def provider_dashboard_view(request):
    provider = get_object_or_404(ServiceProvider, user=request.user)
    services = ProviderService.objects.filter(provider=provider)

    # Ensure a ProviderEarning exists for this provider and read fresh
    provider_earning, _ = ProviderEarning.objects.get_or_create(provider=provider)

    # Convert Decimal to float for template display
    try:
        total_earnings = float(provider_earning.total_earnings)
    except Exception:
        total_earnings = 0.0

    context = {
        'provider': provider,
        'services': services,
        'total_earnings': total_earnings,
    }
    return render(request, 'users/provider_dashboard.html', context)



@login_required(login_url='login_provider')
def list_service_view(request):
    if request.user.role != 'provider':
        return redirect('login_provider')

    provider = ServiceProvider.objects.get(user=request.user)

    # Get the last listed service if exists
    last_service = ProviderService.objects.filter(provider=provider).last()

    if request.method == 'POST':
        form = ProviderServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.provider = provider
            service.save()
            messages.success(request, 'Service listed successfully!')
            return redirect('provider_dashboard')
        else:
            # Print form errors for debugging
            print("Form invalid! Errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pull phone from last service if exists
        initial_data = {}
        if last_service:
            initial_data.update({
                'phone': last_service.phone,
                'address': last_service.address,
                'experience': last_service.experience,
                'service_type': last_service.service_type,
            })
        form = ProviderServiceForm(initial=initial_data)

    context = {
        'form': form,
        'provider': provider,
    }
    return render(request, 'users/list_service.html', context)



@login_required(login_url='login_provider')
def provider_profile_view(request):
    provider = ServiceProvider.objects.get(user=request.user)
    service = ProviderService.objects.filter(provider=provider).last()
    
    context = {
        'provider': provider,
        'service': service,
    }
    return render(request, 'users/provider_profile.html', context)



@login_required(login_url='login_customer')
def customer_dashboard_view(request):
    if request.user.role != 'customer':
        return redirect('login_customer')  # extra safety

    context = {
        'customer': request.user,
    }
    return render(request, 'users/customer_dashboard.html', context)


@login_required(login_url='login_customer')
def customer_profile_view(request):
    if request.user.role != 'customer':
        return redirect('login_customer')

    customer = Customer.objects.get(user=request.user)

    if request.method == 'POST':
        phone = request.POST.get('phone')
        address = request.POST.get('address')

        customer.phone = phone
        customer.address = address
        customer.save()

        messages.success(request, 'Profile updated successfully!')

    context = {
        'customer': customer,
    }
    return render(request, 'users/customer_profile.html', context)


@login_required(login_url='login_customer')
def customer_services_view(request):
    services = Service.objects.all()
    context = {'services': services}
    return render(request, 'users/customer_services.html', context)


@login_required(login_url='login_customer')
def customer_providers_by_service_view(request, profession_name):
    # Get all ProviderService objects for this service type
    services = ProviderService.objects.filter(service_type__profession_name=profession_name)

    # Keep only one ProviderService per provider
    unique_providers = {}  
    for service in services:
        provider = service.provider
        if provider.id not in unique_providers:
            unique_providers[provider.id] = {
                'provider': provider,
                'service': service,
                'service_type': service.service_type.profession_name,      
                'experience': service.experience,
                'price': service.price,
                'address': service.address,
                'phone': service.phone,
            }

    customer = request.user

    context = {
        'service_name': profession_name,
        'providers': unique_providers.values(),
        'customer': customer,
    }
    return render(request, 'users/customer_providers_by_service.html', context)



@login_required(login_url='login_customer')
@require_POST
def create_booking_view(request):
    # Ensure it's an AJAX request
    if request.headers.get('x-requested-with') != 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': 'Invalid request!'})

    service_id = request.POST.get('service_id')
    provider_id = request.POST.get('provider_id')
    schedule_date = request.POST.get('schedule_date')
    timing = request.POST.get('timing')

    # Validate all required fields
    if not all([service_id, provider_id, schedule_date, timing]):
        return JsonResponse({'status': 'error', 'message': 'Missing required data!'})

    try:
        customer = Customer.objects.get(user=request.user)

        #  Check if customer profile is complete
        if not customer.phone or not customer.address:
            return JsonResponse({
                'status': 'error',
                'message': 'Please complete your profile (phone and address) before booking a service.'
            })

        provider = ServiceProvider.objects.get(id=provider_id)
        service = ProviderService.objects.get(id=service_id, provider=provider)

        # Prevent duplicate bookings for same service, provider, date, and time
        existing = Booking.objects.filter(
            customer=customer,
            provider=provider,
            service=service,
            schedule_date=schedule_date,
            timing=timing
        ).first()

        if existing:
            return JsonResponse({
                'status': 'error',
                'message': 'You have already booked this service for the selected date and time.'
            })

        #  Create the booking only if profile is complete
        booking = Booking.objects.create(
            customer=customer,
            provider=provider,
            service=service,
            schedule_date=schedule_date,
            timing=timing,
            status='pending'  # initial status
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Booking created successfully!',
            'booking_id': booking.id
        })

    except ServiceProvider.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Invalid service provider!'})
    except ProviderService.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Invalid service selection!'})
    except Customer.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Customer profile not found!'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})




@login_required(login_url='login_customer')
def payment_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer__user=request.user)
    amount = booking.service.price  # Amount to be displayed

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')

        if not payment_method:
            messages.error(request, "Please select a payment method.")
            return redirect('payment', booking_id=booking.id)

        # Store selected payment method in booking for reference
        booking.payment_method = payment_method
        booking.save()

        # Redirect based on payment method
        if payment_method == 'cod':
            return redirect('cod_confirmation', booking_id=booking.id)
        else:
            return redirect('payment_success', booking_id=booking.id)

    context = {
        'booking': booking,
        'amount': amount,
    }
    return render(request, 'users/payment.html', context)

@login_required(login_url='login_customer')
def cod_confirmation_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, customer__user=request.user)

    # Keep booking pending; provider must confirm later
    booking.status = 'pending'
    booking.save()

    messages.info(request, "Your booking has been placed successfully! The service provider will confirm soon. Please pay cash after service completion.")

    return render(request, 'users/cod_confirmation.html', {
        'booking': booking,
        'amount': booking.service.price
    })



import logging
logger = logging.getLogger(__name__)

@login_required(login_url='login_customer')
def payment_success_view(request, booking_id):
    if not booking_id:
        return render(request, 'users/payment_success.html', {'error': 'Invalid booking ID.'})

    # Fetch the booking
    booking = get_object_or_404(Booking, id=booking_id, customer__user=request.user)
    provider = booking.provider

    # Get amount and ensure Decimal
    amount = booking.service.price if booking.service and booking.service.price is not None else Decimal('0.00')
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    # 1) Update booking status
    booking.status = 'pending'
    booking.save()

    # 2) Update provider earnings (Decimal-safe)
    provider_earning, created = ProviderEarning.objects.get_or_create(provider=provider)
    # ensure provider_earning.total_earnings is Decimal
    if not isinstance(provider_earning.total_earnings, Decimal):
        provider_earning.total_earnings = Decimal(str(provider_earning.total_earnings or '0.00'))

    provider_earning.total_earnings = provider_earning.total_earnings + amount
    provider_earning.save()

    # 3) Logging / console info for debugging
    logger.info(f'Payment success: booking_id={booking.id}, provider={provider.user.username}, amount={amount}, new_total={provider_earning.total_earnings}')
    print(f' Payment success: booking {booking.id} — credited {provider.user.username} with {amount}. New total: {provider_earning.total_earnings}')

    messages.success(request, f'Payment successful! ₹{amount} added to {provider.user.username} earnings.')

    return render(request, 'users/payment_success.html', {
        'booking': booking,
        'amount': amount,
    })





@login_required(login_url='login_customer')
def customer_bookings_view(request):
    customer = Customer.objects.get(user=request.user)
    
    # Current bookings: pending, confirmed, arriving
    current_bookings = Booking.objects.filter(
        customer=customer,
        status__in=['pending','confirmed','arriving','arrived']
    ).order_by('-schedule_date')
    
    # Past bookings: completed, cancelled
    past_bookings = Booking.objects.filter(
        customer=customer,
        status__in=['completed','cancelled']
    ).order_by('-schedule_date')
    
    context = {
        'current_bookings': current_bookings,
        'past_bookings': past_bookings,
    }
    return render(request, 'users/customer_bookings.html', context)

# -------------------------
# Customer - Cancel Booking
# -------------------------
@login_required(login_url='login_customer')
@require_POST
def cancel_booking_view(request):
    booking_id = request.POST.get('booking_id')

    try:
        customer = Customer.objects.get(user=request.user)
        booking = Booking.objects.get(id=booking_id, customer=customer)

        # Only allow cancellation if status is pending, confirmed, or arriving
        if booking.status.lower() in ['pending', 'confirmed', 'arriving']:
            booking.status = 'cancelled'
            booking.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': 'Cannot cancel completed or already cancelled bookings.'})

    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Booking not found.'})
    except Customer.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Customer not found.'})

@login_required(login_url='login_customer')
def customer_review_view(request):
    if request.user.role != 'customer':
        return redirect('login_customer')

    customer = Customer.objects.get(user=request.user)

    if request.method == 'POST':
        content = request.POST.get('review')
        if content.strip():
            Review.objects.create(customer=customer, content=content)
            messages.success(request, "Review submitted successfully!")
            return redirect('customer_review')

    reviews = Review.objects.filter(customer=customer).order_by('-created_at')
    return render(request, 'users/customer_review.html', {
        'customer': customer,
        'reviews': reviews
    })
