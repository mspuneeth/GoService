from django import forms # type: ignore
from django.contrib.auth.forms import UserCreationForm # type: ignore
from .models import CustomUser, Customer, ServiceProvider, ProviderService, Booking
from main.models import Service
import re


# ------------------------------
# Customer Signup Form
# ------------------------------
class CustomerSignupForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="Required. Enter a valid email address.",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )

    profile_pic = forms.ImageField(
        required=True,
        label='Profile Picture',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'profile_pic', 'password1', 'password2']

    # --- Ensure email is unique
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already registered.")
        return email

    # --- Validate password strength
    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if password1:
            if len(password1) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")
            if not re.search(r"[A-Z]", password1):
                raise forms.ValidationError("Password must contain at least one uppercase letter.")
            if not re.search(r"[a-z]", password1):
                raise forms.ValidationError("Password must contain at least one lowercase letter.")
            if not re.search(r"[0-9]", password1):
                raise forms.ValidationError("Password must contain at least one number.")
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password1):
                raise forms.ValidationError("Password must contain at least one special character.")
        return password1

    # --- Confirm both passwords match
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    # --- Save user as Customer
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'customer'
        if commit:
            user.save()
            Customer.objects.create(user=user)
        return user


# ------------------------------
# Service Provider Signup Form
# ------------------------------
class ProviderSignupForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="Required. Enter a valid email address.",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )

    profile_pic = forms.ImageField(
        required=True,
        label='Profile Picture',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'profile_pic', 'password1', 'password2']

    # --- Ensure email is unique
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already registered.")
        return email

    # --- Validate password strength
    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if password1:
            if len(password1) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")
            if not re.search(r"[A-Z]", password1):
                raise forms.ValidationError("Password must contain at least one uppercase letter.")
            if not re.search(r"[a-z]", password1):
                raise forms.ValidationError("Password must contain at least one lowercase letter.")
            if not re.search(r"[0-9]", password1):
                raise forms.ValidationError("Password must contain at least one number.")
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password1):
                raise forms.ValidationError("Password must contain at least one special character.")
        return password1

    # --- Confirm both passwords match
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    # --- Save user as Provider
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'provider'
        if commit:
            user.save()
            ServiceProvider.objects.create(user=user)
        return user


# ------------------------------
# Admin Login Form
# ------------------------------
class AdminLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter admin username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        required=True
    )


# ------------------------------
# Provider Service Form
# ------------------------------
class ProviderServiceForm(forms.ModelForm):
    service_type = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        empty_label=None,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    address = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter service address'})
    )
    phone = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter 10-digit contact number'})
    )
    experience = forms.ChoiceField(
        required=True,
        choices=ProviderService.EXPERIENCE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    price = forms.DecimalField(
        required=True,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter price per Sevice',
            'step': 0.01
        })
    )

    class Meta:
        model = ProviderService
        fields = ['service_type', 'address', 'phone', 'experience', 'price']

    # --- Custom phone number validation ---
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r'^\d{10}$', phone):
            raise forms.ValidationError("Phone number must be exactly 10 digits.")
        return phone


# ------------------------------
# Booking Form
# ------------------------------
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['schedule_date', 'timing']
        widgets = {
            'schedule_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'timing': forms.Select(attrs={'class': 'form-select'}),
        }
