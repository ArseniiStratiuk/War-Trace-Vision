#volunteer_app/vies.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Request, VolunteerViewedRequest
from authentication.decorators import login_required, volunteer
from django.urls import reverse
from django.db.models import Prefetch, Max, OuterRef, Subquery
from chat.models import Chat, Message


@login_required
@volunteer
def request_list(request):
    current_request = Request.objects.filter(status='in_search').exclude(
        viewed_requests__user=request.user.profile, volunteer=None
    ).first()
    return render(request, 'volunteer_app/request_list.html', {
        'current_request': current_request
    })

@login_required
@volunteer
def accept_request(request, request_id):
    request_obj = get_object_or_404(Request, id=request_id)
    user_profile = request.user.profile
    request_obj.volunteer = user_profile
    request_obj.status = "in_progress"
    request_obj.save()
    VolunteerViewedRequest.objects.get_or_create(user=user_profile, req=request_obj)
    return redirect('volunteer_app:search')

@login_required
@volunteer
def reject_request(request, request_id):
    request_obj = get_object_or_404(Request, id=request_id)
    VolunteerViewedRequest.objects.get_or_create(user=request.user.profile, req=request_obj)
    return redirect('volunteer_app:search')

@login_required
@volunteer
def start_chat_and_redirect(request, request_id):
    """
    Перенаправляє користувача до чату з автором запиту
    """
    return redirect('chat:start_chat', request_id=request_id)

@login_required
def create_request(request):
    if request.method == 'POST':
        form = Request(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.user = request.user.profile
            req.save()
            return redirect('volunteer_app:search')
    else:
        form = Request()
    return render(request, 'volunteer_app/create_request.html', {'form': form})
from chat.models import Chat


@login_required
def chat_history(request):
    user_chats = Chat.objects.filter(
        participants=request.user
    ).select_related(
        'request'
    ).prefetch_related(
        'participants', 
        Prefetch(
            'messages', 
            queryset=Message.objects.order_by('-timestamp'),
            to_attr='message_list'
        )
    ).order_by('-updated_at')
    return render(request, 'volunteer_app/chat_history.html', {'chats': user_chats})