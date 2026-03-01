"""Traffic light timing logic based on vehicle count."""
from models import TrafficDecision


def calculate_traffic_timing(vehicle_count: int) -> TrafficDecision:
    """
    Calculate traffic light timing based on vehicle count.
    
    Rules:
    - < 5 vehicles: Green for 10 seconds (Low traffic)
    - 5-11 vehicles: Green for 25 seconds (Moderate traffic)
    - >= 12 vehicles: Green for 40 seconds (Heavy traffic)
    
    Args:
        vehicle_count: Total number of vehicles detected
        
    Returns:
        TrafficDecision with light color, duration, and reason
    """
    if vehicle_count < 5:
        return TrafficDecision(
            light="green",
            duration=10,
            reason="Low traffic (< 5 vehicles)"
        )
    elif vehicle_count < 12:
        return TrafficDecision(
            light="green",
            duration=25,
            reason="Moderate traffic (5-11 vehicles)"
        )
    else:
        return TrafficDecision(
            light="green",
            duration=40,
            reason="Heavy traffic (≥ 12 vehicles)"
        )
