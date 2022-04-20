from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.
from account.models import UsersModel

if settings.DEBUG:  # 正式环境不要放出来
    @admin.register(UsersModel)
    class UserModelAdmin(UserAdmin):
        list_display = ["id", 'username', 'is_staff', 'is_active', 'is_superuser']
        list_filter = ['email', 'username', 'is_staff', 'is_active', 'is_superuser']
        search_fields = ['email', 'username']
        fieldsets = (
            (None, {'fields': ('email', 'password')}),
            ('Personal info', {'fields': ('username', 'avatar')}),
            ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        )
        add_fieldsets = (
            (None, {
                'classes': ('wide',),
                'fields': ('email', 'username', 'password1', 'password2', 'avatar')
            }),
        )
