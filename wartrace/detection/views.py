import json
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import models
from django.conf import settings

from content.models import Marker, MarkerFile
from .models import Detection, ObjectDetection, ClassificationResult
from .services.main import process_marker, process_marker_file, model_service, MODEL_CONFIG


@login_required
def review_view(request):
    """View for reviewing AI detection results"""
    # Get markers with AI detection enabled
    ai_markers = Marker.objects.filter(
        user=request.user
    ).filter(
        models.Q(object_detection=True) | 
        models.Q(military_detection=True) | 
        models.Q(damage_assessment=True) | 
        models.Q(emergency_recognition=True)
    )
    
    # Get available detector types and their descriptions
    detector_types = {}
    for detector_type, detector_models in MODEL_CONFIG.items():
        first_model = next(iter(detector_models.values()))
        detector_types[detector_type] = first_model['description']
    
    return render(request, 'detection/review.html', {
        'markers': ai_markers,
        'detector_types': detector_types
    })


@login_required
@require_http_methods(["POST"])
def process_marker_api(request, marker_id):
    """API endpoint to process a marker's files with AI"""
    marker = get_object_or_404(Marker, id=marker_id)
    
    # Security check - only owner or staff can process
    if marker.user != request.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        # Determine which detector types to use based on marker settings
        detector_types = []
        if marker.object_detection:
            detector_types.append('object_detection')
        if marker.military_detection:
            detector_types.append('military_detection')
        if marker.damage_assessment:
            detector_types.append('damage_assessment')
        if marker.emergency_recognition:
            detector_types.append('emergency_recognition')
        
        if not detector_types:
            return JsonResponse({
                'success': False,
                'message': 'No AI detection options enabled for this marker'
            }, status=400)
        
        # Process the marker
        results = process_marker(marker)
        
        # Save processed images as new marker files
        processed_files = 0
        for marker_file in marker.files.all():
            # Get all detections for this file that have images
            detections = Detection.objects.filter(
                marker_file=marker_file, 
                detector_type__in=['object_detection', 'military_detection']
            ).exclude(image_path='')
            
            for detection in detections:
                # Handle the image path
                image_path = detection.image_path
                if image_path.startswith('/'):
                    image_path = image_path[1:]  # Remove leading slash
                
                full_path = os.path.join(settings.MEDIA_ROOT, image_path)
                if os.path.exists(full_path):
                    # Check if this processed image already exists
                    file_name = f"{detection.detector_type}_{detection.id}.jpg"
                    if not MarkerFile.objects.filter(marker=marker, file__contains=file_name).exists():
                        # Create a new marker file with the processed image
                        with open(full_path, 'rb') as f:
                            MarkerFile.objects.create(
                                marker=marker,
                                file=ContentFile(f.read(), name=file_name)
                            )
                            processed_files += 1
        
        return JsonResponse({
            'success': True,
            'message': f"Processed {results['processed']} files with {results['detections']} detections. Created {processed_files} result images.",
            'results': results
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f"Error processing marker: {str(e)}"
        }, status=500)


@login_required
@require_http_methods(["GET"])
def marker_detection_results(request, marker_id):
    """View detection results for a specific marker"""
    marker = get_object_or_404(Marker, id=marker_id)
    
    # Security check - only owner or staff can view
    if marker.user != request.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    # Get all detections for this marker's files
    files_with_detections = []
    
    for marker_file in marker.files.all():
        # Get detections for this file
        detections = Detection.objects.filter(marker_file=marker_file)
        if detections.exists():
            detection_data = []
            
            for detection in detections:
                # Get objects for this detection
                objects = list(ObjectDetection.objects.filter(detection=detection).values(
                    'label', 'confidence', 'x_min', 'y_min', 'x_max', 'y_max'
                ))
                
                # Get classifications for this detection
                classifications = list(ClassificationResult.objects.filter(detection=detection).values(
                    'label', 'confidence'
                ))
                
                # Get model description
                model_description = ""
                if detection.detector_type in MODEL_CONFIG:
                    if detection.model_name in MODEL_CONFIG[detection.detector_type]:
                        model_description = MODEL_CONFIG[detection.detector_type][detection.model_name].get('description', '')
                
                detection_data.append({
                    'id': detection.id,
                    'detector_type': detection.detector_type,
                    'model_name': detection.model_name,
                    'model_description': model_description,
                    'summary': detection.summary,
                    'image_path': detection.image_path,
                    'objects': objects,
                    'classifications': classifications
                })
            
            files_with_detections.append({
                'file': marker_file,
                'detections': detection_data
            })
    
    # Get all detector types
    detector_types = {}
    for detector_type, detector_models in MODEL_CONFIG.items():
        first_model = next(iter(detector_models.values()))
        detector_types[detector_type] = {
            'name': detector_type.replace('_', ' ').title(),
            'description': first_model.get('description', '')
        }
    
    return render(request, 'detection/marker_results.html', {
        'marker': marker,
        'files_with_detections': files_with_detections,
        'detector_types': detector_types
    })


@login_required
@require_http_methods(["POST"])
def process_single_file(request, file_id):
    """Process a single file with AI detection"""
    marker_file = get_object_or_404(MarkerFile, id=file_id)
    marker = marker_file.marker
    
    # Security check - only owner or staff can process
    if marker.user != request.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    # Determine which detector types to use based on marker settings
    detector_types = []
    if marker.object_detection:
        detector_types.append('object_detection')
    if marker.military_detection:
        detector_types.append('military_detection')
    if marker.damage_assessment:
        detector_types.append('damage_assessment')
    if marker.emergency_recognition:
        detector_types.append('emergency_recognition')
    
    if not detector_types:
        return JsonResponse({
            'success': False,
            'message': 'No AI detection options enabled for this marker'
        }, status=400)
    
    # Check if the file has already been processed with all enabled detector types
    existing_detection_types = set(Detection.objects.filter(marker_file=marker_file).values_list('detector_type', flat=True))
    remaining_detector_types = [dt for dt in detector_types if dt not in existing_detection_types]
    
    if not remaining_detector_types:
        return JsonResponse({
            'success': True,
            'message': 'File has already been processed with all enabled detector types',
            'alreadyProcessed': True,
            'detection_count': Detection.objects.filter(marker_file=marker_file).count()
        })
    
    try:
        # Process the file only with the remaining detector types
        detections = process_marker_file(marker_file, remaining_detector_types)
        
        # Save any generated images as new marker files
        for detection in detections:
            if detection.detector_type in ['object_detection', 'military_detection'] and detection.image_path:
                # Process the image path
                image_path = detection.image_path
                if image_path.startswith('/'):
                    image_path = image_path[1:]  # Remove leading slash
                
                full_path = os.path.join(settings.MEDIA_ROOT, image_path)
                if os.path.exists(full_path):
                    # Create a new marker file with the processed image
                    file_name = f"{detection.detector_type}_{detection.id}.jpg"
                    if not MarkerFile.objects.filter(marker=marker, file__contains=file_name).exists():
                        with open(full_path, 'rb') as f:
                            MarkerFile.objects.create(
                                marker=marker,
                                file=ContentFile(f.read(), name=file_name)
                            )
        
        return JsonResponse({
            'success': True,
            'message': f"Processed file with {len(detections)} detection results",
            'detection_count': len(detections)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f"Error processing file: {str(e)}"
        }, status=500)
