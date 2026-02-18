from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Customer, ServiceProvider, AdminService, ProviderService, Review

# Register CustomUser with default UserAdmin
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Profile', {'fields': ('role', 'profile_pic')}),
    )
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')

# Register other models
admin.site.register(Customer)
admin.site.register(ServiceProvider)
admin.site.register(AdminService)
admin.site.register(ProviderService)
admin.site.register(Review)
