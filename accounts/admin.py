from django.contrib import admin
from django.contrib.auth.models import User


class UserAdmin(admin.ModelAdmin):

    list_display = (
        'username',
        'email',
        'first_name',
        'is_active',
        'is_staff'
    )

    list_filter = (
        'is_active',
        'is_staff'
    )

    search_fields = (
        'username',
        'email',
        'first_name'
    )


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
from django.contrib import admin
from .models import Profile

admin.site.register(Profile)