from pygame import Vector2

from environment.hit_point import HitPoint


class Raycast:
    """A single raycast: start/end positions and hit info."""

    def __init__(
        self,
        start_pos: Vector2,
        end_pos: Vector2,
        hit_info: HitPoint,
    ):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.hit_info = hit_info
