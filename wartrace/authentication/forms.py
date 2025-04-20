from django import forms
from django.contrib.auth.models import User
from .models import UserProfile
import json

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Пароль'}), help_text='Пароль')
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'placeholder': 'Повторіть пароль'}), help_text='Повторіть пароль')
    category = forms.ChoiceField(choices=UserProfile.CATEGORY_CHOICES, help_text='Виберіть категорію') #add category

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username' : forms.TextInput(attrs={'placeholder':"Ім'я користувача"}),
            'email': forms.TextInput(attrs={'placeholder':"Введіть ваш email"}),
            'first_name': forms.TextInput(attrs={'placeholder':"Ваше ім'я"}),
            'last_name': forms.TextInput(attrs={'placeholder':"Ваше прізвище"}),
        }
        help_texts = {
            'username': "Ваше ім'я користувача",
            'email': "Введіть ваш email",
            'first_name': "Ваше ім'я",
            'last_name': "Ваше прізвище",
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.Meta.fields:
            self.fields[field_name].required = True
        self.fields['category'].required = True
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

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
    phone = forms.CharField(label='Номер телефону', required=False)
    socials_title = forms.CharField(label='Назва соц. мережі', required=False)
    socials_link = forms.URLField(label='Посилання на соц. мережі', required=False)