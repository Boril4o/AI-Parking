import pygame
import random
from pygame import Rect, Vector2
import numpy as np
from environment.colors import Colors
from environment.hit_point import HitPoint
from environment.raycast import Raycast
from environment.scale import meters_to_pixels

class ParkingWarehouse:
    parking_spot_width = 4
    parking_spot_height = 6
    car_width, car_height = 4.46, 1.80
    wall_width = 1
    playground_width = parking_spot_width * 4 + wall_width * 2
    playground_height = (parking_spot_height * 2) + (wall_width * 2) + 5
    parking_spot_count_on_side = 4
    parked_cars_count = 4
    raycast_length = 50.0
    car_default_center = (playground_width / 2, playground_height / 2)

    def __init__(self):
        pygame.init()
        self.screen = None
        self.clock = pygame.time.Clock()

        self.parking_spot_width_pixels = meters_to_pixels(self.parking_spot_width)
        self.parking_spot_height_pixels = meters_to_pixels(self.parking_spot_height)
        self.car_width_pixels = meters_to_pixels(self.car_width)
        self.car_height_pixels = meters_to_pixels(self.car_height)
        self.wall_width_pixels = meters_to_pixels(self.wall_width)
        self.playground_width_pixels = meters_to_pixels(self.playground_width)
        self.playground_height_pixels = meters_to_pixels(self.playground_height)
        self.car_default_center_pixels = (meters_to_pixels(self.car_default_center[0]), meters_to_pixels(self.car_default_center[1]))

        self.velocity = 0
        self.car_angle = 0
        self.car_pos = ()

        top_wall = pygame.Rect(0, 0, self.playground_width_pixels, self.wall_width_pixels)
        bottom_wall = pygame.Rect(0, self.playground_height_pixels - self.wall_width_pixels, self.playground_width_pixels, self.wall_width_pixels)

        left_wall = pygame.Rect(0, 0, self.wall_width_pixels, self.playground_height_pixels)
        right_wall = pygame.Rect(self.playground_width_pixels - self.wall_width_pixels, 0, self.wall_width_pixels, self.playground_height_pixels)

        self.original_car_surf = pygame.Surface((self.car_width_pixels, self.car_height_pixels), pygame.SRCALPHA)
        self.original_car_surf.fill(Colors.CAR)
        self.original_car_rect = self.original_car_surf.get_rect(center=self.car_default_center_pixels)

        self.static_BG = pygame.Surface((self.playground_width_pixels, self.playground_height_pixels))
        self.static_BG.fill(Colors.BACKGROUND)

        self.parking_spots = []
        self.parked_cars = []
        empty_parking_spot_indexes = []

        for i in range(self.parking_spot_count_on_side):
            x_position = (self.parking_spot_width_pixels * i) + self.wall_width_pixels
            y_position = self.wall_width_pixels
            
            parking_spot = pygame.Rect(x_position, y_position, self.parking_spot_width_pixels, self.parking_spot_height_pixels)
            pygame.draw.rect(self.static_BG, Colors.PARKING_SPOT, parking_spot, width=4)

            self.parking_spots.append(parking_spot)

            if len(self.parked_cars) < self.parked_cars_count and random.random() < 0.5:
                parked_car = pygame.Rect(0, 0, self.car_height_pixels, self.car_width_pixels)
                parked_car.center = (x_position + self.parking_spot_width_pixels / 2, y_position + self.parking_spot_height_pixels / 2)
                pygame.draw.rect(self.static_BG, Colors.PARKED_CAR, parked_car)
                self.parked_cars.append(parked_car)
            else:
                empty_parking_spot_indexes.append(i)

        for i in range(self.parking_spot_count_on_side):
            x_position = (self.parking_spot_width_pixels * i) + self.wall_width_pixels
            y_position = self.playground_height_pixels - self.parking_spot_height_pixels - self.wall_width_pixels
            
            parking_spot = pygame.Rect(x_position, y_position, self.parking_spot_width_pixels, self.parking_spot_height_pixels)
            pygame.draw.rect(self.static_BG, Colors.PARKING_SPOT, parking_spot, width=4)

            if len(self.parked_cars) < self.parked_cars_count and random.random() < 0.5:
                parked_car = pygame.Rect(0, 0, self.car_height_pixels, self.car_width_pixels)
                parked_car.center = (x_position + self.parking_spot_width_pixels / 2, y_position + self.parking_spot_height_pixels / 2)
                pygame.draw.rect(self.static_BG, Colors.PARKED_CAR, parked_car)
                self.parked_cars.append(parked_car)
            else:
                empty_parking_spot_indexes.append(i)

        self.target_parking_spot = self.parking_spots[empty_parking_spot_indexes[random.randint(0, len(empty_parking_spot_indexes) - 1)]]

        self.obstacles: list[Rect] = [top_wall, bottom_wall, left_wall, right_wall, *self.parked_cars]

        pygame.draw.rect(self.static_BG, Colors.WALL, top_wall)
        pygame.draw.rect(self.static_BG, Colors.WALL, bottom_wall)
        pygame.draw.rect(self.static_BG, Colors.WALL, left_wall)
        pygame.draw.rect(self.static_BG, Colors.WALL, right_wall)

    def render(self):
        if not self.screen:
            self.screen = pygame.display.set_mode((self.playground_width_pixels, self.playground_height_pixels))

        self.screen.blit(self.static_BG, (0, 0))

        rotated_car_surf = pygame.transform.rotate(self.original_car_surf, self.car_angle)
        rotated_car_rect = rotated_car_surf.get_rect(center=self.original_car_rect.center)
        self.screen.blit(rotated_car_surf, rotated_car_rect)

        raycasts = self.get_raycast()

        for raycast in raycasts:
            pygame.draw.line(self.screen, Colors.WALL, raycast.start_pos, raycast.end_pos)

        pygame.event.pump()
        pygame.display.flip()
        self.clock.tick(60)

    def get_raycast(self):
        corners_offsets = [
            Vector2(-self.car_width_pixels / 2, -self.car_height_pixels / 2),
            Vector2(-self.car_width_pixels / 2, self.car_height_pixels / 2),
            Vector2(self.car_width_pixels / 2, -self.car_height_pixels / 2),
            Vector2(self.car_width_pixels / 2, self.car_height_pixels / 2),
        ]

        sides_offsets = [
            Vector2(-self.car_width_pixels / 2, 0),
            Vector2(0, -self.car_height_pixels / 2),
            Vector2(self.car_width_pixels / 2, 0),
            Vector2(0, self.car_height_pixels / 2)
        ]

        offsets = corners_offsets + sides_offsets

        rays: list[tuple[Vector2, Vector2, Vector2]] = []

        for offset in offsets:
            rotated_offset = offset.rotate(-self.car_angle)
            corner_pos = self.original_car_rect.center + rotated_offset 

            ray_direction = rotated_offset.normalize()

            start_pos = corner_pos
            end_pos = start_pos + (ray_direction * self.raycast_length)

            rays.append((start_pos, end_pos))

        # info for raycast [(start_pos, end_post, ((hit_point), distance))]
        #return [(raycast[0], raycast[1], self.check_raycast(raycast)) for raycast in rays]
        return [
            Raycast(start_pos=raycast[0], end_pos=raycast[1], hit_info=self.check_raycast(raycast))
            for raycast in rays
        ]

    def check_raycast(self, raycast: tuple[Vector2, Vector2]):
        closest_hit = None
        min_dist = float("inf")

        raycast_start, raycast_end = raycast

        for obstacle in self.obstacles:
            hit_points = obstacle.clipline(raycast_start, raycast_end)

            if hit_points:
                start_p, end_p = hit_points
                dist = Vector2(raycast_start).distance_to(start_p)

                if dist < min_dist:
                    min_dist = dist
                    closest_hit = start_p


        distance: float = np.clip(min_dist / self.raycast_length, 0.0, 1.0)

        return HitPoint(point=closest_hit, distance=distance)

    def get_obs(self):
        raycasts: list[float] = [raycast.hit_info.distance for raycast in self.get_raycast()]

        return {
            # raycasts: value from 0.0 to 1.0; 1.0 is for clear, 0.0 for touching object
            # car pos: current pos of the car; (x, y) value
            # park pos: park spot position
            # car angle
            # velocity: current car velocity

            "car_pos": self.car_pos,
            "target_parking_spot_pos": self.target_parking_spot.center,
            "car_angle": self.car_angle,
            "velocity": self.velocity,
            "raycasts": raycasts
        }


a = ParkingWarehouse()

while True:
    a.render()