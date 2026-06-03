from django.contrib import admin
from django.contrib.auth.models import User
from .models import Profile


class CustomUserAdmin(admin.ModelAdmin):

    list_display = (
        'username',
        'email',
        'get_id_value',
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
    )

    ordering = ('username',)

    def get_id_value(self, obj):
        return obj.first_name

    get_id_value.short_description = "Roll No / Staff ID"


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'role',
        'user_id_value',
    )

    list_filter = (
        'role',
    )

    search_fields = (
        'user__username',
        'user__email',
    )

    def user_id_value(self, obj):
        return obj.user.first_name

    user_id_value.short_description = "Roll No / Staff ID"


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)