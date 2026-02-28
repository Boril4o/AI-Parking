scale = 50.0  # 1 meter = 50 pixels

def meters_to_pixels(meters: float | int) -> float:
    return meters * scale
