# chat/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from volunteer_app.models import Request
from .models import Chat, Message
from .forms import MessageForm
from authentication.decorators import login_required, volunteer
from django.db.models import Count, Q, Exists, OuterRef
from django.urls import reverse

User = get_user_model()

@login_required
def chat_list(request):
    """
    Display a list of chats for the current user.
    
    Retrieves all chats where the current user is a participant and annotates
    each chat with information about unread messages.
    
    Args:
        request: HttpRequest object containing metadata about the request
        
    Returns:
        HttpResponse object rendering the chat list template with context
    """
    # Get all chats with unread message status
    chats = request.user.chats.all().prefetch_related(
        'messages', 
        'participants', 
        'request'
    )
    
    # Annotate each chat with unread message count
    for chat in chats:
        chat.has_unread = chat.messages.filter(is_read=False).exclude(sender=request.user).exists()
    
    return render(request, 'chat/chat_list.html', {'chats': chats})

@login_required
def start_chat(request, request_id):
    """
    Initiate a chat session based on a volunteer request.
    
    Finds or creates a chat between the current user and the author of the specified
    military request.
    
    Args:
        request: HttpRequest object containing metadata about the request
        request_id: The ID of the military request to create a chat for
        
    Returns:
        HttpResponseRedirect to the chat detail page if successful
        HttpResponseRedirect to search page if the request author cannot be found
    """
    military_request = get_object_or_404(Request, id=request_id)
    
    # Ensure we have the author user
    if not hasattr(military_request, 'author') or not hasattr(military_request.author, 'user'):
        return redirect(reverse('volunteer_app:search'))
    
    author_user = military_request.author.user

    # Look for existing chat
    chat = Chat.objects.filter(
        request=military_request,
        participants=request.user
    ).first()
    
    if not chat:
        chat = Chat.objects.create(request=military_request)
        chat.participants.add(request.user, author_user)
    
    return redirect(reverse('chat:chat_detail', kwargs={'chat_id': chat.id}))

@login_required
def chat_detail(request, chat_id):
    """
    Display a specific chat conversation and handle message posting.
    
    Gets the chat with the specified ID, displays its messages, and processes
    new message submissions. Also marks unread messages as read when viewed
    by the recipient.
    
    Args:
        request: HttpRequest object containing metadata about the request
        chat_id: The ID of the chat to display
        
    Returns:
        HttpResponse object rendering the chat detail template with messages
        HttpResponseRedirect back to the same page after posting a message
    """
    # Get the chat with participants preloaded
    chat = get_object_or_404(
        Chat.objects.prefetch_related('participants', 'messages', 'request'), 
        id=chat_id, 
        participants=request.user
    )
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.chat = chat
            message.sender = request.user
            message.save()

            # Update chat timestamp
            chat.save()
            
            return redirect(reverse('chat:chat_detail', kwargs={'chat_id': chat.id}))
    else:
        form = MessageForm()
    
    # Mark messages as read
    chat.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    return render(request, 'chat/chat_detail.html', {
        'chat': chat,
        'messages': chat.messages.all(),
        'form': form,
        'recipient': chat.participants.exclude(id=request.user.id).first()
    })