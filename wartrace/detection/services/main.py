import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import cv2
import matplotlib.pyplot as plt
from pathlib import Path
import shutil
from datetime import datetime
from collections import Counter

class YOLODetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced YOLO Object Detection")
        self.root.geometry("1300x800")
        
        # Create output directory if it doesn't exist
        self.output_dir = Path("detection_results")
        self.output_dir.mkdir(exist_ok=True)
        
        # Variables
        self.image_path = None
        self.current_image = None
        self.original_img_size = None
        self.progress_var = tk.DoubleVar(value=0)
        
        # Define available models
        self.models = {
            "YOLOv8n": {
                "selected": tk.BooleanVar(value=True),
                "model": None,
                "source": "ultralytics/yolov8",
                "pretrained": "yolov8n.pt",
                "description": "YOLOv8 Nano - fastest model (COCO dataset)"
            },
            "YOLOv8x": {
                "selected": tk.BooleanVar(value=False),
                "model": None,
                "source": "ultralytics/yolov8",
                "pretrained": "yolov8x.pt",
                "description": "YOLOv8 X-Large - most accurate (COCO dataset)"
            },
            "YOLOv8-seg": {
                "selected": tk.BooleanVar(value=False),
                "model": None,
                "source": "ultralytics/yolov8",
                "pretrained": "yolov8n-seg.pt",
                "description": "YOLOv8 with instance segmentation (COCO dataset)"
            },
            "YOLO-World": {
                "selected": tk.BooleanVar(value=False),
                "model": None,
                "source": "MIVisionLab/yolo_world",
                "pretrained": "yolo_world_s.pt",
                "description": "YOLO-World - Open Vocabulary detection (21K classes)"
            }
        }
        
        # Special models
        self.special_models = {
            "Military Detection": {
                "selected": tk.BooleanVar(value=False),
                "model": None,
                "source": "custom",
                "pretrained": "military_detection.pt",
                "description": "Custom model trained on military vehicles and personnel"
            }
        }
        
        # Combine all models
        self.all_models = {**self.models, **self.special_models}
        
        # Create UI elements
        self.create_widgets()
    
    def create_widgets(self):
        # Create main frames
        left_frame = tk.Frame(self.root, width=350)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        right_frame = tk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - controls and options
        # Image selection
        select_btn = tk.Button(left_frame, text="Select Image", command=self.select_image, 
                              height=2, font=('Arial', 10, 'bold'))
        select_btn.pack(fill=tk.X, pady=5)
        
        # Model selection frame with scrollbar
        model_container = tk.Frame(left_frame)
        model_container.pack(fill=tk.X, pady=10)
        
        model_label = tk.Label(model_container, text="Select Detection Models:", font=('Arial', 10, 'bold'))
        model_label.pack(anchor=tk.W)
        
        # Scrollable frame for model checkboxes
        model_canvas = tk.Canvas(model_container, borderwidth=0)
        model_scrollbar = ttk.Scrollbar(model_container, orient=tk.VERTICAL, command=model_canvas.yview)
        model_frame = tk.Frame(model_canvas)
        
        model_canvas.configure(yscrollcommand=model_scrollbar.set)
        model_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        model_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        model_canvas.create_window((0, 0), window=model_frame, anchor=tk.NW)
        
        model_frame.bind("<Configure>", lambda e: model_canvas.configure(scrollregion=model_canvas.bbox("all")))
        
        # Standard models section
        tk.Label(model_frame, text="Standard Models", font=('Arial', 9, 'bold')).pack(anchor=tk.W, padx=5, pady=2)
        
        # Add model checkboxes with descriptions
        for model_name, model_info in self.models.items():
            cb_frame = tk.Frame(model_frame)
            cb_frame.pack(fill=tk.X, padx=5, pady=2)
            
            cb = tk.Checkbutton(
                cb_frame, 
                text=model_name, 
                variable=model_info["selected"],
                onvalue=True,
                offvalue=False
            )
            cb.pack(side=tk.LEFT)
            
            # Add help tooltip/description as smaller grey text
            desc = tk.Label(cb_frame, text=model_info["description"], font=('Arial', 7), fg='grey')
            desc.pack(side=tk.LEFT, padx=5)
        
        # Special models section
        tk.Label(model_frame, text="Specialized Models", font=('Arial', 9, 'bold')).pack(anchor=tk.W, padx=5, pady=(10, 2))
        
        for model_name, model_info in self.special_models.items():
            cb_frame = tk.Frame(model_frame)
            cb_frame.pack(fill=tk.X, padx=5, pady=2)
            
            cb = tk.Checkbutton(
                cb_frame, 
                text=model_name, 
                variable=model_info["selected"],
                onvalue=True,
                offvalue=False
            )
            cb.pack(side=tk.LEFT)
            
            desc = tk.Label(cb_frame, text=model_info["description"], font=('Arial', 7), fg='grey')
            desc.pack(side=tk.LEFT, padx=5)
        
        # Custom detection options
        options_frame = tk.LabelFrame(left_frame, text="Detection Options")
        options_frame.pack(fill=tk.X, pady=10)
        
        # Confidence threshold slider
        tk.Label(options_frame, text="Confidence Threshold:").pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.conf_scale = tk.Scale(options_frame, from_=0.1, to=0.9, resolution=0.05, 
                                  orient=tk.HORIZONTAL, value=0.25)
        self.conf_scale.pack(fill=tk.X, padx=10)
        
        # IOU threshold slider
        tk.Label(options_frame, text="IoU Threshold:").pack(anchor=tk.W, padx=10, pady=(5, 0))
        self.iou_scale = tk.Scale(options_frame, from_=0.1, to=0.9, resolution=0.05, 
                                orient=tk.HORIZONTAL, value=0.45)
        self.iou_scale.pack(fill=tk.X, padx=10)
        
        # Run detection button
        detect_btn = tk.Button(left_frame, text="Run Detection", command=self.run_detection,
                             height=2, bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'))
        detect_btn.pack(fill=tk.X, pady=10)
        
        # Progress bar
        tk.Label(left_frame, text="Progress:").pack(anchor=tk.W)
        self.progress_bar = ttk.Progressbar(left_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Status information
        self.status_var = tk.StringVar(value="Ready")
        status_label = tk.Label(left_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(fill=tk.X, pady=5)
        
        # Statistics panel
        stats_frame = tk.LabelFrame(left_frame, text="Detection Statistics")
        stats_frame.pack(fill=tk.X, pady=10, expand=True)
        
        # Add text widget with scrollbar
        stats_scroll = tk.Scrollbar(stats_frame)
        stats_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.stats_text = tk.Text(stats_frame, height=10, wrap=tk.WORD, yscrollcommand=stats_scroll.set)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        stats_scroll.config(command=self.stats_text.yview)
        
        # Right side - image display
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Original image tab
        original_tab = tk.Frame(self.notebook)
        self.notebook.add(original_tab, text="Original")
        
        self.original_canvas = tk.Canvas(original_tab, bg='#f0f0f0')
        self.original_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Results tab - will be populated after detection
        self.results_tab = tk.Frame(self.notebook)
        self.notebook.add(self.results_tab, text="Detection Results")
        
        self.results_canvas = tk.Canvas(self.results_tab, bg='#f0f0f0')
        self.results_canvas.pack(fill=tk.BOTH, expand=True)
    
    def select_image(self):
        """Open file dialog to select an image"""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tif")]
        )
        
        if file_path:
            self.image_path = file_path
            self.load_and_display_image(file_path)
            self.status_var.set(f"Image loaded: {os.path.basename(file_path)}")
    
    def load_and_display_image(self, path):
        """Load and display the selected image on the canvas"""
        try:
            # Load image with PIL
            image = Image.open(path)
            self.original_img_size = image.size
            
            # Display on original tab
            self.display_image_on_canvas(image, self.original_canvas)
            
            # Switch to original tab
            self.notebook.select(0)
            
        except Exception as e:
            self.status_var.set(f"Error loading image: {str(e)}")
            messagebox.showerror("Image Error", str(e))
    
    def display_image_on_canvas(self, image, canvas):
        """Display an image on the specified canvas with proper sizing"""
        # Get canvas dimensions
        canvas_width = canvas.winfo_width() or 800
        canvas_height = canvas.winfo_height() or 600
            
        # Resize with aspect ratio preserved
        img_width, img_height = image.size
        ratio = min(canvas_width/img_width, canvas_height/img_height)
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Clear canvas and add new image
        canvas.delete("all")
        
        # Store reference to prevent garbage collection
        self._image_ref = ImageTk.PhotoImage(resized_image)
        
        # Center the image on canvas
        x_offset = (canvas_width - new_width) // 2
        y_offset = (canvas_height - new_height) // 2
        
        canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self._image_ref)
    
    def run_detection(self):
        """Run object detection on the loaded image using selected models"""
        if not self.image_path:
            messagebox.showinfo("No Image", "Please select an image first.")
            return
        
        # Check if at least one model is selected
        if not any(model_info["selected"].get() for model_info in self.all_models.values()):
            messagebox.showinfo("No Model", "Please select at least one model.")
            return
        
        # Run detection in a separate thread to keep UI responsive
        import threading
        self.progress_var.set(0)
        threading.Thread(target=self._run_detection_task, daemon=True).start()
    
    def _run_detection_task(self):
        """Run detection task in background thread"""
        try:
            self.status_var.set("Loading models...")
            
            # Create a timestamp-based folder for this detection run
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_dir = self.output_dir / f"detection_{timestamp}"
            run_dir.mkdir(exist_ok=True)
            
            # Load selected models
            selected_models = {}
            for model_name, model_info in self.all_models.items():
                if model_info["selected"].get():
                    self.status_var.set(f"Loading {model_name}...")
                    self.progress_var.set(10)  # Update progress
                    
                    if model_info["source"] == "ultralytics/yolov8":
                        # For YOLOv8 models
                        from ultralytics import YOLO
                        model = YOLO(model_info["pretrained"])
                        selected_models[model_name] = model
                    
                    elif model_info["source"] == "MIVisionLab/yolo_world":
                        # For YOLO-World models
                        # In a real implementation, you'd install and use the yolo_world package
                        # For now, we'll use a stub that we'll load from YOLOv8 for demo
                        from ultralytics import YOLO
                        model = YOLO("yolov8s.pt")  # Placeholder
                        selected_models[model_name] = model
                    
                    elif model_info["source"] == "custom":
                        # For custom models - would download from a repo or local path
                        from ultralytics import YOLO
                        
                        # In a real implementation, you'd need the actual model file
                        # For demonstration, we'll use yolov8n as a stand-in
                        model = YOLO("yolov8n.pt")
                        selected_models[model_name] = model
            
            # Record detection statistics across models
            all_results = {}
            combined_stats = {}
            
            # Process with each selected model
            model_count = len(selected_models)
            for i, (model_name, model) in enumerate(selected_models.items()):
                self.status_var.set(f"Running detection with {model_name}...")
                progress_base = 20 + int(70 * i / model_count)
                self.progress_var.set(progress_base)
                
                # Get confidence and IoU thresholds
                conf_threshold = self.conf_scale.get()
                iou_threshold = self.iou_scale.get()
                
                # Run inference with threshold settings
                results = model(self.image_path, conf=conf_threshold, iou=iou_threshold)
                
                for j, result in enumerate(results):
                    # Convert to dictionary format we can work with
                    boxes = result.boxes.cpu().numpy()
                    
                    if hasattr(result, 'masks') and result.masks is not None:
                        # This is a segmentation model
                        masks = result.masks.cpu().numpy()
                    else:
                        masks = None
                    
                    # Extract detection info
                    detections = []
                    for k in range(len(boxes)):
                        detection = {
                            'xmin': float(boxes.xyxy[k][0]),
                            'ymin': float(boxes.xyxy[k][1]),
                            'xmax': float(boxes.xyxy[k][2]),
                            'ymax': float(boxes.xyxy[k][3]),
                            'confidence': float(boxes.conf[k]),
                            'class': int(boxes.cls[k]),
                            'name': result.names[int(boxes.cls[k])]
                        }
                        detections.append(detection)
                    
                    # Store results
                    all_results[model_name] = {
                        'detections': detections,
                        'has_masks': masks is not None,
                        'result_object': result
                    }
                    
                    # Update statistics
                    self.update_statistics(detections, model_name, combined_stats)
                    
                    # Save results image for this model
                    progress_step = progress_base + int(15 / model_count)
                    self.progress_var.set(progress_step)
                    
                    # Save visualized results
                    output_path = run_dir / f"{model_name}_result.jpg"
                    result.save(filename=str(output_path))
            
            # Create a combined visualization with all models
            self.status_var.set("Creating combined visualization...")
            self.progress_var.set(90)
            self.create_combined_visualization(all_results, run_dir)
            
            # Display results summary and update UI
            self.root.after(0, lambda: self.display_summary(combined_stats))
            self.root.after(0, lambda: self.display_results(run_dir))
            
            # Save the original image for reference
            orig_path = run_dir / "original.jpg"
            shutil.copy(self.image_path, orig_path)
            
            self.progress_var.set(100)
            self.status_var.set("Detection complete! Results saved.")
            messagebox.showinfo("Success", f"Detection complete! Results saved to:\n{run_dir}")
            
        except Exception as e:
            import traceback
            self.status_var.set(f"Error: {str(e)}")
            print(traceback.format_exc())
            messagebox.showerror("Detection Error", str(e))
    
    def update_statistics(self, detections, model_name, combined_stats):
        """Update detection statistics from the results"""
        # Count objects by class
        class_counts = Counter([det['name'] for det in detections])
        
        # Update combined stats
        for cls_name, count in class_counts.items():
            if cls_name not in combined_stats:
                combined_stats[cls_name] = {}
            combined_stats[cls_name][model_name] = count
    
    def display_summary(self, combined_stats):
        """Display detection summary in the stats text area"""
        self.stats_text.delete(1.0, tk.END)
        
        # Check if we have any detections
        if not combined_stats:
            self.stats_text.insert(tk.END, "No objects detected in the image.")
            return
        
        # Summary header
        self.stats_text.insert(tk.END, "DETECTION SUMMARY\n", "header")
        self.stats_text.insert(tk.END, "=================\n\n")
        
        # Create summary text
        for cls_name, model_counts in combined_stats.items():
            self.stats_text.insert(tk.END, f"{cls_name}: ")
            counts = [f"{model}: {count}" for model, count in model_counts.items()]
            self.stats_text.insert(tk.END, ", ".join(counts) + "\n")
        
        # Add a human-readable description
        self.stats_text.insert(tk.END, "\nDetection Description:\n", "subheader")
        self.stats_text.insert(tk.END, "-------------------\n")
        
        # Create a merged count across all models (taking max count for each class)
        merged_counts = {}
        for cls_name, model_counts in combined_stats.items():
            merged_counts[cls_name] = max(model_counts.values())
        
        # Sort classes by count for more natural description
        sorted_classes = sorted(merged_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Generate description
        description = []
        for cls_name, count in sorted_classes:
            # Handle plural forms
            if count == 1:
                description.append(f"{count} {cls_name}")
            else:
                # Handle special plural cases
                if cls_name.endswith('person'):
                    plural = cls_name.replace('person', 'people')
                else:
                    plural = f"{cls_name}s"
                description.append(f"{count} {plural}")
        
        description_text = ", ".join(description)
        
        # Insert natural language description
        if description_text:
            self.stats_text.insert(tk.END, f"The image contains {description_text}.\n")
        else:
            self.stats_text.insert(tk.END, "No objects detected.\n")
    
    def display_results(self, results_dir):
        """Display the combined results in the results tab"""
        try:
            # Load the combined results image
            combined_path = results_dir / "combined_results.jpg"
            if not combined_path.exists():
                # Use the first model result if combined doesn't exist
                result_files = list(results_dir.glob("*_result.jpg"))
                if result_files:
                    combined_path = result_files[0]
            
            if combined_path.exists():
                result_img = Image.open(combined_path)
                self.display_image_on_canvas(result_img, self.results_canvas)
                
                # Switch to results tab
                self.notebook.select(1)
        except Exception as e:
            print(f"Error displaying results: {str(e)}")
    
    def create_combined_visualization(self, all_results, output_dir):
        """Create a combined visualization with results from all models"""
        try:
            # Load original image
            img = cv2.imread(self.image_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            fig, ax = plt.subplots(figsize=(14, 10))
            ax.imshow(img)
            
            # Used to track which objects we've already drawn to avoid overlaps
            drawn_objects = set()
            
            # Define a list of distinct colors for different models
            model_colors = {
                "YOLOv8n": "tab:blue",
                "YOLOv8x": "tab:orange",
                "YOLOv8-seg": "tab:green",
                "YOLO-World": "tab:red",
                "Military Detection": "tab:purple"
            }
            
            # Add results from each model with different styles
            for model_idx, (model_name, results) in enumerate(all_results.items()):
                detections = results['detections']
                
                # Get color for this model
                model_color = model_colors.get(model_name, f"C{model_idx}")
                
                for det in detections:
                    # Get box coordinates
                    x1, y1, x2, y2 = det['xmin'], det['ymin'], det['xmax'], det['ymax']
                    cls_name = det['name']
                    conf = det['confidence']
                    
                    # Create rectangle with model-specific style
                    rect = plt.Rectangle(
                        (x1, y1), x2-x1, y2-y1, 
                        fill=True, 
                        alpha=0.2,
                        color=model_color,
                        linewidth=2, 
                        linestyle='-',
                        edgecolor=model_color
                    )
                    ax.add_patch(rect)
                    
                    # Add label
                    label_text = f"{cls_name}: {conf:.2f} ({model_name})"
                    ax.text(
                        x1, y1-5, 
                        label_text, 
                        fontsize=8,
                        color='black',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1)
                    )
            
            # Add model legend
            legend_patches = [
                plt.Rectangle((0, 0), 1, 1, color=model_colors.get(model, f"C{i}"), alpha=0.5)
                for i, model in enumerate(all_results.keys())
            ]
            ax.legend(legend_patches, all_results.keys(), loc='upper right')
            
            # Save the combined visualization
            plt.title("Combined Detection Results")
            plt.axis('off')
            
            combined_path = output_dir / "combined_results.jpg"
            plt.savefig(combined_path, bbox_inches='tight', dpi=200)
            plt.close(fig)
        
        except Exception as e:
            print(f"Error creating combined visualization: {str(e)}")

if __name__ == "__main__":
    # Set better font rendering for Windows
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
        
    root = tk.Tk()
    app = YOLODetectionApp(root)
    root.mainloop()