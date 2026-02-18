from django.contrib.auth.models import AbstractUser # type: ignore
from django.contrib.auth import get_user_model  # type: ignore
from django.db import models # type: ignore
from main.models import Service
from django.utils import timezone # type: ignore


# -------------------------------
# Custom User Model
# -------------------------------
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('provider', 'Service Provider'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

# -------------------------------
# Customer Extra Fields
# -------------------------------
class Customer(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    def __str__(self):
        return self.user.username

# -------------------------------
# Service Provider Extra Fields
# -------------------------------
class ServiceProvider(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)


    def __str__(self):
        return self.user.username

User = get_user_model()

# -------------------------------
# Admin-added Services
# -------------------------------
class AdminService(models.Model):
    # Services that admin adds
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# -------------------------------
# Provider Listed Services
# -------------------------------
class ProviderService(models.Model):
    EXPERIENCE_CHOICES = [
        ('0-1', '0-1 years'),
        ('2-3', '2-3 years'),
        ('4-5', '4-5 years'),
        ('6-10', '6-10 years'),
        ('10+', 'Above 10 years'),
    ]

    provider = models.ForeignKey('ServiceProvider', on_delete=models.CASCADE)
    service_type = models.ForeignKey(Service, on_delete=models.CASCADE)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    experience = models.CharField(max_length=10, choices=EXPERIENCE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider.user.username} - {self.service_type.name}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('arriving', 'Arriving'),
        ('arrived', 'Arrived'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    provider = models.ForeignKey('ServiceProvider', on_delete=models.CASCADE)
    service = models.ForeignKey('ProviderService', on_delete=models.CASCADE)
    schedule_date = models.DateField()
    timing = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.user.username} - {self.service.service_type.name} with {self.provider.user.username}"


class ProviderEarning(models.Model):
    provider = models.OneToOneField(ServiceProvider, on_delete=models.CASCADE)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.provider.user.username} - ₹{self.total_earnings}"


class Review(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.customer.user.username} - {self.content[:30]}"