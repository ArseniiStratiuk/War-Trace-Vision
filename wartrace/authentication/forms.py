from django import forms
from django.contrib.auth.models import User
from .models import UserProfile
import json

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    category = forms.ChoiceField(choices=UserProfile.CATEGORY_CHOICES) #add category

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError("Passwords don't match.")
        return cd['password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            UserProfile.objects.create(user=user, category=self.cleaned_data['category']) #create profile
        return user

class ContactForm(forms.Form):
    phone = forms.CharField(label='Phone', required=False)
    socials_title = forms.CharField(label='Socials Title', required=False)
    socials_link = forms.URLField(label='Socials Link', required=False)

class RequestForm(forms.Form):
    title = forms.CharField()
    description = forms.CharField(widget=forms.Textarea)
    deadline = forms.DateField(input_formats=['%d/%m/%Y']) #dd/mm/yyyy
    approximate_price = forms.IntegerField(label="Приблизна ціна (грн)")
