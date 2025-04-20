# chat/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from volunteer_app.models import Request
from .models import Chat, Message
from .forms import MessageForm
from authentication.decorators import login_required, volunteer

User = get_user_model()

@login_required
def chat_list(request):
    chats = request.user.chats.all()
    return render(request, 'chat/chat_list.html', {'chats': chats})

@login_required
def start_chat(request, request_id):
    military_request = get_object_or_404(Request, id=request_id)
    
    author_user = military_request.author.user

    chat = Chat.objects.filter(
        request=military_request,
        participants=request.user
    ).first()
    
    if not chat:
        chat = Chat.objects.create(request=military_request)
        chat.participants.add(request.user, author_user)
    
    return redirect('chat:chat_detail', chat_id=chat.id)


@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.chat = chat
            message.sender = request.user
            message.save()

            chat.save()
            
            return redirect('chat:chat_detail', chat_id=chat.id)
    else:
        form = MessageForm()
    

    chat.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    return render(request, 'chat/chat_detail.html', {
        'chat': chat,
        'messages': chat.messages.all(),
        'form': form,
        'recipient': chat.participants.exclude(id=request.user.id).first()
    })