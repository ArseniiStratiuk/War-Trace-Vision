import os
import json
import numpy as np
import cv2
from pathlib import Path
from typing import Dict, List, Tuple, Any, Union, Optional
import logging
import traceback
import random
import time

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from ..models import Detection, ObjectDetection, ClassificationResult

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
            'threshold': 0.30,  # Increased confidence threshold
            'iou': 0.45,  # Added IoU threshold for NMS
            'description': 'General object recognition (COCO dataset - 80 classes)'
        }
    },
    'military_detection': {
        'yolo11s_military': {
            'model_path': os.path.join(MODELS_ROOT, 'yolo11s-military.pt'),
            'type': 'ultralytics',
            'threshold': 0.35,  # Higher confidence for more precise military detections
            'iou': 0.40,  # IoU threshold for NMS
            'description': 'Military objects detection (specialized model)',
            'classes': [
                'camouflage_soldier', 'weapon', 'military_tank', 'military_truck', 
                'military_vehicle', 'civilian', 'soldier', 'civilian_vehicle',
                'military_artillery', 'trench', 'military_aircraft', 'military_warship'
            ]
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

# Ensure detection results directories exist
def ensure_detection_directories():
    """Make sure all required directories for detection results exist"""
    # Main results directory
    os.makedirs(RESULTS_ROOT, exist_ok=True)
    
    # Create subdirectories for each detection type
    for detector_type in MODEL_CONFIG.keys():
        detector_dir = os.path.join(RESULTS_ROOT, detector_type)
        os.makedirs(detector_dir, exist_ok=True)
    
    # Directory for classifications
    classifications_dir = os.path.join(RESULTS_ROOT, 'classifications')
    os.makedirs(classifications_dir, exist_ok=True)

# Call this function to ensure directories exist when the module is loaded
ensure_detection_directories()

# Modern color palette for object visualization (RGBA for overlay transparency handling)
COLOR_PALETTE = {
    # Military object colors - using more modern, distinct colors with reduced transparency
    'camouflage_soldier': (52, 96, 73, 0.5),     # Camo green
    'weapon': (145, 30, 30, 0.6),                # Dark red
    'military_tank': (94, 23, 35, 0.6),          # Burgundy
    'military_truck': (155, 62, 21, 0.6),        # Rust
    'military_vehicle': (201, 70, 24, 0.6),      # Orange-red
    'civilian': (20, 158, 140, 0.5),             # Teal
    'soldier': (38, 82, 153, 0.5),               # Blue
    'civilian_vehicle': (76, 175, 80, 0.5),      # Green
    'military_artillery': (110, 28, 36, 0.6),    # Brown-red
    'trench': (94, 78, 23, 0.5),                 # Brown
    'military_aircraft': (48, 63, 159, 0.5),     # Royal blue
    'military_warship': (26, 35, 126, 0.5),      # Navy blue
    
    # Common COCO object colors with reduced transparency
    'person': (63, 81, 181, 0.5),                # Indigo
    'bicycle': (33, 150, 243, 0.5),              # Blue
    'car': (0, 188, 212, 0.5),                   # Cyan
    'motorcycle': (0, 150, 136, 0.5),            # Teal
    'airplane': (76, 175, 80, 0.5),              # Green
    'bus': (139, 195, 74, 0.5),                  # Light green
    'train': (205, 220, 57, 0.5),                # Lime
    'truck': (255, 235, 59, 0.5),                # Yellow
    'boat': (255, 193, 7, 0.5),                  # Amber
    'traffic light': (255, 152, 0, 0.5),         # Orange
    'fire hydrant': (255, 87, 34, 0.5),          # Deep orange
    'stop sign': (244, 67, 54, 0.5),             # Red
    'bench': (156, 39, 176, 0.5),                # Purple
    
    # Default for other classes
    'default': (158, 158, 158, 0.5)              # Gray
}

class ModelService:
    """Service for handling ML model operations"""
    
    def __init__(self):
        self.loaded_models = {}
        logger.info("Model service initialized")
    
    def get_model(self, detector_type: str, model_name: str = None) -> Any:
        """Load and cache a model based on detector type and model name"""
        # Use first available model if model_name not specified
        if model_name is None:
            model_name = list(MODEL_CONFIG.get(detector_type, {}).keys())[0]
        
        model_key = f"{detector_type}_{model_name}"
        logger.info(f"Requesting model: {model_key}")
        
        # Return cached model if already loaded
        if (model_key in self.loaded_models):
            logger.info(f"Using cached model: {model_key}")
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
        
        try:
            if model_type == 'ultralytics':
                try:
                    from ultralytics import YOLO
                    start_time = time.time()
                    
                    if os.path.exists(model_path):
                        logger.info(f"Loading YOLO model from {model_path}")
                        model = YOLO(model_path)
                        logger.info(f"Loaded YOLO model from {model_path} in {time.time() - start_time:.2f}s")
                    else:
                        # If model file doesn't exist, attempt to download it
                        logger.warning(f"Model file not found at {model_path}, attempting to download")
                        model = YOLO(model_name)  # This will try to download from ultralytics
                except ImportError:
                    logger.error("Ultralytics package not installed, please install with: pip install ultralytics")
                    return None
                except Exception as e:
                    logger.error(f"Error loading YOLO model: {str(e)}")
                    logger.error(traceback.format_exc())
                    return None
            elif model_type == 'keras':
                try:
                    import tensorflow as tf
                    if os.path.exists(model_path):
                        model = tf.keras.models.load_model(model_path)
                        logger.info(f"Loaded Keras model from {model_path}")
                    else:
                        logger.error(f"Keras model file not found: {model_path}")
                        return None
                except ImportError:
                    logger.error("TensorFlow not installed, please install with: pip install tensorflow")
                    return None
                except Exception as e:
                    logger.error(f"Error loading Keras model: {str(e)}")
                    logger.error(traceback.format_exc())
                    return None
            else:
                logger.error(f"Unsupported model type: {model_type}")
                return None
                
            # Cache the loaded model
            self.loaded_models[model_key] = {
                'model': model,
                'config': model_config
            }
            
            return self.loaded_models[model_key]
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def process_image(self, file_path: str, detector_types: List[str]) -> Dict[str, Any]:
        """
        Process an image with multiple detector types
        
        Args:
            file_path: Path to the image file
            detector_types: List of detector types to use
            
        Returns:
            Dictionary of results per detector type
        """
        logger.info(f"Processing image {file_path} with detector types: {detector_types}")
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
                logger.warning(f"No model loaded for {detector_type}, skipping")
                continue
                
            model = model_data['model']
            config = model_data['config']
            
            # Process with the appropriate method based on detector type
            try:
                if detector_type in ['object_detection', 'military_detection']:
                    if config['type'] == 'ultralytics':
                        # Process with YOLO model
                        result = self._process_with_yolo(file_path, detector_type, model, config)
                    else:
                        logger.warning(f"Unsupported model type for {detector_type}: {config['type']}")
                        continue
                elif detector_type in ['damage_assessment', 'emergency_recognition']:
                    if config['type'] == 'keras':
                        # Process with Keras model
                        result = self._process_with_keras(file_path, detector_type, model, config)
                    else:
                        logger.warning(f"Unsupported model type for {detector_type}: {config['type']}")
                        continue
                
                results[detector_type] = {
                    'model_name': model_name,
                    'result': result
                }
                
            except Exception as e:
                logger.error(f"Error processing {detector_type} for {file_path}: {str(e)}")
                logger.error(traceback.format_exc())
        
        return results
    
    def _process_with_yolo(self, file_path: str, detector_type: str, model, config: Dict) -> Dict:
        """Process an image with a YOLO model"""
        # Generate output filename and path
        file_stem = Path(file_path).stem
        output_filename = f"{file_stem}_{detector_type}.jpg"
        
        # Store in detector-specific subfolder
        output_dir = os.path.join(RESULTS_ROOT, detector_type)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)
        
        try:
            # Run inference with the model
            threshold = config.get('threshold', 0.30)
            iou = config.get('iou', 0.45)
            logger.info(f"Running inference with {detector_type} model (conf={threshold}, iou={iou})")
            
            start_time = time.time()
            results = model(file_path, conf=threshold, iou=iou)
            inference_time = time.time() - start_time
            logger.info(f"Inference completed in {inference_time:.2f}s")
            
            # Read original image for annotation
            original_img = cv2.imread(file_path)
            if original_img is None:
                logger.error(f"Failed to read image: {file_path}")
                raise ValueError(f"Could not read image file: {file_path}")
            
            # Extract detection results
            detections = []
            result = results[0]  # First image result
            
            # Convert YOLO results to our format
            for box in result.boxes:
                label_idx = int(box.cls)
                
                # Use the YOLO model's class names or config's class list
                if hasattr(result, 'names') and label_idx in result.names:
                    label = result.names[label_idx]
                elif 'classes' in config and label_idx < len(config['classes']):
                    label = config['classes'][label_idx]
                else:
                    label = f"class_{label_idx}"
                    
                conf = float(box.conf)
                
                # Get coordinates (convert to pixels)
                x1, y1, x2, y2 = box.xyxy[0].tolist()  # xyxy format (top-left, bottom-right)
                
                detections.append({
                    'label': label,
                    'confidence': conf,
                    'bbox': [x1, y1, x2, y2]
                })
            
            logger.info(f"Found {len(detections)} objects in image")
            
            # Draw annotations on the image
            annotated_img = self._draw_modern_annotations(original_img.copy(), detections, detector_type)
            
            # Save the annotated image
            cv2.imwrite(output_path, annotated_img)
            logger.info(f"Saved annotated image to {output_path}")
            
            # Define the URL path for accessing the result
            relative_path = f"detection_results/{detector_type}/{output_filename}"
            
            # Create summary text
            label_counts = {}
            for det in detections:
                label = det['label']
                label_counts[label] = label_counts.get(label, 0) + 1
            
            summary_parts = []
            for label, count in label_counts.items():
                summary_parts.append(f"{count} {label}{'s' if count > 1 else ''}")
            
            summary = f"Found {len(detections)} objects: " + ", ".join(summary_parts) if detections else "No objects detected"
            
            return {
                'detections': detections,
                'output_path': output_path,
                'relative_path': relative_path,
                'summary': summary,
                'inference_time': inference_time
            }
            
        except Exception as e:
            logger.error(f"Error in YOLO processing: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Create error image
            error_img = np.zeros((400, 600, 3), dtype=np.uint8)
            cv2.putText(
                error_img, 
                f"Error processing image with {detector_type}", 
                (20, 150), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                (255, 255, 255), 
                1
            )
            cv2.putText(
                error_img, 
                str(e), 
                (20, 200), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                (200, 100, 100), 
                1
            )
            
            # Save error image
            cv2.imwrite(output_path, error_img)
            
            relative_path = f"detection_results/{detector_type}/{output_filename}"
            
            return {
                'detections': [],
                'output_path': output_path,
                'relative_path': relative_path,
                'summary': f"Error processing image: {str(e)}"
            }
    
    def _draw_modern_annotations(self, img, detections, detector_type):
        """Draw modern, minimalistic annotations with segmentation-style labels"""
        h, w = img.shape[:2]
        
        # Create a clean copy of the image for overlays
        result_img = img.copy()
        
        # Apply slight brightness enhancement to original image (1.1 = 10% brighter)
        result_img = cv2.convertScaleAbs(result_img, alpha=1.1, beta=5)
        
        # Configure header style based on detector type
        if detector_type == 'object_detection':
            header_bg_color = (37, 37, 38)  # Dark gray
            header_accent = (66, 165, 245)  # Blue
            header_text = "COCO Object Detection"
        else:  # military_detection
            header_bg_color = (37, 37, 38)  # Dark gray
            header_accent = (239, 83, 80)   # Red
            header_text = "Military Object Detection"
        
        # Calculate label font scale based on image size
        base_font_scale = 0.4 * max(1, min(w, h) / 500)
        
        # Add a minimal modern header
        header_height = int(60 * base_font_scale)
        header_bar = np.zeros((header_height, w, 3), dtype=np.uint8)
        header_bar[:] = header_bg_color
        
        # Add accent line at bottom of header
        accent_height = int(3 * base_font_scale)
        header_bar[-accent_height:, :] = header_accent
        
        # Add header text
        font_scale = base_font_scale * 1.1
        font_thickness = max(1, int(1.5 * base_font_scale))
        cv2.putText(
            header_bar,
            header_text,
            (int(20 * base_font_scale), int(header_height * 0.6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            font_thickness
        )
        
        # Add the header to the result image
        result_img = np.vstack([header_bar, result_img])
        h = result_img.shape[0]  # Update height with header
        
        # Draw detections on the overlay
        for det in detections:
            x_min, y_min, x_max, y_max = map(int, det['bbox'])
            
            # Adjust for header
            y_min += header_height
            y_max += header_height
            
            # Make sure coordinates are within bounds
            x_min = max(0, x_min)
            y_min = max(0, y_min)
            x_max = min(w, x_max)
            y_max = min(h, y_max)
            
            label = det['label']
            conf = det['confidence']
            
            # Get color for this class
            rgba_color = COLOR_PALETTE.get(label.lower(), COLOR_PALETTE['default'])
            color = rgba_color[:3]  # BGR format
            alpha = rgba_color[3]   # Transparency value
            
            # Create a more visible detection box (semi-transparent fill)
            overlay = result_img.copy()
            cv2.rectangle(overlay, (x_min, y_min), (x_max, y_max), color, -1)
            
            # Apply alpha blending for the fill
            cv2.addWeighted(
                overlay, 
                alpha, 
                result_img, 
                1 - alpha, 
                0, 
                result_img
            )
            
            # Draw a solid border (more visible)
            border_thickness = max(2, int(3 * base_font_scale))
            cv2.rectangle(
                result_img, 
                (x_min, y_min), 
                (x_max, y_max), 
                color, 
                border_thickness
            )
            
            # Create an improved label with better visibility
            label_text = f"{label} {conf:.2f}"
            font_scale = base_font_scale * 0.9  # Slightly larger font
            thickness = max(1, int(base_font_scale * 1.2))  # Thicker text
            
            # Get text size for the label
            (text_width, text_height), baseline = cv2.getTextSize(
                label_text, 
                cv2.FONT_HERSHEY_SIMPLEX, 
                font_scale, 
                thickness
            )
            
            # Add padding to label background
            padding = int(6 * base_font_scale)
            
            # Make sure label doesn't go above the image
            label_y_min = max(header_height, y_min - text_height - padding * 2)
            
            # Position label at top of bounding box with solid background
            label_bg = np.array([
                [x_min, label_y_min],
                [x_min + text_width + padding * 2, label_y_min],
                [x_min + text_width + padding * 2, label_y_min + text_height + padding * 2],
                [x_min, label_y_min + text_height + padding * 2]
            ], np.int32)
            
            # Draw solid label background (no transparency)
            cv2.fillPoly(result_img, [label_bg], color)
            
            # Add a white border around the label for better visibility
            cv2.polylines(result_img, [label_bg], True, (255, 255, 255), 1)
            
            # Draw label text in white with improved visibility
            cv2.putText(
                result_img,
                label_text,
                (x_min + padding, label_y_min + text_height + padding),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (255, 255, 255),
                thickness
            )
        
        # Add a footer with model info
        footer_height = int(40 * base_font_scale)
        footer_bar = np.zeros((footer_height, w, 3), dtype=np.uint8)
        footer_bar[:] = header_bg_color
        
        # Add accent line at top of footer
        footer_bar[:accent_height, :] = header_accent
        
        # Add model info
        model_name = list(MODEL_CONFIG[detector_type].keys())[0]
        detection_count = f"Detections: {len(detections)}"
        
        # Add model info to footer
        cv2.putText(
            footer_bar,
            f"Model: {model_name}",
            (int(20 * base_font_scale), int(footer_height * 0.6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            base_font_scale * 0.7,
            (255, 255, 255),  # Brighter text color
            1
        )
        
        # Add detection count to right side
        (text_width, _), _ = cv2.getTextSize(
            detection_count, 
            cv2.FONT_HERSHEY_SIMPLEX, 
            base_font_scale * 0.7, 
            1
        )
        
        cv2.putText(
            footer_bar,
            detection_count,
            (w - text_width - int(20 * base_font_scale), int(footer_height * 0.6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            base_font_scale * 0.7,
            (255, 255, 255),  # Brighter text color
            1
        )
        
        # Add the footer to the result image
        result_img = np.vstack([result_img, footer_bar])
        
        return result_img

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
    logger.info(f"Processing file ID {marker_file.id} with detector types: {detector_types}")
    
    # Check if file exists
    if not marker_file.file:
        logger.warning(f"File not found: {marker_file.id}")
        return []
    
    try:
        file_path = marker_file.file.path
        if not os.path.exists(file_path):
            logger.warning(f"File does not exist on disk: {file_path}")
            return []
            
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Check if it's a processable image
        processable_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp']
        if file_ext not in processable_extensions:
            logger.warning(f"Skipping non-processable file: {file_path} (format: {file_ext})")
            return []
        
        # Check for existing detections and remove if requested
        existing_detections = marker_file.detections.filter(detector_type__in=detector_types)
        if existing_detections.exists():
            logger.info(f"Found {existing_detections.count()} existing detections, deleting them for reprocessing")
            existing_detections.delete()
        
        # Process with model service
        try:
            logger.info(f"Calling model service for file {marker_file.id}")
            start_time = time.time()
            results = model_service.process_image(file_path, detector_types)
            logger.info(f"Model processing completed in {time.time() - start_time:.2f}s for detector types: {list(results.keys())}")
        except Exception as e:
            logger.error(f"Error in model processing: {str(e)}")
            logger.error(traceback.format_exc())
            return []
        
        # Create detection records
        detection_objects = []
        
        for detector_type, result_data in results.items():
            try:
                logger.info(f"Creating detection record for {detector_type}")
                
                # Create base detection record
                detection = Detection(
                    marker_file=marker_file,
                    detector_type=detector_type,
                    model_name=result_data['model_name']
                )
                
                result = result_data['result']
                
                # Store overall summary
                detection.summary = result.get('summary', '')
                
                # Store the relative path for serving via URL
                if 'relative_path' in result:
                    detection.image_path = result['relative_path']
                
                # Store inference time if available
                if 'inference_time' in result:
                    detection.metadata = {'inference_time': result['inference_time']}
                
                detection.save()
                logger.info(f"Saved detection ID {detection.id}")
                
                # Store individual detections
                for det in result.get('detections', []):
                    object_detection = ObjectDetection.objects.create(
                        detection=detection,
                        label=det['label'],
                        confidence=det['confidence'],
                        x_min=det['bbox'][0],
                        y_min=det['bbox'][1],
                        x_max=det['bbox'][2],
                        y_max=det['bbox'][3]
                    )
                    logger.info(f"Created object detection {object_detection.id}: {det['label']} ({det['confidence']:.2f})")
                
                detection_objects.append(detection)
                
            except Exception as e:
                logger.error(f"Error creating detection record: {str(e)}")
                logger.error(traceback.format_exc())
        
        return detection_objects
        
    except Exception as e:
        logger.error(f"Error in process_marker_file: {str(e)}")
        logger.error(traceback.format_exc())
        return []

def process_marker(marker) -> Dict[str, int]:
    """
    Process all files for a marker based on its detection settings
    
    Args:
        marker: Marker instance
        
    Returns:
        Summary of processed files and detections
    """
    logger.info(f"Starting process_marker for marker ID {marker.id}")
    
    detector_types = []
    
    # Check which detector types are enabled - use the correct field names
    if marker.object_detection:
        detector_types.append('object_detection')
    if marker.camouflage_detection:  # Model field name
        detector_types.append('military_detection')  # Detector type name
    if marker.damage_assessment:
        detector_types.append('damage_assessment')
    if marker.thermal_analysis:  # Model field name
        detector_types.append('emergency_recognition')  # Detector type name
    
    logger.info(f"Enabled detector types: {detector_types}")
    
    if not detector_types:
        logger.info(f"No AI detection options enabled for marker {marker.id}")
        return {'processed': 0, 'detections': 0, 'errors': 0}
    
    # Process all files
    processed_count = 0
    detection_count = 0
    error_count = 0
    start_time = time.time()
    
    # Process all files
    for marker_file in marker.files.all():
        try:
            file_path = marker_file.file.path
            # Check if the file exists
            if not os.path.exists(file_path):
                logger.warning(f"File not found on disk: {file_path}")
                error_count += 1
                continue
                
            logger.info(f"Processing file {marker_file.id} with detector types {detector_types}")
            detections = process_marker_file(marker_file, detector_types)
            
            if detections:
                processed_count += 1
                detection_count += len(detections)
                logger.info(f"Created {len(detections)} detections for file {marker_file.id}")
            else:
                logger.info(f"No detections created for file {marker_file.id}")
                
        except Exception as e:
            logger.error(f"Error processing file {marker_file.id}: {str(e)}")
            logger.error(traceback.format_exc())
            error_count += 1
    
    # Calculate total processing time
    total_time = time.time() - start_time
    
    result = {
        'processed': processed_count,
        'detections': detection_count,
        'errors': error_count,
        'processing_time': f"{total_time:.2f}s"
    }
    
    logger.info(f"Finished processing marker {marker.id}: {result}")
    return result
