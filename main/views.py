from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from users.views import is_admin  # reuse admin check
from django.contrib.auth.decorators import user_passes_test # type: ignore
from .forms import ServiceForm
from .models import Service
from users.models import Review
from users.models import ProviderService, ServiceProvider


def home(request):
    reviews = Review.objects.select_related('customer__user').order_by('-created_at')[:10]  
    return render(request, 'main/index.html', {'reviews': reviews})


@login_required(login_url='login_admin')
@user_passes_test(is_admin, login_url='login_admin')
def add_service_view(request):
    form = ServiceForm(request.POST or None, request.FILES or None)
    
    if request.method == 'POST':
        if 'add' in request.POST and form.is_valid():
            form.save()
            return redirect('view_services')  # redirect to view services after adding
        elif 'clear' in request.POST:
            form = ServiceForm()  # reset form

    context = {'form': form}
    return render(request, 'main/add_service.html', context)


@login_required(login_url='login_admin')
@user_passes_test(is_admin, login_url='login_admin')
def view_services_view(request):
    services = Service.objects.all()
    context = {'services': services}
    return render(request, 'main/view_services.html', context)



@login_required(login_url='login_admin')
@user_passes_test(is_admin, login_url='login_admin')
def providers_by_profession_view(request, profession_name):
    # Filter ProviderService by service_type's profession_name
    services = ProviderService.objects.filter(service_type__profession_name=profession_name)

    # Keep only unique providers
    providers_dict = {}
    for service in services:
        provider = service.provider
        if provider.id not in providers_dict:
            providers_dict[provider.id] = {
                'provider': provider,
                'service_type': service.service_type.profession_name,
                'experience': service.experience,
                'address': service.address,
                'phone': service.phone,
            }

    context = {
        'profession_name': profession_name,
        'providers': providers_dict.values(),
    }
    return render(request, 'main/providers_by_profession.html', context)




@login_required(login_url='login_admin')
@user_passes_test(is_admin, login_url='login_admin')
def delete_service_view(request, service_id):
    print(" Delete request received for service ID:", service_id)
    service = get_object_or_404(Service, id=service_id)
    
    if request.method == 'POST':
        print(" POST request confirmed — deleting service...")
        if service.image:
            service.image.delete(save=False)
        service.delete()
        print(" Deleted successfully.")
        return redirect('view_services')

    print(" Not a POST request — redirecting.")
    return redirect('view_services')

