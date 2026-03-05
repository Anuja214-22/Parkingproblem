from datetime import datetime
from flask import current_app

def calculate_parking_fee(entry_time, exit_time):
    """
    Calculate parking fee based on duration
    
    Args:
        entry_time: datetime when vehicle entered
        exit_time: datetime when vehicle exited
    
    Returns:
        float: calculated fee
    """
    # Calculate duration in hours
    duration = (exit_time - entry_time).total_seconds() / 3600
    
    # Get fee configuration
    fee_per_hour = current_app.config.get('PARKING_FEE_PER_HOUR', 5.0)
    minimum_charge = current_app.config.get('MINIMUM_CHARGE', 2.0)
    
    # Calculate fee
    if duration == 0:
        fee = minimum_charge
    elif duration < 1:
        fee = minimum_charge
    else:
        fee = duration * fee_per_hour
    
    return round(fee, 2)


def get_parking_duration_string(entry_time, exit_time):
    """
    Get human-readable parking duration
    
    Args:
        entry_time: datetime when vehicle entered
        exit_time: datetime when vehicle exited
    
    Returns:
        str: formatted duration string
    """
    duration = exit_time - entry_time
    
    hours = int(duration.total_seconds() // 3600)
    minutes = int((duration.total_seconds() % 3600) // 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"