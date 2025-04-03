from django.shortcuts import render, redirect
from .models import Request

def request_list(request):
    current_request = Request.objects.filter(status="pending").first()
    return render(request, 'volunteer_app/request_list.html', {'current_request': current_request})

def accept_request(request, request_id):
    request_obj = Request.objects.get(id=request_id)
    request_obj.status = "accepted"
    request_obj.save()
    return redirect('chat')

def reject_request(request, request_id):
    request_obj = Request.objects.get(id=request_id)
    request_obj.status = "rejected"
    request_obj.save()
    return redirect('home')

def chat_list(request):
    return render(request, 'volunteer_app/chat.html')

def profile(request):
    return render(request, 'volunteer_app/profile.html')

def map_view(request):
    return render(request, 'volunteer_app/map.html')
