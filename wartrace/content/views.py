from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.forms import modelformset_factory
from .models import Marker, MarkerFile
from .forms import MarkerForm, MarkerFileForm
from django.db import models
import json

@login_required()
def marker_create(request):
    if request.method == 'POST':
        form = MarkerForm(request.POST)
        if form.is_valid():
            # Create marker but don't save to database yet
            marker = form.save(commit=False)
            marker.user = request.user
            
            # Default to unverified status when created
            marker.verification = 'unverified'
            marker.save()

            # Handle file uploads
            files = request.FILES.getlist('files')
            for file in files:
                MarkerFile.objects.create(marker=marker, file=file)
                
            return redirect('marker_detail', pk=marker.pk)
    else:
        form = MarkerForm()
    
    return render(request, 'marker-create.html', {
        'form': form
    })

@login_required()
def marker_detail(request, pk):
    marker = get_object_or_404(Marker, pk=pk)
    files = marker.files.all()
    
    # Check if user has permission to view this marker
    if marker.visibility == 'private' and marker.user != request.user:
        return redirect('map')
    
    return render(request, 'marker-detail.html', {
        'marker': marker,
        'files': files
    })

def marker_api(request):
    """API endpoint to get markers for map display"""
    user = request.user
    
    # Filter markers based on visibility and user
    markers = Marker.objects.all()
    
    if not user.is_authenticated:
        # For anonymous users, only show public markers
        markers = markers.filter(visibility='public')
    else:
        # For logged in users, show public markers, their own markers, and verified_only if they are staff
        if user.is_staff:
            # Staff can see all markers
            pass
        else:
            # Regular users can see public markers and their own private markers
            markers = markers.filter(
                models.Q(visibility='public') | 
                models.Q(visibility='verified_only', verification='verified') |
                models.Q(user=user)
            )
    
    # Convert markers to JSON
    markers_list = []
    for marker in markers:
        markers_list.append({
            'id': marker.id,
            'lat': marker.latitude,
            'lng': marker.longitude,
            'title': marker.title,
            'description': marker.description,
            'date': marker.date.strftime('%Y-%m-%d'),
            'confidence': f"{marker.confidence}%",
            'category': marker.category,
            'verification': marker.verification,
            'source': marker.source,
            'user': marker.user.username,
        })
    
    return JsonResponse({'markers': markers_list})
