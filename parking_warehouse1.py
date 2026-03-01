import math
from typing import Optional
import pygame
import random
from pygame import Rect, Vector2
import numpy as np
from environment.colors import Colors
from environment.hit_point import HitPoint
from environment.raycast import Raycast
from environment.scale import meters_to_pixels
import gymnasium as gym

class ParkingWarehouse(gym.Env):
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
    turn_speed = 50.0
    car_speed = 50.0
    dt = 1 / 60

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

        self.top_wall = pygame.Rect(0, 0, self.playground_width_pixels, self.wall_width_pixels)
        self.bottom_wall = pygame.Rect(0, self.playground_height_pixels - self.wall_width_pixels, self.playground_width_pixels, self.wall_width_pixels)

        self.left_wall = pygame.Rect(0, 0, self.wall_width_pixels, self.playground_height_pixels)
        self.right_wall = pygame.Rect(self.playground_width_pixels - self.wall_width_pixels, 0, self.wall_width_pixels, self.playground_height_pixels)

        self.static_BG = pygame.Surface((self.playground_width_pixels, self.playground_height_pixels))
        self.obstacles_surf = pygame.Surface((self.playground_width_pixels, self.playground_height_pixels), pygame.SRCALPHA)

        self.parking_spots: list[Rect] = []

        self.obstacles = [self.top_wall, self.bottom_wall, self.left_wall, self.right_wall]

        for i in range(self.parking_spot_count_on_side):
            x_position = (self.parking_spot_width_pixels * i) + self.wall_width_pixels
            y_position = self.wall_width_pixels
            
            parking_spot = pygame.Rect(x_position, y_position, self.parking_spot_width_pixels, self.parking_spot_height_pixels)

            self.parking_spots.append(parking_spot)

        for i in range(self.parking_spot_count_on_side):
            x_position = (self.parking_spot_width_pixels * i) + self.wall_width_pixels
            y_position = self.playground_height_pixels - self.parking_spot_height_pixels - self.wall_width_pixels
            
            parking_spot = pygame.Rect(x_position, y_position, self.parking_spot_width_pixels, self.parking_spot_height_pixels)
            self.parking_spots.append(parking_spot)

    def reset(self, seed: Optional[int] = None, options: Optional[dict] = None):
        super().reset(seed=seed)

        self.velocity = 0
        self.angular_velocity = 0
        self.car_angle = 0
        self.car_pos = self.car_default_center_pixels

        self.original_car_surf = pygame.Surface((self.car_width_pixels, self.car_height_pixels), pygame.SRCALPHA)
        self.original_car_surf.fill(Colors.CAR)
        self.original_car_rect = self.original_car_surf.get_rect(center=self.car_pos)

        self.static_BG.fill(Colors.BACKGROUND)

        parked_cars = []
        empty_parking_spots = []
        for parking_spot in self.parking_spots:
            pygame.draw.rect(self.static_BG, Colors.PARKING_SPOT, parking_spot, width=4)

            if len(parked_cars) < self.parked_cars_count and self.np_random.uniform(0.0, 1.0) < 0.5:
                parked_car = pygame.Rect(0, 0, self.car_height_pixels, self.car_width_pixels)
                parked_car.center = parking_spot.center
                pygame.draw.rect(self.static_BG, Colors.PARKED_CAR, parked_car)
                parked_cars.append(parked_car)
            else:
                empty_parking_spots.append(parking_spot)

        self.obstacles.extend(parked_cars)

        self.target_parking_spot = empty_parking_spots[self.np_random.integers(0, len(empty_parking_spots)) - 1]

        self.obstacles_surf.fill((0, 0, 0, 0))

        pygame.draw.rect(self.static_BG, Colors.WALL, self.top_wall)
        pygame.draw.rect(self.static_BG, Colors.WALL, self.bottom_wall)
        pygame.draw.rect(self.static_BG, Colors.WALL, self.left_wall)
        pygame.draw.rect(self.static_BG, Colors.WALL, self.right_wall)

        pygame.draw.rect(self.obstacles_surf, Colors.WALL, self.top_wall)
        pygame.draw.rect(self.obstacles_surf, Colors.WALL, self.bottom_wall)
        pygame.draw.rect(self.obstacles_surf, Colors.WALL, self.left_wall)
        pygame.draw.rect(self.obstacles_surf, Colors.WALL, self.right_wall)
        for parked_car in parked_cars:
            pygame.draw.rect(self.obstacles_surf, Colors.PARKED_CAR, parked_car)

        self.obstacles_mask = pygame.mask.from_surface(self.obstacles_surf)
        self.car_mask = pygame.mask.from_surface(self.original_car_surf)

    def render(self):
        if not self.screen:
            self.screen = pygame.display.set_mode((self.playground_width_pixels, self.playground_height_pixels))

        self.screen.blit(self.static_BG, (0, 0))

        self.screen.blit(self.rotated_car_surf, self.rotated_car_rect)

        raycasts = self.get_raycast()

        for raycast in raycasts:
            if raycast.hit_info.point:
                pygame.draw.line(self.screen, Colors.WALL, raycast.start_pos, raycast.hit_info.point, width=2)
            else:
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
            # car angle: current car angle in degrees
            # velocity: current car velocity
            # angular_velocity: current car angular velocity in degrees per second

            "car_pos": self.car_pos,
            "target_parking_spot_pos": self.target_parking_spot.center,
            "car_angle": self.car_angle,
            "velocity": self.velocity,
            "angular_velocity": self.angular_velocity,
            "raycasts": raycasts
        }

    def step(self, action):
        #both actions can be between -1 and 1
        steer_action, gas_action = action

        steer_action = np.clip(steer_action, -1.0, 1.0)
        gas_action = np.clip(gas_action, -1.0, 1.0)

        self.angular_velocity = steer_action * -gas_action * self.turn_speed

        self.car_angle += self.angular_velocity * self.dt #car angle in degrees

        rad = math.radians(self.car_angle) #car angle in radians

        velocity_x = math.cos(rad) * gas_action * self.car_speed
        velocity_y = -math.sin(rad) * gas_action * self.car_speed

        x, y = self.car_pos

        x_new = x + velocity_x * self.dt
        y_new = y + velocity_y * self.dt

        self.car_pos = (x_new, y_new)
        self.original_car_rect.center = self.car_pos
        self.velocity = math.sqrt(velocity_x**2 + velocity_y**2)

        self.rotated_car_surf = pygame.transform.rotate(self.original_car_surf, self.car_angle)
        self.rotated_car_rect = self.rotated_car_surf.get_rect(center=self.original_car_rect.center)

        self.car_mask = pygame.mask.from_surface(self.rotated_car_surf) #update car mask

        observation = self.get_obs()
        reward = 0
        terminated = self.check_collison()
        truncated = False
        info = {}

        return observation, reward, terminated, truncated, info

    def check_collison(self):
        offset_x = -self.rotated_car_rect.x
        offset_y = -self.rotated_car_rect.y

        if self.car_mask.overlap(self.obstacles_mask, offset=(offset_x, offset_y)):
            return True
        return False

    def check_parking_spot(self):
        car_top_left_corner_offset = Vector2(-self.car_width_pixels / 2, -self.car_height_pixels / 2)
        car_bottom_right_corner_offset = Vector2(self.car_width_pixels / 2, self.car_height_pixels / 2)

        car_top_left_rotated_offset = car_top_left_corner_offset.rotate(-self.car_angle)
        car_bottom_right_rotated_offset = car_bottom_right_corner_offset.rotate(-self.car_angle)

        car_top_left_pos = self.original_car_rect.center + car_top_left_rotated_offset
        car_bottom_right_pos = self.original_car_rect.center + car_bottom_right_rotated_offset

        if (self.target_parking_spot.top_left_pos.x < car_top_left_pos.x < self.target_parking_spot.bottom_right_pos.x 
            and self.target_parking_spot.top_left_pos.y < car_top_left_pos.y < self.target_parking_spot.bottom_right_pos.y
            and self.target_parking_spot.top_left_pos.x < car_bottom_right_pos.x < self.target_parking_spot.bottom_right_pos.x 
            and self.target_parking_spot.top_left_pos.y < car_bottom_right_pos.y < self.target_parking_spot.bottom_right_pos.y):
            return True
        return False

a = ParkingWarehouse()
a.reset()

while True:
    keys = pygame.key.get_pressed()

    steer_action, gas_action = 0, 0

    if keys[pygame.K_a]:
        steer_action = -1
    elif keys[pygame.K_d]:
        steer_action = 1
    
    if keys[pygame.K_w]:
        gas_action = 1
    elif keys[pygame.K_s]:
        gas_action = -1

    observation, reward, terminated, truncated, info = a.step([steer_action, gas_action])

    if terminated or truncated:
        a.reset()

    a.render()