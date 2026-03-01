"""FastAPI application for AI Traffic Management System."""
import logging
import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image
from io import BytesIO
import config
from detector import VehicleDetector
from video_processor import VideoProcessor
from traffic_logic import calculate_traffic_timing
from models import DetectionResponse, ErrorResponse, DetectionResult
import shutil
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Traffic Management System",
    description="Vehicle detection and traffic light timing using YOLOv8",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global detector instance
detector: Optional[VehicleDetector] = None
video_processor: Optional[VideoProcessor] = None


@app.on_event("startup")
async def startup_event():
    """Load YOLO model at startup."""
    global detector, video_processor
    try:
        logger.info(f"Loading YOLO model from {config.MODEL_PATH}")
        
        # Check if model file exists
        if not os.path.exists(config.MODEL_PATH):
            logger.error(f"Model file not found: {config.MODEL_PATH}")
            raise FileNotFoundError(f"Model file not found: {config.MODEL_PATH}")
        
        detector = VehicleDetector(config.MODEL_PATH)
        video_processor = VideoProcessor(detector)
        logger.info("YOLO model loaded successfully")
        
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": detector is not None
    }


@app.post("/api/detect", response_model=DetectionResponse)
async def detect_vehicles(file: UploadFile = File(...)):
    """
    Detect vehicles in uploaded image.
    
    Args:
        file: Uploaded image file
        
    Returns:
        DetectionResponse with vehicle counts, detections, and traffic decision
    """
    try:
        # Check if model is loaded
        if detector is None:
            raise HTTPException(
                status_code=503,
                detail="Model not loaded. Service unavailable."
            )
        
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in config.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format. Allowed: {', '.join(config.ALLOWED_EXTENSIONS)}"
            )
        
        # Read and validate file size
        contents = await file.read()
        if len(contents) > config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {config.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        # Open image
        try:
            image = Image.open(BytesIO(contents))
            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file: {str(e)}"
            )
        
        # Run detection
        logger.info(f"Processing image: {file.filename}")
        detections = detector.detect(image)
        
        # Get statistics
        stats = detector.get_statistics(detections)
        
        # Calculate traffic timing
        traffic_decision = calculate_traffic_timing(stats["total_vehicles"])
        
        # Draw bounding boxes
        annotated_image = detector.draw_boxes(image, detections)
        
        # Convert to base64
        annotated_image_b64 = detector.image_to_base64(annotated_image)
        
        # Format detections for response
        detection_results = [
            DetectionResult(
                class_name=d["class"],
                confidence=d["confidence"],
                bbox=d["bbox"]
            )
            for d in detections
        ]
        
        logger.info(f"Detection complete: {stats['total_vehicles']} vehicles found")
        
        return DetectionResponse(
            success=True,
            total_vehicles=stats["total_vehicles"],
            cars=stats["cars"],
            trucks=stats["trucks"],
            average_confidence=stats["average_confidence"],
            traffic_decision=traffic_decision,
            detections=detection_results,
            annotated_image=annotated_image_b64
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detection error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Detection failed: {str(e)}"
        )


@app.post("/api/detect-video")
async def detect_video(file: UploadFile = File(...)):
    """
    Process video for vehicle detection and traffic analysis.
    
    Args:
        file: Uploaded video file
        
    Returns:
        JSON with processed video path and statistics
    """
    try:
        # Check if model is loaded
        if detector is None or video_processor is None:
            raise HTTPException(
                status_code=503,
                detail="Model not loaded. Service unavailable."
            )
        
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in config.ALLOWED_VIDEO_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid video format. Allowed: {', '.join(config.ALLOWED_VIDEO_EXTENSIONS)}"
            )
        
        # Read and validate file size
        contents = await file.read()
        if len(contents) > config.MAX_VIDEO_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Video too large. Maximum size: {config.MAX_VIDEO_SIZE / (1024*1024):.1f}MB"
            )
        
        # Save uploaded video temporarily
        input_filename = f"input_{uuid.uuid4().hex[:8]}{file_ext}"
        input_path = os.path.join(config.UPLOAD_DIR, input_filename)
        
        with open(input_path, "wb") as buffer:
            buffer.write(contents)
        
        logger.info(f"Processing video: {file.filename}")
        
        # Process video
        result = video_processor.process_video(input_path)
        
        # Clean up input file
        try:
            os.remove(input_path)
        except:
            pass
        
        logger.info(f"Video processing complete: {result['average_vehicle_count']} avg vehicles")
        
        return JSONResponse({
            "success": True,
            "output_filename": result["output_filename"],
            "download_url": f"/api/download-video/{result['output_filename']}",
            "total_frames": result["total_frames"],
            "average_vehicle_count": result["average_vehicle_count"],
            "max_vehicle_count": result["max_vehicle_count"],
            "min_vehicle_count": result["min_vehicle_count"],
            "video_duration_seconds": result["video_duration_seconds"],
            "traffic_decision": {
                "light": result["traffic_decision"].light,
                "duration": result["traffic_decision"].duration,
                "reason": result["traffic_decision"].reason
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video processing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Video processing failed: {str(e)}"
        )


@app.get("/api/download-video/{filename}")
async def download_video(filename: str):
    """
    Download processed video.
    
    Args:
        filename: Name of the processed video file
        
    Returns:
        Video file
    """
    video_path = os.path.join(config.VIDEO_OUTPUT_DIR, filename)
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=filename
    )


# Serve frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    
    @app.get("/")
    async def serve_frontend():
        """Serve the frontend HTML page."""
        return FileResponse(str(frontend_path / "index.html"))


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {config.HOST}:{config.PORT}")
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=False
    )
