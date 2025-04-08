"""
Process and manage markers on the map.
This module handles the creation, deletion, and retrieval of markers on the map.
"""
from datetime import datetime
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.core.files.storage import default_storage
from django.urls import reverse
from django.forms import modelformset_factory
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import models, transaction
import json

from .models import Marker, MarkerFile, Comment, MarkerReport
from .forms import MarkerForm, MarkerFileForm


@login_required
def edit_marker_view(request, marker_id):
    """Render the marker editing page."""
    marker = get_object_or_404(Marker, id=marker_id)

    # Check if user has permission to edit this marker
    if marker.user != request.user and not request.user.is_staff:
        return render(request, '403.html', status=403)
    
    # Create formset for files associated with the marker
    MarkerFileFormSet = modelformset_factory(MarkerFile, form=MarkerFileForm, extra=0)
    formset = MarkerFileFormSet(queryset=marker.files.all())

    return render(request, 'marker-edit.html', {'marker': marker, 'formset': formset})


@login_required
@require_http_methods(["POST"])
def edit_marker_submit(request, marker_id):
    """Handle marker editing form submission."""
    marker = get_object_or_404(Marker, id=marker_id)

    # Check if user has permission to edit this marker
    if marker.user != request.user and not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Permission denied'
        }, status=403)

    # Handle form submission
    if request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                form = MarkerForm(data, instance=marker)
            else:
                form = MarkerForm(request.POST, instance=marker)
                
            if form.is_valid():
                form.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Marker updated successfully',
                    'redirect': reverse('marker_detail', args=[marker.id])
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Form validation failed',
                    'errors': form.errors
                }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating marker: {str(e)}'
            }, status=500)

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)


@login_required
@require_http_methods(["POST"])
def add_comment(request, marker_id):
    """Handle comment submission for a marker."""
    marker = get_object_or_404(Marker, id=marker_id)
    
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            text = data.get('text', '')
        else:
            text = request.POST.get('text', '')
        
        if not text.strip():
            return JsonResponse({
                'success': False,
                'message': 'Comment text cannot be empty'
            }, status=400)
            
        comment = Comment(marker=marker, user=request.user, text=text)
        comment.save()
        
        # Return data for updating the UI
        return JsonResponse({
            'success': True,
            'id': comment.id,
            'text': comment.text,
            'username': comment.user.username,
            'date': comment.created_at.strftime('%Y-%m-%d'),
            'is_verified': hasattr(request.user, 'profile') and request.user.profile.is_verified
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error adding comment: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def add_media(request, marker_id):
    """Handle media file uploads for a marker."""
    marker = get_object_or_404(Marker, id=marker_id)
    
    # Check if user has permission to add media
    if marker.user != request.user and not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Permission denied'
        }, status=403)
    
    try:
        # Handle file uploads
        files = request.FILES.getlist('file')  # Changed from 'files' to 'file' to match the HTML form
        uploaded_files = []
        
        for file in files:
            file_instance = MarkerFile(marker=marker, file=file)
            file_instance.save()
            
            uploaded_files.append({
                'id': file_instance.id,
                'url': file_instance.file.url,
                'name': file_instance.file.name,
                'uploaded_at': file_instance.uploaded_at.strftime('%Y-%m-%d')
            })
        
        # If it's an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'files': uploaded_files
            })
        
        # Otherwise redirect to the marker detail page
        return redirect('marker_detail', marker_id=marker.id)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error uploading files: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def verify_marker(request, marker_id):
    """Handle marker verification."""
    # Only staff members can verify markers
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Permission denied'
        }, status=403)
    
    marker = get_object_or_404(Marker, id=marker_id)
    
    try:
        data = json.loads(request.body) if request.body else {}
        verification = data.get('verification')
        
        if verification in [choice[0] for choice in Marker.VERIFICATION_CHOICES]:
            marker.verification = verification
            marker.save()
            
            return JsonResponse({
                'success': True,
                'verification': marker.verification
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid verification status'
            }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error verifying marker: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def upvote_marker(request, marker_id):
    """Handle marker upvoting."""
    marker = get_object_or_404(Marker, id=marker_id)
    
    # Toggle upvote
    if request.user in marker.upvotes.all():
        marker.upvotes.remove(request.user)
        action = 'removed'
    else:
        marker.upvotes.add(request.user)
        action = 'added'
    
    return JsonResponse({
        'success': True,
        'action': action,
        'upvotes': marker.upvote_count
    })


@login_required
@require_http_methods(["POST"])
def upvote_comment(request, comment_id):
    """Handle comment upvoting."""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Toggle upvote
    if request.user in comment.upvotes.all():
        comment.upvotes.remove(request.user)
        action = 'removed'
    else:
        comment.upvotes.add(request.user)
        action = 'added'
    
    return JsonResponse({
        'success': True,
        'action': action,
        'votes': comment.votes
    })


@login_required
@require_http_methods(["POST"])
def report_marker(request, marker_id):
    """Handle marker reporting."""
    marker = get_object_or_404(Marker, id=marker_id)
    
    try:
        data = json.loads(request.body) if request.body else {}
        reason = data.get('reason', '')
        
        if not reason.strip():
            return JsonResponse({
                'success': False,
                'message': 'Report reason cannot be empty'
            }, status=400)
        
        # Create report
        report = MarkerReport(
            marker=marker,
            user=request.user,
            reason=reason
        )
        report.save()
        
        # Update marker status to disputed if it has multiple reports
        if marker.reports.count() >= 3 and marker.verification != 'disputed':
            marker.verification = 'disputed'
            marker.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Report submitted successfully'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error reporting marker: {str(e)}'
        }, status=500)


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
        # Get the first image file as thumbnail if available
        thumbnail_url = None
        if marker.files.exists():
            first_file = marker.files.first()
            if hasattr(first_file, 'file') and first_file.file and hasattr(first_file.file, 'url'):
                thumbnail_url = first_file.file.url
        
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
            'upvotes': marker.upvote_count,
            'thumbnail': thumbnail_url
        })
    
    return JsonResponse({'markers': markers_list})


def index(request):
    """Render the main map view."""
    return render(request, 'map.html')


@login_required
def create_marker_view(request):
    """Render the marker creation page."""
    return render(request, 'marker-create.html')


@login_required
@require_http_methods(["POST"])
def create_marker(request):
    """Handle marker creation form submission."""
    try:
        # Parse form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            # Handle form data
            data = request.POST.dict()

            # Convert string boolean values to actual booleans
            for key in ['object_detection', 'camouflage_detection', 'damage_assessment', 
                        'thermal_analysis', 'request_verification']:
                if key in data:
                    data[key] = data[key].lower() == 'true'

        # Create marker instance
        marker = Marker(
            user=request.user,
            title=data.get('title'),
            description=data.get('description'),
            latitude=float(data.get('latitude', 0)),
            longitude=float(data.get('longitude', 0)),
            date=datetime.strptime(data.get('date'), '%Y-%m-%d').date() if data.get('date') else timezone.now(),
            category=data.get('category', 'infrastructure'),
            source=data.get('source', ''),
            visibility=data.get('visibility', 'private'),
            object_detection=data.get('object_detection', False),
            camouflage_detection=data.get('camouflage_detection', False),
            damage_assessment=data.get('damage_assessment', False),
            thermal_analysis=data.get('thermal_analysis', False),
            request_verification=data.get('request_verification', False)
        )
        marker.save()

        # Handle file uploads
        files = request.FILES.getlist('files')
        for file in files:
            file_instance = MarkerFile(marker=marker, file=file)
            file_instance.save()

        # If request verification is enabled, update marker verification status
        if marker.request_verification:
            marker.verification = 'pending'
            marker.save()

        return redirect('marker_detail', marker_id=marker.id)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating marker: {str(e)}'
        }, status=400)


def marker_detail(request, marker_id):
    """Render the marker detail page."""
    marker = get_object_or_404(Marker, id=marker_id)

    # Check if user has permission to view this marker
    if marker.visibility == 'private' and (not request.user.is_authenticated or marker.user != request.user):
        return render(request, '403.html', status=403)
    
    # If marker is for verified users only, check if user is verified
    if marker.visibility == 'verified_only' and (not request.user.is_authenticated or 
                                               not hasattr(request.user, 'profile') or 
                                               not request.user.profile.is_verified):
        return render(request, '403.html', status=403)
    
    # Get comments for the marker
    comments = Comment.objects.filter(marker=marker).order_by('-created_at')
        
    return render(request, 'marker-detail.html', {
        'marker': marker,
        'comments': comments,
    })


@login_required
@require_http_methods(["DELETE"])
def delete_marker(request, marker_id):
    """Handle marker deletion."""
    marker = get_object_or_404(Marker, id=marker_id)
    
    # Check if user has permission to delete
    if marker.user != request.user and not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Permission denied'
        }, status=403)
    
    try:    
        # Delete associated files from storage
        for file_obj in marker.files.all():
            if default_storage.exists(file_obj.file.name):
                default_storage.delete(file_obj.file.name)
        
        # Delete marker
        marker.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Marker deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting marker: {str(e)}'
        }, status=500)
