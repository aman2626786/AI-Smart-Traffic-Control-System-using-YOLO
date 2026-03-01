# Quick Start Guide - AI Traffic Management System

## Step 1: Install Dependencies

```cmd
cd backend
pip install -r requirements.txt
```

## Step 2: Run the Application

```cmd
python main.py
```

## Step 3: Open in Browser

Open your browser and go to:
```
http://localhost:8000
```

## Step 4: Upload Image

1. Click "Choose Image" or drag and drop a traffic image
2. Wait for detection to complete
3. View results with:
   - Annotated image with bounding boxes
   - Vehicle counts (total, cars, trucks)
   - Average confidence score
   - Traffic light timing recommendation

## Troubleshooting

### Error: Model file not found
Make sure `models/best.pt` exists in the project directory.

### Error: Module not found
Run: `pip install -r requirements.txt` from the backend directory

### Port already in use
Change the port in `backend/config.py` or set environment variable:
```cmd
set PORT=8080
python main.py
```

## Project Structure

```
E:\Vehicles Detection Model\
├── backend/
│   ├── main.py              # Start here!
│   ├── config.py
│   ├── detector.py
│   ├── traffic_logic.py
│   ├── models.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── models/
│   └── best.pt              # Your YOLO model
└── uploads/                 # Temporary files
```

## API Endpoints

- `GET /` - Frontend interface
- `POST /api/detect` - Upload image for detection
- `GET /api/health` - Check service status

Enjoy! 🚦
