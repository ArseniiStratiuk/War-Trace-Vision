import os
import json
import numpy as np
import cv2
from pathlib import Path
from typing import Dict, List, Tuple, Any, Union, Optional
import logging

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from ..models import Detection, ObjectDetection, ClassificationResult, SegmentationMask

logger = logging.getLogger(__name__)

# Define the paths
MODELS_ROOT = os.path.join(settings.BASE_DIR, 'detection', 'cv_models')
RESULTS_ROOT = os.path.join(settings.MEDIA_ROOT, 'detection_results')

# Ensure directories exist
os.makedirs(MODELS_ROOT, exist_ok=True)
os.makedirs(RESULTS_ROOT, exist_ok=True)

# Updated Model configuration dictionary with our specific models
MODEL_CONFIG = {
    'object_detection': {
        'yolo11m': {
            'model_path': os.path.join(MODELS_ROOT, 'yolo11m.pt'),
            'type': 'ultralytics',
            'threshold': 0.25,
            'description': 'General object recognition (people, vehicles, etc.)'
        }
    },
    'military_detection': {
        'yolo11m_military': {
            'model_path': os.path.join(MODELS_ROOT, 'yolo11m-military.pt'),
            'type': 'ultralytics',
            'threshold': 0.3,
            'description': 'Military objects detection (vehicles, weapons, soldiers, etc.)'
        }
    },
    'damage_assessment': {
        'xbd_classifier': {
            'model_path': os.path.join(MODELS_ROOT, 'xbd_damage_classifier.h5'),
            'type': 'keras',
            'labels': ['no_damage', 'minor_damage', 'major_damage', 'destroyed'],
            'description': 'Building damage assessment from satellite imagery'
        }
    },
    'emergency_recognition': {
        'emergency_net': {
            'model_path': os.path.join(MODELS_ROOT, 'emergency_net.h5'),
            'type': 'keras',
            'labels': ['normal', 'fire', 'flood', 'explosion', 'collapse', 'other_emergency'],
            'description': 'Emergency situation recognition'
        }
    }
}

class ModelService:
    """Service for handling ML model operations"""
    
    def __init__(self):
        self.loaded_models = {}
    
    def get_model(self, detector_type: str, model_name: str = None) -> Any:
        """Load and cache a model based on detector type and model name"""
        # Use first available model if model_name not specified
        if model_name is None:
            model_name = list(MODEL_CONFIG.get(detector_type, {}).keys())[0]
        
        model_key = f"{detector_type}_{model_name}"
        
        # Return cached model if already loaded
        if model_key in self.loaded_models:
            return self.loaded_models[model_key]
        
        # Get model config
        try:
            model_config = MODEL_CONFIG[detector_type][model_name]
        except KeyError:
            logger.error(f"Model not found: {detector_type}/{model_name}")
            return None
        
        # Load model based on type
        model_path = model_config['model_path']
        model_type = model_config['type']
        
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            return None
        
        # Load based on model type
        if model_type == 'ultralytics':
            from ultralytics import YOLO
            model = YOLO(model_path)
        elif model_type == 'keras':
            from keras.models import load_model
            model = load_model(model_path)
        else:
            logger.error(f"Unsupported model type: {model_type}")
            return None
        
        # Cache the loaded model
        self.loaded_models[model_key] = {
            'model': model,
            'config': model_config
        }
        
        return self.loaded_models[model_key]
    
    def process_image(self, file_path: str, detector_types: List[str]) -> Dict[str, Any]:
        """
        Process an image with multiple detector types
        
        Args:
            file_path: Path to the image file
            detector_types: List of detector types to use
            
        Returns:
            Dictionary of results per detector type
        """
        results = {}
        
        # Process each detector type
        for detector_type in detector_types:
            if detector_type not in MODEL_CONFIG:
                logger.warning(f"Unknown detector type: {detector_type}")
                continue
                
            # Get the first model for this detector type
            model_name = list(MODEL_CONFIG[detector_type].keys())[0]
            model_data = self.get_model(detector_type, model_name)
            
            if not model_data:
                continue
                
            model = model_data['model']
            config = model_data['config']
            
            # Process with the appropriate method based on detector type
            try:
                if detector_type in ['object_detection', 'military_detection']:
                    if config['type'] == 'ultralytics':
                        result = self._process_ultralytics_detection(model, file_path, config)
                    else:
                        logger.error(f"Unsupported model type for {detector_type}: {config['type']}")
                        continue
                elif detector_type in ['damage_assessment', 'emergency_recognition']:
                    if config['type'] == 'keras':
                        result = self._process_keras_classification(model, file_path, config)
                    else:
                        logger.error(f"Unsupported model type for {detector_type}: {config['type']}")
                        continue
                
                results[detector_type] = {
                    'model_name': model_name,
                    'result': result
                }
                
            except Exception as e:
                logger.exception(f"Error processing {detector_type} for {file_path}: {str(e)}")
        
        return results
    
    def _process_ultralytics_detection(self, model, file_path: str, config: Dict) -> Dict:
        """Process image with Ultralytics YOLOv8 model"""
        results = model(file_path, conf=config.get('threshold', 0.25))
        
        # Generate output image
        output_filename = f"det_{Path(file_path).stem}_{Path(file_path).stat().st_mtime:.0f}.jpg"
        output_path = os.path.join(RESULTS_ROOT, output_filename)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save plotted results
        result_plotted = results[0].plot()
        cv2.imwrite(output_path, result_plotted)
        
        # Define the correct URL format for accessing through Django
        # This needs to match the URL pattern we defined
        relative_path = f"/detection_results/{output_filename}"
        
        # Process results
        detections = []
        for r in results:
            if r.boxes is not None:
                for box in r.boxes:
                    bbox = box.xyxy[0].cpu().numpy()  # xyxy format: [x1, y1, x2, y2]
                    conf = float(box.conf[0].cpu().numpy())
                    cls_id = int(box.cls[0].cpu().numpy())
                    cls_name = r.names[cls_id]
                    
                    detections.append({
                        'label': cls_name,
                        'confidence': conf,
                        'bbox': [float(x) for x in bbox]  # Convert numpy values to Python floats
                    })
        
        return {
            'detections': detections,
            'output_path': output_path,
            'relative_path': relative_path,
            'summary': f"Found {len(detections)} objects"
        }
    
    def _process_keras_classification(self, model, file_path: str, config: Dict) -> Dict:
        """Process image with Keras classification model"""
        # Load and preprocess image
        img = cv2.imread(file_path)
        img = cv2.resize(img, (224, 224))  # Standard input size
        img = img / 255.0  # Normalize
        img = np.expand_dims(img, axis=0)
        
        # Get predictions
        predictions = model.predict(img)
        
        # Handle different prediction types
        if len(predictions.shape) == 2:  # Multi-class classification
            # Get class with highest probability
            class_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][class_idx])
            
            # Get class name from labels if available, otherwise use index
            if 'labels' in config:
                class_name = config['labels'][class_idx]
            else:
                class_name = f"class_{class_idx}"
                
            result = {
                'class': class_name,
                'confidence': confidence,
                'all_predictions': {
                    config['labels'][i] if 'labels' in config else f"class_{i}": float(pred)
                    for i, pred in enumerate(predictions[0])
                }
            }
        else:  # Binary classification
            confidence = float(predictions[0][0])
            result = {
                'confidence': confidence,
                'class': 'positive' if confidence > config.get('threshold', 0.5) else 'negative'
            }
            
        return result


# Singleton instance
model_service = ModelService()


def process_marker_file(marker_file, detector_types: List[str]) -> List[Detection]:
    """
    Process a marker file with the requested detector types
    
    Args:
        marker_file: MarkerFile instance
        detector_types: List of detector types to use
        
    Returns:
        List of created Detection objects
    """
    # Check if file exists and is an image
    if not marker_file.file:
        logger.error(f"File not found: {marker_file.id}")
        return []
    
    # Check if this file has already been processed with these detector types
    # Fix: Use the correct query pattern for related objects
    existing_detections = Detection.objects.filter(marker_file=marker_file, detector_type__in=detector_types)
    
    if existing_detections.exists():
        logger.info(f"File {marker_file.id} already processed. Skipping.")
        return list(existing_detections)
        
    file_path = marker_file.file.path
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Check if it's a processable image
    processable_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']
    if file_ext not in processable_extensions:
        logger.info(f"Skipping non-processable file: {file_path}")
        return []
    
    # Process with model service
    results = model_service.process_image(file_path, detector_types)
    
    # Create detection records
    detection_objects = []
    
    for detector_type, result_data in results.items():
        # Create base detection record
        detection = Detection(
            marker_file=marker_file,
            detector_type=detector_type,
            model_name=result_data['model_name']
        )
        
        result = result_data['result']
        
        # Handle different detector types
        if detector_type in ['object_detection', 'military_detection']:
            # Store overall summary
            detection.summary = result.get('summary', '')
            
            # Store the relative path for serving via URL
            detection.image_path = result.get('relative_path', '')
            detection.save()
            
            # Store individual detections
            for det in result.get('detections', []):
                ObjectDetection.objects.create(
                    detection=detection,
                    label=det['label'],
                    confidence=det['confidence'],
                    x_min=det['bbox'][0],
                    y_min=det['bbox'][1],
                    x_max=det['bbox'][2],
                    y_max=det['bbox'][3]
                )
                
        elif detector_type in ['damage_assessment', 'emergency_recognition']:
            # Store classification result
            detection.summary = f"Classified as {result['class']} with {result['confidence']:.2f} confidence"
            detection.save()
            
            ClassificationResult.objects.create(
                detection=detection,
                label=result['class'],
                confidence=result['confidence']
            )
            
            # Store all prediction confidences if available
            if 'all_predictions' in result:
                for label, conf in result['all_predictions'].items():
                    if label != result['class']:  # Main prediction already stored
                        ClassificationResult.objects.create(
                            detection=detection,
                            label=label,
                            confidence=conf
                        )
        
        detection_objects.append(detection)
    
    return detection_objects


def process_marker(marker) -> Dict[str, int]:
    """
    Process all files for a marker based on its detection settings
    
    Args:
        marker: Marker instance
        
    Returns:
        Summary of processed files and detections
    """
    detector_types = []
    
    # Check which detector types are enabled
    if marker.object_detection:
        detector_types.append('object_detection')
    if marker.military_detection:
        detector_types.append('military_detection')
    if marker.damage_assessment:
        detector_types.append('damage_assessment')
    if marker.emergency_recognition:
        detector_types.append('emergency_recognition')
    
    if not detector_types:
        return {'processed': 0, 'detections': 0}
    
    # Process all files
    processed_count = 0
    detection_count = 0
    already_processed_count = 0
    
    # Fix: Access files through proper relation syntax
    for marker_file in marker.files.all():
        # Skip files that have already been processed with the same detector types
        # Fix: Use proper query to get existing detections
        existing_detections = Detection.objects.filter(marker_file=marker_file).values_list('detector_type', flat=True)
        existing_detection_types = set(existing_detections)
        
        # Check which detector types need processing
        remaining_detector_types = [dt for dt in detector_types if dt not in existing_detection_types]
        
        if not remaining_detector_types:
            already_processed_count += 1
            continue
            
        detections = process_marker_file(marker_file, remaining_detector_types)
        if detections:
            processed_count += 1
            detection_count += len(detections)
    
    return {
        'processed': processed_count,
        'detections': detection_count,
        'already_processed': already_processed_count
    }
