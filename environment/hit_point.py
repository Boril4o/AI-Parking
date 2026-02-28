from typing import Optional

from pygame import Vector2


class HitPoint:
    """Result of a raycast hit: the hit position (if any) and normalized distance (0.0-1.0)."""

    def __init__(self, point: Optional[tuple[float, float] | Vector2], distance: float):
        self.point = point
        self.distance = distance
