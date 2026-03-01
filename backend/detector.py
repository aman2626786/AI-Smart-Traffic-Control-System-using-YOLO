"""YOLO-based vehicle detection module."""
import base64
from io import BytesIO
from typing import List, Dict, Tuple
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
import config


class VehicleDetector:
    """Vehicle detection using YOLOv8 model."""
    
    def __init__(self, model_path: str):
        """
        Initialize the detector with YOLO model.
        
        Args:
            model_path: Path to the YOLOv8 model file (.pt)
        """
        self.model = YOLO(model_path)
        self.vehicle_classes = {"car", "truck"}
        
    def detect(self, image: Image.Image) -> List[Dict]:
        """
        Run vehicle detection on an image.
        
        Args:
            image: PIL Image object
            
        Returns:
            List of detections with class, confidence, and bbox
        """
        # Run inference
        results = self.model(image, conf=config.CONFIDENCE_THRESHOLD)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get class name
                class_id = int(box.cls[0])
                class_name = self.model.names[class_id]
                
                # Filter for vehicles only
                if class_name.lower() in self.vehicle_classes:
                    confidence = float(box.conf[0])
                    bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                    
                    detections.append({
                        "class": class_name.lower(),
                        "confidence": confidence,
                        "bbox": bbox
                    })
        
        return detections
    
    def draw_boxes(self, image: Image.Image, detections: List[Dict]) -> Image.Image:
        """
        Draw bounding boxes on image.
        
        Args:
            image: PIL Image object
            detections: List of detection dictionaries
            
        Returns:
            Annotated PIL Image
        """
        # Convert PIL to OpenCV format
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Define colors for different classes
        colors = {
            "car": (0, 255, 0),      # Green
            "truck": (255, 165, 0)   # Orange
        }
        
        for det in detections:
            class_name = det["class"]
            confidence = det["confidence"]
            bbox = det["bbox"]
            
            # Extract coordinates
            x1, y1, x2, y2 = map(int, bbox)
            
            # Get color
            color = colors.get(class_name, (0, 255, 0))
            
            # Draw rectangle
            cv2.rectangle(img_cv, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            
            # Draw label background
            cv2.rectangle(img_cv, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            
            # Draw label text
            cv2.putText(img_cv, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Convert back to PIL
        img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        return img_pil
    
    def get_statistics(self, detections: List[Dict]) -> Dict:
        """
        Calculate detection statistics.
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            Dictionary with counts and average confidence
        """
        total_vehicles = len(detections)
        cars = sum(1 for d in detections if d["class"] == "car")
        trucks = sum(1 for d in detections if d["class"] == "truck")
        
        # Calculate average confidence
        if total_vehicles > 0:
            avg_confidence = sum(d["confidence"] for d in detections) / total_vehicles
        else:
            avg_confidence = 0.0
        
        return {
            "total_vehicles": total_vehicles,
            "cars": cars,
            "trucks": trucks,
            "average_confidence": round(avg_confidence, 2)
        }
    
    @staticmethod
    def image_to_base64(image: Image.Image) -> str:
        """
        Convert PIL Image to base64 string.
        
        Args:
            image: PIL Image object
            
        Returns:
            Base64 encoded image string with data URI prefix
        """
        buffered = BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"
