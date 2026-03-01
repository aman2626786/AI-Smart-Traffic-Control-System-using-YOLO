"""Pydantic models for request and response validation."""
from typing import List, Optional
from pydantic import BaseModel, Field


class DetectionResult(BaseModel):
    """Single vehicle detection result."""
    class_name: str = Field(..., alias="class", description="Vehicle class (car or truck)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    bbox: List[float] = Field(..., min_length=4, max_length=4, description="Bounding box [x1, y1, x2, y2]")

    class Config:
        populate_by_name = True


class TrafficDecision(BaseModel):
    """Traffic light timing decision."""
    light: str = Field(..., description="Traffic light color")
    duration: int = Field(..., gt=0, description="Duration in seconds")
    reason: str = Field(..., description="Reason for the decision")


class DetectionResponse(BaseModel):
    """Complete detection API response."""
    success: bool = Field(True, description="Whether the detection was successful")
    total_vehicles: int = Field(..., ge=0, description="Total number of vehicles detected")
    cars: int = Field(..., ge=0, description="Number of cars detected")
    trucks: int = Field(..., ge=0, description="Number of trucks detected")
    average_confidence: float = Field(..., ge=0.0, le=1.0, description="Average detection confidence")
    traffic_decision: TrafficDecision = Field(..., description="Traffic light timing recommendation")
    detections: List[DetectionResult] = Field(..., description="List of all detections")
    annotated_image: str = Field(..., description="Base64 encoded annotated image")


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error message")
