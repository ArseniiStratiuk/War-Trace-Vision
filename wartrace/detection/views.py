import json
import os
import traceback
import logging
import threading
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.urls import reverse
from django.db import models, transaction
from django.conf import settings
from django.contrib import messages
from concurrent.futures import ThreadPoolExecutor

from content.models import Marker, MarkerFile
from .models import Detection, ObjectDetection, ClassificationResult, DetectionConfig
from .services.main import process_marker, process_marker_file, model_service, MODEL_CONFIG, ensure_detection_directories

# Set up logging
logger = logging.getLogger(__name__)

# Global worker pool for processing
worker_pool = ThreadPoolExecutor(max_workers=2)
# Track processing status
processing_markers = {}

def can_edit_marker(user, marker):
    """Check if user can edit the marker"""
    return user.is_staff or marker.user == user

def can_view_marker(user, marker):
    """Check if user can view the marker (more permissive)"""
    # If public marker, anyone can view
    if marker.visibility == 'public':
        return True
    
    # If private marker, only owner or staff can view
    if marker.visibility == 'private':
        return user.is_staff or marker.user == user
    
    # If verified_only marker, verified users, owner or staff can view
    if marker.visibility == 'verified_only':
        # This assumes some verified status for users - adjust as needed
        return (user.is_authenticated and marker.verification == 'verified') or user.is_staff or marker.user == user
    
    return False

@login_required
def process_marker_view(request, marker_id):
    """
    Process a marker with AI detection
    """
    marker = get_object_or_404(Marker, id=marker_id)
    
    # Check if user has permission to process this marker
    if marker.user != request.user and not request.user.is_staff:
        return render(request, '403.html', status=403)
    
    # Check if marker has files
    file_count = marker.files.count()
    if file_count == 0:
        messages.warning(request, "This marker has no uploaded files to process.")
        return redirect('detection:marker_results', marker_id=marker.id)
    
    # Get current detector types enabled for this marker
    detector_types = []
    if marker.object_detection:
        detector_types.append('object_detection')
    if marker.camouflage_detection:
        detector_types.append('military_detection')
    if marker.damage_assessment:
        detector_types.append('damage_assessment')
    if marker.thermal_analysis:
        detector_types.append('emergency_recognition')
    
    # Clear previous detections if reprocessing
    # Fix: access marker_file.detections.all() first to get a related manager
    detection_count = 0
    for marker_file in marker.files.all():
        detections = marker_file.detections.all()  # Get the related manager
        detection_count += detections.filter(detector_type__in=detector_types).count()
    
    if detection_count > 0:
        if request.method == 'POST' and request.POST.get('confirm_reprocess') == 'yes':
            # User confirmed reprocessing, delete old detections
            logger.info(f"Reprocessing marker {marker_id} - deleting {detection_count} existing detections")
            
            for marker_file in marker.files.all():
                file_detections = marker_file.detections.filter(detector_type__in=detector_types)
                
                # Clean up both DB-stored and legacy filesystem images before deleting records
                for detection in file_detections:
                    # Clean up DB-stored images
                    if detection.processed_image:
                        try:
                            detection.processed_image.delete(save=False)
                            logger.info(f"Deleted DB-stored image for detection {detection.id}")
                        except Exception as e:
                            logger.error(f"Error deleting DB-stored image: {str(e)}")
                    
                    # Clean up legacy filesystem images
                    if detection.image_path:
                        try:
                            legacy_path = detection.image_path
                            if legacy_path.startswith('/'):
                                legacy_path = legacy_path[1:]
                            
                            if default_storage.exists(legacy_path):
                                default_storage.delete(legacy_path)
                                logger.info(f"Deleted legacy filesystem image: {legacy_path}")
                        except Exception as e:
                            logger.error(f"Error deleting legacy filesystem image: {str(e)}")
                
                # Now delete the detection records
                file_detections.delete()
        else:
            # Ask for confirmation before reprocessing
            return render(request, 'detection/confirm_reprocess.html', {
                'marker': marker,
                'detection_count': detection_count,
                'detector_types': detector_types
            })
    
    # Process the marker
    try:
        # Use the processing service
        from .services.main import process_marker
        result = process_marker(marker)
        
        # Show success message
        messages.success(request, f"Processing complete: {result['processed']} files processed with {result['detections']} detections.")
        
    except Exception as e:
        logger.exception(f"Error processing marker {marker_id}: {str(e)}")
        messages.error(request, f"Error during processing: {str(e)}")
    
    # Redirect to the results page
    return redirect('detection:marker_results', marker_id=marker.id)

@login_required
@require_http_methods(["POST"])
def process_marker_api(request, marker_id):
    """API endpoint to start marker processing"""
    marker = get_object_or_404(Marker, id=marker_id)
    
    # Check permissions
    if not request.user.is_staff and marker.user != request.user:
        return JsonResponse({
            'success': False,
            'message': 'Permission denied'
        }, status=403)
    
    # Check if already processing
    if marker_id in processing_markers and processing_markers[marker_id]['status'] == 'processing':
        return JsonResponse({
            'success': False,
            'message': 'Processing already in progress'
        })
    
    try:
        # Parse enabled detector types from form
        detector_types = []
        
        # Map UI model types to backend model types
        model_map = {
            'object_detection': 'object_detection',
            'military_detection': 'camouflage_detection',
            'damage_assessment': 'damage_assessment',
            'emergency_recognition': 'thermal_analysis'
        }
        
        # Update marker with selected detection options
        for ui_type, model_field in model_map.items():
            # Check if this type was selected in the form
            enabled = request.POST.get(ui_type) == 'on'
            setattr(marker, model_field, enabled)
            
            if enabled:
                detector_types.append(ui_type)
        
        # Save updated marker
        marker.save()
        
        # Start processing in background
        processing_markers[marker_id] = {
            'status': 'processing',
            'progress': 0,
            'detector_types': detector_types
        }
        
        # Start background processing task
        worker_pool.submit(
            process_marker_background,
            marker, 
            detector_types
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Processing started',
            'detector_types': detector_types
        })
    
    except Exception as e:
        logger.error(f"Error starting processing: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'Error starting processing: {str(e)}'
        }, status=500)

@login_required
def marker_processing_status(request, marker_id):
    """Get the current processing status for a marker"""
    marker = get_object_or_404(Marker, id=marker_id)
    
    # Check permissions
    if not request.user.is_staff and marker.user != request.user:
        return JsonResponse({
            'success': False,
            'message': 'Permission denied'
        }, status=403)
    
    # Get current status
    if marker_id in processing_markers:
        status_data = processing_markers[marker_id]
        return JsonResponse({
            'status': status_data['status'],
            'progress': status_data.get('progress', 0),
            'result': status_data.get('result')
        })
    else:
        return JsonResponse({
            'status': 'idle'
        })

@login_required
@require_http_methods(["POST"])
def auto_process_marker(request, marker_id):
    """Automatically start processing for a marker based on its detection settings"""
    marker = get_object_or_404(Marker, id=marker_id)
    
    # Check permissions
    if not request.user.is_staff and marker.user != request.user:
        return JsonResponse({
            'success': False,
            'message': 'Permission denied'
        }, status=403)
    
    try:
        # Check if already processing
        if marker_id in processing_markers and processing_markers[marker_id]['status'] == 'processing':
            return JsonResponse({
                'success': False,
                'message': 'Processing already in progress'
            })
        
        # Map model types to detector types
        model_map = {
            'object_detection': marker.object_detection,
            'military_detection': marker.camouflage_detection,
            'damage_assessment': marker.damage_assessment,
            'emergency_recognition': marker.thermal_analysis
        }
        
        # Get enabled detector types
        detector_types = [dt for dt, enabled in model_map.items() if enabled]
        
        if not detector_types:
            return JsonResponse({
                'success': False,
                'message': 'No detection types enabled'
            })
        
        # Start processing in background
        processing_markers[marker_id] = {
            'status': 'processing',
            'progress': 0,
            'detector_types': detector_types
        }
        
        # Start background processing task
        worker_pool.submit(
            process_marker_background,
            marker, 
            detector_types
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Processing started',
            'detector_types': detector_types
        })
    
    except Exception as e:
        logger.error(f"Error starting auto processing: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'Error starting processing: {str(e)}'
        }, status=500)

def process_marker_background(marker, detector_types):
    """Process a marker in background thread"""
    marker_id = marker.id
    
    try:
        logger.info(f"Starting background processing for marker {marker_id}")
        
        # Process marker with selected detector types
        result = process_marker(marker)
        
        # Update status to completed
        processing_markers[marker_id] = {
            'status': 'completed',
            'progress': 100,
            'detector_types': detector_types,
            'result': {
                'success': True,
                'message': 'Processing completed successfully',
                'processed': result.get('processed', 0),
                'detections': result.get('detections', 0),
                'result_images': result.get('detections', 0),
                'processing_time': result.get('processing_time')
            }
        }
        logger.info(f"Completed background processing for marker {marker_id}: {result}")
    
    except Exception as e:
        logger.error(f"Error in background processing for marker {marker_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Update status to error
        processing_markers[marker_id] = {
            'status': 'error',
            'progress': 0,
            'detector_types': detector_types,
            'result': {
                'success': False,
                'message': f'Error during processing: {str(e)}'
            }
        }

@login_required
def marker_detection_results(request, marker_id):
    """
    Display all detection results for a marker
    """
    marker = get_object_or_404(Marker, id=marker_id)

    # Check if user has permission to view this marker
    if marker.visibility == 'private' and (not request.user.is_authenticated or marker.user != request.user):
        return render(request, '403.html', status=403)
    
    # Get all files for this marker
    marker_files = marker.files.all()
    
    # Collect all detections for all files of this marker
    all_detections = []
    detector_types = []
    
    for marker_file in marker_files:
        # The correct way to query related Detection objects
        detections = marker_file.detections.all()
        
        all_detections.extend(detections)
        for det in detections:
            if det.detector_type not in detector_types:
                detector_types.append(det.detector_type)
    
    # Group detections by detector type
    grouped_detections = {}
    for det_type in detector_types:
        grouped_detections[det_type] = [d for d in all_detections if d.detector_type == det_type]
    
    # Prepare data for the template
    files_with_detections = []
    total_objects = 0
    
    for marker_file in marker_files:
        file_detections = marker_file.detections.all()
        
        if file_detections.exists():
            # Count objects in all detections for this file
            file_objects_count = sum(d.objects.count() for d in file_detections)
            total_objects += file_objects_count
            
            # Enhance detection objects with additional data
            enhanced_detections = []
            for detection in file_detections:
                # Get display name for detector type
                detector_display_name = {
                    'object_detection': 'Розпізнавання об\'єктів',
                    'military_detection': 'Військова техніка',
                    'damage_assessment': 'Оцінка пошкоджень',
                    'emergency_recognition': 'Аналіз надзвичайних ситуацій'
                }.get(detection.detector_type, detection.detector_type)
                
                # Get inference time from metadata
                inference_time = None
                if detection.metadata and 'inference_time' in detection.metadata:
                    inference_time = detection.metadata['inference_time']
                
                # Calculate object classes
                object_classes = {}
                for obj in detection.objects.all():
                    label = obj.label
                    object_classes[label] = object_classes.get(label, 0) + 1
                
                enhanced_detections.append({
                    'id': detection.id,
                    'detector_type': detection.detector_type,
                    'detector_display_name': detector_display_name,
                    'model_name': detection.model_name,
                    'summary': detection.summary,
                    'image_url': detection.image_url,  # Uses the property that handles both storage methods
                    'object_count': detection.objects.count(),
                    'object_classes': object_classes,
                    'inference_time': inference_time,
                    'objects': detection.objects.all()
                })
            
            files_with_detections.append({
                'file': marker_file,
                'detections': enhanced_detections,
                'detection_count': len(enhanced_detections)
            })
    
    # Prepare detector types info for the template
    detector_types_info = {
        'object_detection': {
            'name': 'Розпізнавання об\'єктів',
            'description': 'Виявлення загальних об\'єктів на зображенні (люди, транспорт, будівлі та ін.)',
            'enabled': marker.object_detection
        },
        'military_detection': {
            'name': 'Військова техніка',
            'description': 'Виявлення військової техніки та об\'єктів (танки, БТР, солдати та ін.)',
            'enabled': marker.camouflage_detection
        },
        'damage_assessment': {
            'name': 'Оцінка пошкоджень',
            'description': 'Аналіз рівня пошкоджень будівель та інфраструктури',
            'enabled': marker.damage_assessment
        },
        'emergency_recognition': {
            'name': 'Надзвичайні ситуації',
            'description': 'Виявлення пожеж, затоплень та інших надзвичайних ситуацій',
            'enabled': marker.thermal_analysis
        }
    }
    
    return render(request, 'detection/marker_results.html', {
        'marker': marker,
        'files_with_detections': files_with_detections,
        'total_detections': len(all_detections),
        'total_objects': total_objects,
        'file_count': marker_files.count(),
        'detector_types': detector_types_info,
        'can_edit': request.user.is_authenticated and (marker.user == request.user or request.user.is_staff)
    })

@login_required
def detection_detail(request, detection_id):
    """View detailed information about a specific detection"""
    detection = get_object_or_404(Detection, id=detection_id)
    marker = detection.marker_file.marker
    
    # Check if user has permission to view this marker
    if marker.visibility == 'private' and (not request.user.is_authenticated or marker.user != request.user):
        return render(request, '403.html', status=403)
    
    # Get objects for this detection
    objects = detection.objects.all().order_by('-confidence')
    
    # Get display name from config or use detector type
    detector_type = detection.detector_type
    display_name = detector_type.replace('_', ' ').title()
    model_description = ""
    
    try:
        config = DetectionConfig.objects.get(detector_type=detector_type)
        display_name = config.display_name
        
        # Get model description from model configuration
        model_info = model_service.get_model(detector_type, detection.model_name)
        if model_info and 'config' in model_info:
            model_description = model_info['config'].get('description', '')
    except DetectionConfig.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
    
    # Calculate object class counts
    object_classes = {}
    for obj in objects:
        object_classes[obj.label] = object_classes.get(obj.label, 0) + 1
    
    context = {
        'detection': detection,
        'marker': marker,
        'objects': objects,
        'total_objects': objects.count(),
        'object_classes': object_classes,
        'detector_display_name': display_name,
        'model_description': model_description,
        'image_url': detection.image_url  # Uses the property that handles both storage methods
    }
    
    return render(request, 'detection/detection_detail.html', context)

@login_required
def available_models(request):
    """API endpoint to get available detection models"""
    detector_configs = DetectionConfig.objects.filter(is_enabled=True).order_by('order')
    
    models = []
    for config in detector_configs:
        models.append({
            'type': config.detector_type,
            'display_name': config.display_name,
            'description': config.description,
            'icon': config.icon,
            'order': config.order
        })
    
    return JsonResponse({
        'success': True,
        'models': models
    })

@login_required
def process_file_view(request, file_id):
    """View for processing a single marker file"""
    marker_file = get_object_or_404(MarkerFile, id=file_id)
    marker = marker_file.marker
    
    # Check if user has permission
    if not request.user.is_staff and marker.user != request.user:
        return render(request, '403.html', status=403)
    
    # Get detector types
    detector_configs = DetectionConfig.objects.filter(is_enabled=True).order_by('order')
    
    # Redirect to marker processing view for simplicity
    return redirect('detection:process_marker', marker_id=marker.id)

@login_required
def file_detection_results(request, file_id):
    """View detection results for a specific file"""
    marker_file = get_object_or_404(MarkerFile, id=file_id)
    marker = marker_file.marker
    
    # Check permissions
    if marker.visibility == 'private' and (not request.user.is_authenticated or marker.user != request.user):
        return render(request, '403.html', status=403)
    
    # Redirect to marker results for simplicity
    return redirect('detection:marker_results', marker_id=marker.id)
