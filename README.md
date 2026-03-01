# AI Traffic Management System

Production-ready web application for vehicle detection and intelligent traffic light timing using YOLOv8.

## Features

- 🚗 Vehicle detection (cars and trucks) using YOLOv8
- 📊 Real-time vehicle counting and statistics
- 🚦 Intelligent traffic light timing recommendations
- 🎨 Modern web interface with drag-and-drop upload
- 📦 Production-ready FastAPI backend
- ⚡ Fast inference with model loaded at startup

## Project Structure

```
ai-traffic-management/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── models.py            # Pydantic models
│   ├── detector.py          # YOLO detection logic
│   ├── traffic_logic.py     # Traffic timing logic
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Main HTML page
│   ├── styles.css           # CSS styling
│   └── app.js               # JavaScript logic
├── models/
│   └── best.pt              # YOLOv8 trained model
└── uploads/                 # Temporary uploads
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup Steps

1. **Install Python dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Verify model file:**
Ensure `models/best.pt` exists in the project directory.

## Running the Application

1. **Start the FastAPI server:**
```bash
cd backend
python main.py
```

2. **Open your browser:**
Navigate to: `http://localhost:8000`

The application will:
- Load the YOLO model at startup
- Serve the frontend interface
- Accept image uploads for vehicle detection

## Usage

1. Open the web interface at `http://localhost:8000`
2. Upload a traffic image (JPEG or PNG)
3. View detection results:
   - Annotated image with bounding boxes
   - Vehicle counts (total, cars, trucks)
   - Average detection confidence
   - Traffic light timing recommendation

## Traffic Logic

The system recommends green light duration based on vehicle count:

- **< 5 vehicles** → Green for 10 seconds (Low traffic)
- **5-11 vehicles** → Green for 25 seconds (Moderate traffic)
- **≥ 12 vehicles** → Green for 40 seconds (Heavy traffic)

## API Documentation

### Detection Endpoint

**POST** `/api/detect`

Upload an image for vehicle detection.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (image file)

**Response:**
```json
{
  "success": true,
  "total_vehicles": 8,
  "cars": 6,
  "trucks": 2,
  "average_confidence": 0.87,
  "traffic_decision": {
    "light": "green",
    "duration": 25,
    "reason": "Moderate traffic (5-11 vehicles)"
  },
  "detections": [...],
  "annotated_image": "data:image/jpeg;base64,..."
}
```

### Health Check

**GET** `/api/health`

Check if the service is running and model is loaded.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

## Configuration

Edit `backend/config.py` to customize:

- `MODEL_PATH`: Path to YOLO model
- `MAX_FILE_SIZE`: Maximum upload size (default: 10MB)
- `CONFIDENCE_THRESHOLD`: Detection confidence threshold (default: 0.25)
- `ALLOWED_EXTENSIONS`: Supported image formats

## Error Handling

The application handles:
- Invalid file formats
- File size limits
- Model loading errors
- Detection failures
- Network errors

## Development

### Running Tests

```bash
cd backend
pytest
```

### Code Formatting

```bash
black backend/
```

## Production Deployment

For production deployment:

1. Set environment variables for configuration
2. Use a production ASGI server (uvicorn with workers)
3. Configure CORS for your domain
4. Set up proper logging and monitoring
5. Implement rate limiting
6. Use HTTPS

## License

MIT License

## Support

For issues or questions, please open an issue on the project repository.
