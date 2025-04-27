from django.shortcuts import render, redirect
from .forms import UserRegistrationForm, ContactForm 
from volunteer_app.forms import RequestForm
from volunteer_app.models import Request
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from authentication.decorators import login_required
from volunteer_app.models import VolunteerViewedRequest
from content.models import Marker # Import Marker model

from .models import UserProfile
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) #login the user after registration
            return redirect('personal_page')  # Redirect to a success page
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
            return render(request, 'registration/login.html', {'form': form, 'error': 'Invalid Credentials'}) #handle error
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def user_logout(request):
    """Handle user logout."""
    logout(request)
    return redirect('login')

@login_required
def personal_page(request):
    if not request.user.is_authenticated:
        return redirect('login')

    user_profile = request.user.profile

    contacts = user_profile.get_contacts()
    if user_profile.category == 'both':
        both_request_data = (("Військовий(-а)",user_profile.requests.all().order_by('-id')), ("Волонтер(-ка)",user_profile.volunteer_req.all().order_by('-id')))
        request_data = None
    elif user_profile.category == 'soldier':
        request_data = user_profile.requests.all()
        request_data = request_data.order_by('-id')
        both_request_data = None
    else:
        request_data = user_profile.volunteer_req.all()
        request_data = request_data.order_by('-id')
        both_request_data = None
    request_form = RequestForm() if user_profile.category in ('soldier', 'both') else None
    contact_form = ContactForm(initial={
        'phone': contacts.get('phone', ''),
        'socials_title': contacts.get('socials', {}).get('title', ''),
        'socials_link': contacts.get('socials', {}).get('link', ''),
    })
    # Fetch markers created by the current user
    my_markers = Marker.objects.filter(user=request.user).order_by('-created_at')

    if request.method == 'POST':
        if 'name' in request.POST:  # Request Form submitted
            request_form = RequestForm(request.POST)
            if request_form.is_valid():
                req_obj = request_form.save(commit=False)
                req_obj.status = 'in_search'
                req_obj.author = user_profile
                req_obj.save()
                VolunteerViewedRequest.objects.get_or_create(user=request.user.profile, req=req_obj)
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

    return render(request, 'personal_page.html', {'contacts': contacts, 'request_data': request_data, 'request_form': request_form, 'contact_form': contact_form, 'my_markers': my_markers, 'both_request_data':both_request_data})

def bad_category(request):
    return render(request, 'bad_category.html')

def profile(request, volunteer_id):
    user_profile = UserProfile.objects.get(id=volunteer_id)
    if user_profile.category == 'both':
        both_request_data = (("Військовий(-а)",user_profile.requests.all().order_by('-id')), ("Волонтер(-ка)",user_profile.volunteer_req.all().order_by('-id')))
        request_data = None
    elif user_profile.category == 'soldier':
        request_data = user_profile.requests.all()
        request_data = request_data.order_by('-id')
        both_request_data = None
    else:
        request_data = user_profile.volunteer_req.all()
        request_data = request_data.order_by('-id')
        both_request_data = None
    visitor = request.user.profile
    return render(request, 'profile.html', {'user':user_profile.user, 'contacts':user_profile.get_contacts(), 'request_data': request_data, 'visitor':visitor, 'both_request_data':both_request_data})

@login_required
def req_ready(request, req_id):
    req = Request.objects.get(id=req_id)
    if request.user.profile != req.author:
        return render(request, 'bad_category.html')
    req.status = 'done'
    req.save()
    return redirect('personal_page')

def add_second_category(request):
    user_profile = request.user.profile
    if user_profile.category != 'both':
        user_profile.category = 'both'
        user_profile.save(update_fields=['category'])
    return redirect('personal_page')

@login_required
def settings(request):
    if request.method == "POST":
        user_profile = request.user.profile
        contacts = user_profile.get_contacts()
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
        return render(request, 'settings.html', {'contact_form':contact_form})
    form = ContactForm()
    return render(request, 'settings.html', {'contact_form':form})
