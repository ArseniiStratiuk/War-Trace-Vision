from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile
import json

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profiles'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'category')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Category', {'fields': ('category',)}),
        ('Request Data', {'fields': ('request_data',)}), #Renamed
        ('Contacts', {'fields': ('contacts',)}), #Added contacts field
    )

    def category(self, obj):
        try:
            return obj.profile.category
        except UserProfile.DoesNotExist:
            return None

    category.short_description = 'Category'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            user_profile = obj.profile
        except UserProfile.DoesNotExist:
            user_profile = UserProfile(user=obj)

        if 'category' in form.cleaned_data:
            user_profile.category = form.cleaned_data['category']

        if 'request_data' in form.cleaned_data:
            try:
                json.loads(form.cleaned_data['request_data'])
                user_profile.request_data = form.cleaned_data['request_data']
            except json.JSONDecodeError:
                pass

        if 'contacts' in form.cleaned_data:
            try:
                json.loads(form.cleaned_data['contacts'])
                user_profile.contacts = form.cleaned_data['contacts']
            except json.JSONDecodeError:
                pass

        user_profile.save()

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)