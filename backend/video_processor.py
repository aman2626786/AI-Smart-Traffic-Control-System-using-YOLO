"""Video processing module for traffic analysis."""
import cv2
import numpy as np
import uuid
import os
from pathlib import Path
from typing import Dict, List
import config
from traffic_logic import calculate_traffic_timing


class VideoProcessor:
    """Process videos for vehicle detection and traffic analysis."""
    
    def __init__(self, detector):
        """
        Initialize video processor.
        
        Args:
            detector: VehicleDetector instance
        """
        self.detector = detector
        
        # Create output directory if it doesn't exist
        os.makedirs(config.VIDEO_OUTPUT_DIR, exist_ok=True)
    
    def process_video(self, input_path: str) -> Dict:
        """
        Process video file for vehicle detection.
        
        Args:
            input_path: Path to input video file
            
        Returns:
            Dictionary with output path and statistics
        """
        # Generate unique output filename
        output_filename = f"output_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(config.VIDEO_OUTPUT_DIR, output_filename)
        
        # Open video
        cap = cv2.VideoCapture(input_path)
        
        if not cap.isOpened():
            raise ValueError("Could not open video file")
        
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Processing variables
        vehicle_history = []
        total_vehicles_per_frame = []
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert BGR to RGB for PIL
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            from PIL import Image
            pil_image = Image.fromarray(frame_rgb)
            
            # Run detection
            detections = self.detector.detect(pil_image)
            
            # Get vehicle count
            total_vehicles = len(detections)
            total_vehicles_per_frame.append(total_vehicles)
            
            # Maintain sliding window for smoothing (1 second)
            vehicle_history.append(total_vehicles)
            if len(vehicle_history) > fps:
                vehicle_history.pop(0)
            
            # Calculate stable count (smoothed)
            stable_count = int(np.mean(vehicle_history)) if vehicle_history else 0
            
            # Get traffic decision
            traffic_decision = calculate_traffic_timing(stable_count)
            
            # Calculate average confidence
            if detections:
                avg_confidence = sum(d["confidence"] for d in detections) / len(detections)
            else:
                avg_confidence = 0.0
            
            # Draw bounding boxes on frame
            annotated_frame = self._draw_boxes_on_frame(frame, detections)
            
            # Add text overlays
            self._add_overlays(
                annotated_frame,
                stable_count,
                traffic_decision,
                avg_confidence,
                frame_count,
                total_frames
            )
            
            # Write frame
            out.write(annotated_frame)
            frame_count += 1
        
        # Release resources
        cap.release()
        out.release()
        
        # Calculate final statistics
        avg_vehicle_count = int(np.mean(total_vehicles_per_frame)) if total_vehicles_per_frame else 0
        max_vehicle_count = max(total_vehicles_per_frame) if total_vehicles_per_frame else 0
        min_vehicle_count = min(total_vehicles_per_frame) if total_vehicles_per_frame else 0
        
        final_decision = calculate_traffic_timing(avg_vehicle_count)
        
        return {
            "output_path": output_path,
            "output_filename": output_filename,
            "total_frames": frame_count,
            "average_vehicle_count": avg_vehicle_count,
            "max_vehicle_count": max_vehicle_count,
            "min_vehicle_count": min_vehicle_count,
            "traffic_decision": final_decision,
            "video_duration_seconds": frame_count / fps if fps > 0 else 0
        }
    
    def _draw_boxes_on_frame(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Draw bounding boxes on video frame.
        
        Args:
            frame: OpenCV frame (BGR)
            detections: List of detection dictionaries
            
        Returns:
            Annotated frame
        """
        colors = {
            "car": (0, 255, 0),      # Green
            "truck": (255, 165, 0)   # Orange
        }
        
        for det in detections:
            class_name = det["class"]
            confidence = det["confidence"]
            bbox = det["bbox"]
            
            x1, y1, x2, y2 = map(int, bbox)
            color = colors.get(class_name, (0, 255, 0))
            
            # Draw rectangle
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            
            # Label background
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10),
                         (x1 + label_size[0], y1), color, -1)
            
            # Label text
            cv2.putText(frame, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return frame
    
    def _add_overlays(self, frame: np.ndarray, vehicle_count: int,
                     traffic_decision, avg_confidence: float,
                     current_frame: int, total_frames: int):
        """
        Add text overlays to frame.
        
        Args:
            frame: OpenCV frame
            vehicle_count: Number of vehicles
            traffic_decision: TrafficDecision object
            avg_confidence: Average confidence score
            current_frame: Current frame number
            total_frames: Total frames in video
        """
        # Background for text
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Vehicle count
        cv2.putText(frame, f"Vehicles: {vehicle_count}", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Traffic decision
        decision_text = f"{traffic_decision.light.upper()} - {traffic_decision.duration}s"
        cv2.putText(frame, decision_text, (20, 75),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Reason
        cv2.putText(frame, traffic_decision.reason, (20, 105),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Confidence
        cv2.putText(frame, f"Confidence: {avg_confidence:.2%}", (20, 135),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Progress
        progress = f"Frame: {current_frame}/{total_frames}"
        cv2.putText(frame, progress, (frame.shape[1] - 250, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
