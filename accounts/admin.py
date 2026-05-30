from django.contrib import admin
from django.contrib.auth.models import User
from .models import Profile


class CustomUserAdmin(admin.ModelAdmin):

    list_display = (
        'username',
        'email',
        'first_name',
        'is_active',
        'is_staff',
        'is_superuser',
    )

    list_filter = (
        'is_active',
        'is_staff',
        'is_superuser',
    )

    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
    )

    ordering = (
        'username',
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'role',
    )

    list_filter = (
        'role',
    )

    search_fields = (
        'user__username',
        'user__email',
    )


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)