from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserRegistrationForm, RequestForm, ContactForm #import ContactForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from .models import UserProfile
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
import json
import uuid
from datetime import datetime

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) #login the user after registration
            return redirect('registration_success')  # Redirect to a success page
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def registration_success(request):
    return render(request, 'registration/registration_success.html')

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST) #use authentication form
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('personal_page') #redirect on success
            else:
                return render(request, 'registration/login.html', {'form': form, 'error': 'Invalid Credentials'}) #handle error
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def personal_page(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user_profile = request.user.profile

    contacts = user_profile.get_contacts()
    request_data = user_profile.get_request_data()
    request_form = RequestForm() if user_profile.category == 'soldier' else None
    contact_form = ContactForm(initial={
        'phone': contacts.get('phone', ''),
        'socials_title': contacts.get('socials', {}).get('title', ''),
        'socials_link': contacts.get('socials', {}).get('link', ''),
    })

    if request.method == 'POST':
        if 'title' in request.POST:  # Request Form submitted
            request_form = RequestForm(request.POST)
            if request_form.is_valid():
                request_id = str(uuid.uuid4())
                request_entry = {
                    'title': request_form.cleaned_data['title'],
                    'description': request_form.cleaned_data['description'],
                    'deadline': request_form.cleaned_data['deadline'].strftime('%d/%m/%Y'),
                    'approximate_price': request_form.cleaned_data['approximate_price'],
                }
                request_data[request_id] = request_entry
                user_profile.set_request_data(request_data)
                user_profile.save()
                return redirect('personal_page')
        else: # Contact Form submitted
            contact_form = ContactForm(request.POST)
            if contact_form.is_valid():
                contacts['phone'] = contact_form.cleaned_data['phone']
                contacts['socials'] = {
                    'title': contact_form.cleaned_data['socials_title'],
                    'link': contact_form.cleaned_data['socials_link'],
                }
                user_profile.set_contacts(contacts)
                user_profile.save()
                return redirect('personal_page')

    return render(request, 'personal_page.html', {'contacts': contacts, 'request_data': request_data, 'request_form': request_form, 'contact_form': contact_form})
