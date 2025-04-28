"""
Process and manage markers on the map.
This module handles the creation, deletion, and retrieval of markers on the map.
"""
from datetime import datetime
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.core.files.storage import default_storage
from django.urls import reverse
from django.forms import modelformset_factory
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import models, transaction
import json
import logging

from .models import Marker, MarkerFile, Comment, MarkerReport
from .forms import MarkerForm, MarkerFileForm

# Configure logging
logger = logging.getLogger(__name__)


@login_required
def edit_marker_view(request, marker_id):
    """
    Render the marker editing page.
    
    Args:
        request: The HTTP request object
        marker_id: The ID of the marker to edit
        
    Returns:
        HttpResponse: Rendered template for editing the marker
        
    Raises:
        Http404: If the marker does not exist
        PermissionDenied: If the user is not the owner of the marker
    """
    print(f"[edit_marker_view] Entering function with marker_id: {marker_id}")
    logger.info(f"User {request.user.username} is attempting to edit marker {marker_id}")
    
    marker = get_object_or_404(Marker, id=marker_id)
    print(f"[edit_marker_view] Retrieved marker: {marker.title} (ID: {marker.id})")

    # Check if user is the owner of this marker
    if marker.user != request.user:
        print(f"[edit_marker_view] Permission denied for user {request.user.username} to edit marker {marker_id}")
        logger.warning(f"Permission denied: User {request.user.username} attempted to edit marker {marker_id} owned by {marker.user.username}")
        return render(request, '403.html', status=403)

    print(f"[edit_marker_view] Rendering edit page for marker {marker_id}")
    return render(request, 'marker-edit.html', {'marker': marker})


@login_required
@require_http_methods(["POST"])
def edit_marker_submit(request, marker_id):
    """
    Handle marker editing form submission.
    
    Updates a marker with the data provided in the form, including metadata,
    visibility settings, and detection options. Also processes any new files.
    
    Args:
        request: The HTTP request object containing form data
        marker_id: The ID of the marker to edit
        
    Returns:
        JsonResponse: Result of the operation with success status and message
        
    Raises:
        Http404: If the marker does not exist
        PermissionDenied: If the user is not the owner of the marker
    """
    print(f"[edit_marker_submit] Entering function with marker_id: {marker_id}")
    logger.info(f"User {request.user.username} is submitting edits for marker {marker_id}")
    
    marker = get_object_or_404(Marker, id=marker_id)
    print(f"[edit_marker_submit] Retrieved marker: {marker.title} (ID: {marker.id})")

    # Check if user is the owner of this marker
    if marker.user != request.user:
        print(f"[edit_marker_submit] Permission denied for user {request.user.username} to edit marker {marker_id}")
        logger.warning(f"Permission denied: User {request.user.username} attempted to submit edits for marker {marker_id}")
        return JsonResponse({
            'success': False,
            'message': 'Permission denied'
        }, status=403)

    try:
        print(f"[edit_marker_submit] Processing form data for marker {marker_id}")
        # Update marker fields from form data
        marker.title = request.POST.get('title', marker.title)
        marker.description = request.POST.get('description', marker.description)
        marker.latitude = float(request.POST.get('latitude', marker.latitude))
        marker.longitude = float(request.POST.get('longitude', marker.longitude))
        marker.source = request.POST.get('source', marker.source)
        marker.category = request.POST.get('category', marker.category)
        marker.visibility = request.POST.get('visibility', marker.visibility)
        
        print(f"[edit_marker_submit] Updated marker data: title={marker.title}, lat={marker.latitude}, lng={marker.longitude}")
        
        # Parse date string
        date_str = request.POST.get('date')
        if date_str:
            marker.date = datetime.strptime(date_str, '%Y-%m-%d').date()
            print(f"[edit_marker_submit] Updated date to {marker.date}")
        
        # Update boolean fields for AI processing
        marker.object_detection = request.POST.get('object_detection') == 'on'
        marker.military_detection = request.POST.get('military_detection') == 'on'
        marker.damage_assessment = request.POST.get('damage_assessment') == 'on'
        marker.emergency_recognition = request.POST.get('emergency_recognition') == 'on'
        marker.request_verification = request.POST.get('request_verification') == 'on'
        
        print(f"[edit_marker_submit] Updated boolean fields: object_detection={marker.object_detection}, "
              f"military_detection={marker.military_detection}, damage_assessment={marker.damage_assessment}, "
              f"emergency_recognition={marker.emergency_recognition}, request_verification={marker.request_verification}")
        
        # If request verification is enabled, update marker verification status
        if marker.request_verification and marker.verification != 'verified':
            marker.verification = 'pending'
            print(f"[edit_marker_submit] Updated verification status to 'pending'")
        
        # Save the updated marker
        marker.save()
        print(f"[edit_marker_submit] Marker {marker_id} saved successfully")
        
        # Handle file uploads - carefully add new files without replacing existing ones
        files = request.FILES.getlist('files')
        print(f"[edit_marker_submit] Processing {len(files)} files for marker {marker_id}")
        
        for i, file in enumerate(files):
            print(f"[edit_marker_submit] Saving file {i+1}/{len(files)}: {file.name}")
            MarkerFile.objects.create(marker=marker, file=file)
        
        print(f"[edit_marker_submit] All files processed successfully")
        logger.info(f"User {request.user.username} successfully updated marker {marker_id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Marker updated successfully',
            'redirect': reverse('content:marker_detail', args=[marker.id])
        })
    except Exception as e:
        print(f"[edit_marker_submit] Error updating marker {marker_id}: {str(e)}")
        logger.error(f"Error updating marker {marker_id}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Error updating marker: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def delete_media(request, marker_id, file_id):
    """
    Delete a media file associated with a marker.
    
    Removes the file both from storage and the database.
    
    Args:
        request: The HTTP request object
        marker_id: The ID of the marker
        file_id: The ID of the file to delete
        
    Returns:
        JsonResponse: Result of the operation with success status
        
    Raises:
        Http404: If the marker or file does not exist
        PermissionDenied: If the user is not the owner of the marker
    """
    print(f"[delete_media] Entering function with marker_id: {marker_id}, file_id: {file_id}")
    logger.info(f"User {request.user.username} is attempting to delete file {file_id} from marker {marker_id}")
    
    marker = get_object_or_404(Marker, id=marker_id)
    print(f"[delete_media] Retrieved marker: {marker.title} (ID: {marker.id})")
    
    # Check if user is the owner of the marker
    if marker.user != request.user:
        print(f"[delete_media] Permission denied for user {request.user.username}")
        logger.warning(f"Permission denied: User {request.user.username} attempted to delete file {file_id}")
        return JsonResponse({
            'success': False,
            'message': 'Permission denied'
        }, status=403)
    
    try:
        # Get the file
        file_obj = get_object_or_404(MarkerFile, id=file_id, marker=marker)
        print(f"[delete_media] Retrieved file: {file_obj.file.name}")
        
        # Delete file from storage
        if default_storage.exists(file_obj.file.name):
            print(f"[delete_media] Deleting file from storage: {file_obj.file.name}")
            default_storage.delete(file_obj.file.name)
        else:
            print(f"[delete_media] File not found in storage: {file_obj.file.name}")
        
        # Delete database record
        print(f"[delete_media] Deleting file record from database")
        file_obj.delete()
        
        print(f"[delete_media] File {file_id} deleted successfully")
        logger.info(f"User {request.user.username} successfully deleted file {file_id} from marker {marker_id}")
        
        return JsonResponse({
            'success': True,
            'message': 'File deleted successfully'
        })
    except Exception as e:
        print(f"[delete_media] Error deleting file {file_id}: {str(e)}")
        logger.error(f"Error deleting file {file_id}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Error deleting file: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def add_comment(request, marker_id):
    """
    Handle comment submission for a marker.
    
    Creates a new comment on the specified marker after verifying
    the user has permission to view and comment on it.
    
    Args:
        request: The HTTP request object containing comment data
        marker_id: The ID of the marker to comment on
        
    Returns:
        JsonResponse: Contains the created comment data or error details
        
    Raises:
        Http404: If the marker does not exist
        PermissionDenied: If the user cannot view the marker
    """
    print(f"[add_comment] Entering function with marker_id: {marker_id}")
    logger.info(f"User {request.user.username} is attempting to add a comment to marker {marker_id}")
    
    marker = get_object_or_404(Marker, id=marker_id)
    print(f"[add_comment] Retrieved marker: {marker.title} (ID: {marker.id})")

    # Check view permission before allowing comment
    can_view = False
    if marker.visibility == 'public':
        can_view = True
    elif request.user.is_authenticated:
        if marker.visibility == 'private' and marker.user == request.user: # Only owner for private
            can_view = True
        elif marker.visibility == 'verified_only' and (request.user.is_staff or marker.user == request.user): # Staff or owner for verified_only
             can_view = True
        # Add check for verified users if you have a specific field/group for that
        # elif marker.visibility == 'verified_only' and request.user.profile.is_verified: # Example check
        #     can_view = True

    if not can_view:
        print(f"[add_comment] Permission denied: User {request.user.username} cannot view marker {marker_id}")
        logger.warning(f"Permission denied: User {request.user.username} attempted to comment on inaccessible marker {marker_id}")
        return JsonResponse({
            'success': False,
            'message': 'Permission denied to view or comment on this marker.'
        }, status=403)

    try:
        # Extract comment text based on content type
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            text = data.get('text', '')
            print(f"[add_comment] Received JSON comment: {text[:50]}{'...' if len(text) > 50 else ''}")
        else:
            text = request.POST.get('text', '')
            print(f"[add_comment] Received form comment: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        if not text.strip():
            print("[add_comment] Comment text is empty")
            return JsonResponse({
                'success': False,
                'message': 'Comment text cannot be empty'
            }, status=400)
            
        comment = Comment(marker=marker, user=request.user, text=text)
        comment.save()
        print(f"[add_comment] Comment saved with ID: {comment.id}")
        
        # Use the built-in is_staff attribute directly
        is_staff = request.user.is_staff
        print(f"[add_comment] User staff status: {is_staff}")
        
        logger.info(f"User {request.user.username} successfully added comment {comment.id} to marker {marker_id}")
        
        # Return data for updating the UI
        return JsonResponse({
            'success': True,
            'id': comment.id,
            'text': comment.text,
            'username': request.user.username,
            'date': comment.created_at.strftime('%Y-%m-%d'),
            'is_staff': is_staff  # Changed property name to match HTML template
        })
    except Exception as e:
        print(f"[add_comment] Error adding comment: {str(e)}")
        logger.error(f"Error adding comment to marker {marker_id}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Error adding comment: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def add_media(request, marker_id):
    """
    Handle media file uploads for a marker.
    
    Processes and saves file uploads for the specified marker,
    creating MarkerFile instances for each uploaded file.
    
    Args:
        request: The HTTP request object containing uploaded files
        marker_id: The ID of the marker to add media to
        
    Returns:
        JsonResponse or HttpResponseRedirect: Information about uploaded files
            or redirect to marker detail page
            
    Raises:
        Http404: If the marker does not exist
        PermissionDenied: If the user is not the owner of the marker
    """
    print(f"[add_media] Entering function with marker_id: {marker_id}")
    logger.info(f"User {request.user.username} is attempting to add media to marker {marker_id}")
    
    marker = get_object_or_404(Marker, id=marker_id)
    print(f"[add_media] Retrieved marker: {marker.title} (ID: {marker.id})")
    
    # Check if user is the owner of the marker
    if marker.user != request.user:
        print(f"[add_media] Permission denied for user {request.user.username}")
        logger.warning(f"Permission denied: User {request.user.username} attempted to add media to marker {marker_id}")
        return JsonResponse({
            'success': False,
            'message': 'Permission denied'
        }, status=403)
    
    try:
        # Handle file uploads
        files = request.FILES.getlist('file')  # Get all files with name 'file'
        print(f"[add_media] Processing {len(files)} files for marker {marker_id}")
        
        if not files:
            return JsonResponse({
                'success': False,
                'message': 'No files were uploaded'
            }, status=400)
        
        uploaded_files = []
        
        for i, file in enumerate(files):
            print(f"[add_media] Processing file {i+1}/{len(files)}: {file.name}, size: {file.size} bytes")
            
            # Create a new MarkerFile instance for each file
            file_instance = MarkerFile(marker=marker, file=file)
            file_instance.save()
            print(f"[add_media] File saved with ID: {file_instance.id}")
            
            uploaded_files.append({
                'id': file_instance.id,
                'url': file_instance.file.url,
                'name': file_instance.file.name,
                'uploaded_at': file_instance.uploaded_at.strftime('%Y-%m-%d')
            })
        
        print(f"[add_media] All {len(files)} files processed successfully")
        logger.info(f"User {request.user.username} successfully added {len(files)} media files to marker {marker_id}")
        
        # If it's an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            print("[add_media] Returning JSON response for AJAX request")
            return JsonResponse({
                'success': True,
                'files': uploaded_files
            })
        
        # Otherwise redirect to the marker detail page
        print(f"[add_media] Redirecting to marker detail page for marker {marker_id}")
        return redirect('content:marker_detail', marker_id=marker.id)
    
    except Exception as e:
        print(f"[add_media] Error uploading files: {str(e)}")
        logger.error(f"Error uploading files to marker {marker_id}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Error uploading files: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def verify_marker(request, marker_id):
    """
    Handle marker verification by staff members.
    
    Updates the verification status of a marker. Only accessible to staff.
    
    Args:
        request: The HTTP request object containing verification data
        marker_id: The ID of the marker to verify
        
    Returns:
        JsonResponse: Contains updated verification status or error details
        
    Raises:
        Http404: If the marker does not exist
        PermissionDenied: If the user is not a staff member
    """
    print(f"[verify_marker] Entering function with marker_id: {marker_id}")
    logger.info(f"User {request.user.username} is attempting to verify marker {marker_id}")
    
    # Only staff members can verify markers
    if not request.user.is_staff:
        print(f"[verify_marker] Permission denied: User {request.user.username} is not staff")
        logger.warning(f"Permission denied: Non-staff user {request.user.username} attempted to verify marker {marker_id}")
        return JsonResponse({
            'success': False,
            'message': 'Permission denied'
        }, status=403)
    
    marker = get_object_or_404(Marker, id=marker_id)
    print(f"[verify_marker] Retrieved marker: {marker.title} (ID: {marker.id})")
    
    try:
        data = json.loads(request.body) if request.body else {}
        verification = data.get('verification')
        print(f"[verify_marker] Requested verification status: {verification}")
        
        if verification in [choice[0] for choice in Marker.VERIFICATION_CHOICES]:
            print(f"[verify_marker] Updating marker {marker_id} verification status from '{marker.verification}' to '{verification}'")
            marker.verification = verification
            marker.save()
            
            logger.info(f"User {request.user.username} successfully changed marker {marker_id} verification status to '{verification}'")
            return JsonResponse({
                'success': True,
                'verification': marker.verification
            })
        else:
            print(f"[verify_marker] Invalid verification status: {verification}")
            return JsonResponse({
                'success': False,
                'message': 'Invalid verification status'
            }, status=400)
    
    except Exception as e:
        print(f"[verify_marker] Error verifying marker: {str(e)}")
        logger.error(f"Error verifying marker {marker_id}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Error verifying marker: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def upvote_marker(request, marker_id):
    """
    Handle marker upvoting.
    
    Toggles the current user's upvote on the specified marker.
    
    Args:
        request: The HTTP request object
        marker_id: The ID of the marker to upvote
        
    Returns:
        JsonResponse: Contains updated upvote count and action performed
        
    Raises:
        Http404: If the marker does not exist
        PermissionDenied: If the user cannot view the marker
    """
    print(f"[upvote_marker] Entering function with marker_id: {marker_id}")
    logger.info(f"User {request.user.username} is toggling upvote for marker {marker_id}")
    
    marker = get_object_or_404(Marker, id=marker_id)
    print(f"[upvote_marker] Retrieved marker: {marker.title} (ID: {marker.id})")

    # Check view permission before allowing upvote
    can_view = False
    if marker.visibility == 'public':
        can_view = True
    elif request.user.is_authenticated:
        if marker.visibility == 'private' and marker.user == request.user: # Only owner for private
            can_view = True
        elif marker.visibility == 'verified_only' and (request.user.is_staff or marker.user == request.user): # Only staff or owner
             can_view = True
        # Add check for verified users if needed

    if not can_view:
        print(f"[upvote_marker] Permission denied: User {request.user.username} cannot view marker {marker_id}")
        logger.warning(f"Permission denied: User {request.user.username} attempted to upvote inaccessible marker {marker_id}")
        return JsonResponse({
            'success': False,
            'message': 'Permission denied to view or interact with this marker.'
        }, status=403)

    # Toggle upvote
    if request.user in marker.upvotes.all():
        print(f"[upvote_marker] Removing upvote from user {request.user.username}")
        marker.upvotes.remove(request.user)
        action = 'removed'
    else:
        print(f"[upvote_marker] Adding upvote from user {request.user.username}")
        marker.upvotes.add(request.user)
        action = 'added'
    
    print(f"[upvote_marker] Updated upvote count: {marker.upvote_count}")
    logger.info(f"User {request.user.username} {action} upvote for marker {marker_id}")
    
    return JsonResponse({
        'success': True,
        'action': action,
        'upvotes': marker.upvote_count
    })


@login_required
@require_http_methods(["POST"])
def upvote_comment(request, comment_id):
    """
    Handle comment upvoting.
    
    Toggles the current user's upvote on the specified comment.
    
    Args:
        request: The HTTP request object
        comment_id: The ID of the comment to upvote
        
    Returns:
        JsonResponse: Contains updated vote count and action performed
        
    Raises:
        Http404: If the comment does not exist
        PermissionDenied: If the user cannot view the associated marker
    """
    print(f"[upvote_comment] Entering function with comment_id: {comment_id}")
    logger.info(f"User {request.user.username} is toggling upvote for comment {comment_id}")
    
    comment = get_object_or_404(Comment, id=comment_id)
    marker = comment.marker # Get the associated marker
    print(f"[upvote_comment] Retrieved comment on marker: {marker.id}")

    # Check view permission for the marker before allowing comment upvote
    can_view = False
    if marker.visibility == 'public':
        can_view = True
    elif request.user.is_authenticated:
        if marker.visibility == 'private' and marker.user == request.user: # Only owner for private
            can_view = True
        elif marker.visibility == 'verified_only' and (request.user.is_staff or marker.user == request.user): # Only staff or owner
             can_view = True
        # Add check for verified users if needed

    if not can_view:
        print(f"[upvote_comment] Permission denied: User {request.user.username} cannot view marker {marker.id}")
        logger.warning(f"Permission denied: User {request.user.username} attempted to upvote comment on inaccessible marker {marker.id}")
        return JsonResponse({
            'success': False,
            'message': 'Permission denied to view or interact with this marker.'
        }, status=403)

    # Toggle upvote
    if request.user in comment.upvotes.all():
        print(f"[upvote_comment] Removing upvote from user {request.user.username}")
        comment.upvotes.remove(request.user)
        action = 'removed'
    else:
        print(f"[upvote_comment] Adding upvote from user {request.user.username}")
        comment.upvotes.add(request.user)
        action = 'added'
    
    print(f"[upvote_comment] Updated vote count: {comment.votes}")
    logger.info(f"User {request.user.username} {action} upvote for comment {comment_id}")
    
    return JsonResponse({
        'success': True,
        'action': action,
        'votes': comment.votes
    })


@login_required
@require_http_methods(["POST"])
def report_marker(request, marker_id):
    """
    Handle marker reporting.
    
    Creates a report for the specified marker and updates the marker's
    verification status if it receives multiple reports.
    
    Args:
        request: The HTTP request object containing report reason
        marker_id: The ID of the marker to report
        
    Returns:
        JsonResponse: Contains report submission status
        
    Raises:
        Http404: If the marker does not exist
        PermissionDenied: If the user cannot view the marker
    """
    print(f"[report_marker] Entering function with marker_id: {marker_id}")
    logger.info(f"User {request.user.username} is reporting marker {marker_id}")
    
    marker = get_object_or_404(Marker, id=marker_id)
    print(f"[report_marker] Retrieved marker: {marker.title} (ID: {marker.id})")

    # Check view permission before allowing report
    can_view = False
    if marker.visibility == 'public':
        can_view = True
    elif request.user.is_authenticated:
        if marker.visibility == 'private' and marker.user == request.user: # Only owner for private
            can_view = True
        elif marker.visibility == 'verified_only' and (request.user.is_staff or marker.user == request.user): # Only staff or owner
             can_view = True
        # Add check for verified users if needed

    if not can_view:
        print(f"[report_marker] Permission denied: User {request.user.username} cannot view marker {marker_id}")
        logger.warning(f"Permission denied: User {request.user.username} attempted to report inaccessible marker {marker_id}")
        return JsonResponse({
            'success': False,
            'message': 'Permission denied to view or report this marker.'
        }, status=403)

    try:
        data = json.loads(request.body) if request.body else {}
        reason = data.get('reason', '')
        print(f"[report_marker] Report reason: {reason[:50]}{'...' if len(reason) > 50 else ''}")
        
        if not reason.strip():
            print("[report_marker] Report reason is empty")
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
        print(f"[report_marker] Report created with ID: {report.id}")
        
        # Update marker status to disputed if it has multiple reports
        report_count = marker.reports.count()
        print(f"[report_marker] Current report count: {report_count}")
        
        if report_count >= 3 and marker.verification != 'disputed':
            print(f"[report_marker] Updating marker verification status to 'disputed' due to {report_count} reports")
            marker.verification = 'disputed'
            marker.save()
        
        logger.info(f"User {request.user.username} successfully reported marker {marker_id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Report submitted successfully'
        })
    
    except Exception as e:
        print(f"[report_marker] Error reporting marker: {str(e)}")
        logger.error(f"Error reporting marker {marker_id}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Error reporting marker: {str(e)}'
        }, status=500)


def marker_api(request):
    """
    API endpoint to get markers for map display.
    
    Filters markers based on user permissions and visibility settings,
    then returns formatted marker data for the map interface.
    
    Args:
        request: The HTTP request object
        
    Returns:
        JsonResponse: Contains list of filtered markers with their metadata
    """
    print("[marker_api] Entering function")
    user = request.user
    print(f"[marker_api] User: {'Authenticated: ' + user.username if user.is_authenticated else 'Anonymous'}")

    # Base queryset
    markers_qs = Marker.objects.select_related('user').prefetch_related('files')
    print(f"[marker_api] Total markers in database: {markers_qs.count()}")

    # Filter based on user permissions
    if not user.is_authenticated:
        # Anonymous users: only public markers
        markers_qs = markers_qs.filter(visibility='public')
        print(f"[marker_api] Filtered to public markers for anonymous user")
    else:
        if user.is_staff:
            # Staff can see public and verified_only markers, plus their own private ones
            markers_qs = markers_qs.filter(
                models.Q(visibility='public') |
                models.Q(visibility='verified_only') |
                models.Q(visibility='private', user=user) # Staff see only their own private markers
            )
            print(f"[marker_api] Filtered markers for staff user {user.username}")
        else:
            # Authenticated non-staff users:
            # - Public markers
            # - Their own private markers
            # - Their own verified_only markers (if they created them)
            markers_qs = markers_qs.filter(
                models.Q(visibility='public') |
                models.Q(visibility='private', user=user) |
                models.Q(visibility='verified_only', user=user) # Only show user's own verified_only markers
            )
            print(f"[marker_api] Filtered markers for user {user.username}")

    final_count = markers_qs.count()
    print(f"[marker_api] Final marker count after filtering: {final_count}")

    # Convert markers to JSON
    markers_list = []
    print(f"[marker_api] Converting {final_count} markers to JSON")

    for i, marker in enumerate(markers_qs):
        # Get the first image file as thumbnail if available
        thumbnail_url = None
        first_file = marker.files.first() # More efficient way to get the first file
        if first_file and hasattr(first_file, 'file') and first_file.file and hasattr(first_file.file, 'url'):
            thumbnail_url = first_file.file.url

        marker_data = {
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
            'thumbnail': thumbnail_url,
            'visibility': marker.visibility # Include visibility for potential frontend logic
        }
        markers_list.append(marker_data)

        if i % 100 == 0 or i == final_count - 1:
            print(f"[marker_api] Processed marker {i+1}/{final_count}: {marker.title} (ID: {marker.id})")

    print(f"[marker_api] Returning {len(markers_list)} markers")
    return JsonResponse({'markers': markers_list})


def index(request):
    """
    Render the main map view.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Rendered map template
    """
    print("[index] Entering function")
    logger.info(f"User {request.user.username if request.user.is_authenticated else 'Anonymous'} is viewing the main map")
    return render(request, 'map.html')


@login_required
def create_marker_view(request):
    """
    Render the marker creation page.
    
    Args:
        request: The HTTP request object
        
    Returns:
        HttpResponse: Rendered marker creation template
    """
    print("[create_marker_view] Entering function")
    logger.info(f"User {request.user.username} is viewing the marker creation page")
    return render(request, 'marker-create.html')


@login_required
@require_http_methods(["POST"])
def create_marker(request):
    """
    Handle marker creation form submission.
    
    Processes form data to create a new marker with specified attributes,
    handles file uploads, and sets verification status if requested.
    
    Args:
        request: The HTTP request object containing form data
        
    Returns:
        JsonResponse: Contains marker creation status and the new marker ID
        
    Raises:
        Exception: If marker creation fails due to invalid data or server error
    """
    print("[create_marker] Entering function")
    logger.info(f"User {request.user.username} is creating a new marker")
    
    try:
        # Parse form data
        data = request.POST.dict()
        
        # Get a specific logger for this view but don't redefine the variable
        create_marker_logger = logging.getLogger('content.views.create_marker')
        create_marker_logger.info(f"Create marker request from user {request.user.username}")
        create_marker_logger.debug(f"Form data: {data}")
        print(f"[create_marker] Form data keys: {list(data.keys())}")

        # Convert checkbox form values to boolean
        boolean_fields = [
            'object_detection', 
            'camouflage_detection',  # This matches the model field name
            'damage_assessment', 
            'thermal_analysis',  # This matches the model field name
            'request_verification'
        ]
        
        for field in boolean_fields:
            # Form checkbox values come as 'on' or various truthy strings or not present
            if field in data:
                # Handle both checkbox 'on' values and JSON 'true'/'false' string values
                val = data[field]
                if isinstance(val, str):
                    data[field] = val.lower() in ('on', 'true', 'yes', '1')
                else:
                    data[field] = bool(val)
            else:
                data[field] = False
                
        create_marker_logger.debug(f"Processed boolean fields: {[(field, data.get(field)) for field in boolean_fields]}")
        print(f"[create_marker] Processed boolean fields: {[(field, data.get(field)) for field in boolean_fields]}")

        # Create marker instance with properly mapped fields
        print(f"[create_marker] Creating marker with title: {data.get('title', '')}")
        marker = Marker(
            user=request.user,
            title=data.get('title', ''),
            description=data.get('description', ''),
            latitude=float(data.get('latitude', 0)),
            longitude=float(data.get('longitude', 0)),
            date=datetime.strptime(data.get('date'), '%Y-%m-%d').date() if data.get('date') else timezone.now(),
            category=data.get('category', 'infrastructure'),
            source=data.get('source', ''),
            visibility=data.get('visibility', 'public'),
            
            # Map form fields directly to model fields - use correct field names
            object_detection=data.get('object_detection', False),
            camouflage_detection=data.get('camouflage_detection', False),
            damage_assessment=data.get('damage_assessment', False),
            thermal_analysis=data.get('thermal_analysis', False),
            request_verification=data.get('request_verification', False)
        )
        
        # Set verification status if requested
        if marker.request_verification:
            marker.verification = 'pending'
            print(f"[create_marker] Setting verification status to 'pending' as requested")
            
        marker.save()
        print(f"[create_marker] Created marker with ID: {marker.id}")
        create_marker_logger.info(f"Created marker {marker.id}")

        # Handle file uploads
        files = request.FILES.getlist('files')
        print(f"[create_marker] Processing {len(files)} files")
        create_marker_logger.info(f"Received {len(files)} files for marker {marker.id}")
        
        successful_files = 0
        for i, file in enumerate(files):
            try:
                # Handle each file with error checking
                print(f"[create_marker] Processing file {i+1}/{len(files)}: {file.name}, size: {file.size} bytes")
                MarkerFile.objects.create(marker=marker, file=file)
                successful_files += 1
                print(f"[create_marker] File {i+1} saved successfully")
            except Exception as e:
                print(f"[create_marker] Error saving file {file.name}: {str(e)}")
                create_marker_logger.error(f"Error saving file {file.name} for marker {marker.id}: {str(e)}")
                # Continue with other files even if one fails
                
        print(f"[create_marker] Successfully saved {successful_files} of {len(files)} files")
        create_marker_logger.info(f"Successfully saved {successful_files} of {len(files)} files for marker {marker.id}")

        return JsonResponse({
            'success': True,
            'message': 'Marker created successfully',
            'marker_id': marker.id
        })

    except Exception as e:
        print(f"[create_marker] Error creating marker: {str(e)}")
        logger.exception(f"Error creating marker: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error creating marker: {str(e)}'
        }, status=400)


def marker_detail(request, marker_id):
    """
    Render the marker detail page.
    
    Retrieves and displays detailed information about a marker,
    including comments, after verifying the user has permission to view it.
    
    Args:
        request: The HTTP request object
        marker_id: The ID of the marker to display
        
    Returns:
        HttpResponse: Rendered marker detail template with context
        
    Raises:
        Http404: If the marker does not exist
        PermissionDenied: If the user cannot view the marker
    """
    print(f"[marker_detail] Entering function with marker_id: {marker_id}")
    logger.info(f"User {request.user.username if request.user.is_authenticated else 'Anonymous'} is viewing marker {marker_id}")

    try:
        marker = get_object_or_404(Marker, id=marker_id)
    except Http404:
        logger.warning(f"Marker with ID {marker_id} not found.")
        raise Http404("Marker not found") # Let Django handle the 404 page

    print(f"[marker_detail] Retrieved marker: {marker.title} (ID: {marker.id})")

    # Check view permissions
    can_view = False
    if marker.visibility == 'public':
        can_view = True
    elif request.user.is_authenticated:
        if marker.visibility == 'private' and marker.user == request.user: # Only owner for private
            can_view = True
        elif marker.visibility == 'verified_only' and (request.user.is_staff or marker.user == request.user): # Only staff or owner
             can_view = True
        # Add check for verified users if you have a specific field/group for that
        # elif marker.visibility == 'verified_only' and request.user.profile.is_verified: # Example check
        #     can_view = True

    if not can_view:
        print(f"[marker_detail] Permission denied for marker {marker_id}, user: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
        logger.warning(f"Permission denied: User {request.user.username if request.user.is_authenticated else 'Anonymous'} attempted to view marker {marker_id} with visibility '{marker.visibility}'")
        return render(request, '403.html', status=403) # Render the 403 template

    # Get comments for the marker
    comments = Comment.objects.filter(marker=marker).select_related('user').order_by('-created_at')
    print(f"[marker_detail] Retrieved {comments.count()} comments")
        
    return render(request, 'marker-detail.html', {
        'marker': marker,
        'comments': comments,
        'can_edit': request.user.is_authenticated and marker.user == request.user # Only owner can edit
    })


@login_required
@require_http_methods(["DELETE"])
def delete_marker(request, marker_id):
    """
    Handle marker deletion.
    
    Deletes a marker and all associated files from both storage and database.
    
    Args:
        request: The HTTP request object
        marker_id: The ID of the marker to delete
        
    Returns:
        JsonResponse: Contains deletion status and result message
        
    Raises:
        Http404: If the marker does not exist
        PermissionDenied: If the user is not the owner of the marker
    """
    print(f"[delete_marker] Entering function with marker_id: {marker_id}")
    logger.info(f"User {request.user.username} is attempting to delete marker {marker_id}")
    
    marker = get_object_or_404(Marker, id=marker_id)
    print(f"[delete_marker] Retrieved marker: {marker.title} (ID: {marker.id})")
    
    # Check if user is the owner
    if marker.user != request.user:
        print(f"[delete_marker] Permission denied for user {request.user.username}")
        logger.warning(f"Permission denied: User {request.user.username} attempted to delete marker {marker_id}")
        return JsonResponse({
            'success': False,
            'message': 'Permission denied'
        }, status=403)
    
    try:    
        # Delete associated files from storage
        file_count = marker.files.count()
        print(f"[delete_marker] Deleting {file_count} associated files")
        
        for i, file_obj in enumerate(marker.files.all()):
            if default_storage.exists(file_obj.file.name):
                print(f"[delete_marker] Deleting file {i+1}/{file_count}: {file_obj.file.name}")
                default_storage.delete(file_obj.file.name)
            else:
                print(f"[delete_marker] File not found in storage: {file_obj.file.name}")
        
        # Delete marker
        print(f"[delete_marker] Deleting marker from database")
        marker.delete()
        
        print(f"[delete_marker] Marker {marker_id} deleted successfully")
        logger.info(f"User {request.user.username} successfully deleted marker {marker_id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Marker deleted successfully'
        })
    except Exception as e:
        print(f"[delete_marker] Error deleting marker: {str(e)}")
        logger.error(f"Error deleting marker {marker_id}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Error deleting marker: {str(e)}'
        }, status=500)
