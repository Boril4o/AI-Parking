import math
from typing import Optional
import pygame
from pygame import Rect, Vector2
import numpy as np
from environment.colors import Colors
from environment.hit_point import HitPoint
from environment.raycast import Raycast
from environment.scale import meters_to_pixels
import gymnasium as gym

class ParkingWarehouse(gym.Env):
    """
    A simple 2D parking-lot environment for a single car.

    The car moves in continuous space inside a rectangular playground with walls
    and parking spots on the top and bottom sides. Some spots contain parked
    cars (obstacles), and one empty spot is chosen as the parking target.
    The agent controls steering and gas (forward / reverse) and receives
    observations based on distance to the target, car orientation and
    raycast distances to surrounding obstacles.
    """
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
    max_step = 1000

    step_penalty = -0.01
    collision_penalty = -10
    parked_reward = 10
    closer_to_park_spot_reward = 0.10

    def __init__(self):
        """Initialize pygame, convert all geometry from meters to pixels,
        and pre-compute static structures like walls and parking spots."""

        self.observation_space = gym.spaces.Dict({
            "distance": gym.spaces.Box(0, 1, shape=(1,), dtype=np.float32),
            "car_angle": gym.spaces.Box(0, 1, shape=(1,), dtype=np.float32),
            "velocity": gym.spaces.Box(-1, 1, shape=(1,), dtype=np.float32),
            "angular_velocity": gym.spaces.Box(-1, 1, shape=(1,), dtype=np.float32),
            "raycasts": gym.spaces.Box(0, 1, shape=(8,), dtype=np.float32),
            })
        self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)

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

        distance_car_spot_horizontal_width = self.playground_width_pixels - (self.parking_spot_width_pixels + self.car_width_pixels) / 2
        distance_car_spot_horizontal_height = self.playground_height_pixels - (self.parking_spot_height_pixels + self.car_height_pixels) / 2
        max_distance_car_spot_horizontal = np.hypot(distance_car_spot_horizontal_width, distance_car_spot_horizontal_height)

        distance_car_spot_vertical_width = self.playground_width_pixels - (self.parking_spot_width_pixels + self.car_height_pixels) / 2
        distance_car_spot_vertical_height = self.playground_height_pixels - (self.parking_spot_height_pixels + self.car_width_pixels) / 2
        max_distance_car_spot_vertical = np.hypot(distance_car_spot_vertical_width, distance_car_spot_vertical_height)

        self.max_distance_car_spot = np.maximum(max_distance_car_spot_horizontal, max_distance_car_spot_vertical)

        self.top_wall = pygame.Rect(0, 0, self.playground_width_pixels, self.wall_width_pixels)
        self.bottom_wall = pygame.Rect(0, self.playground_height_pixels - self.wall_width_pixels, self.playground_width_pixels, self.wall_width_pixels)

        self.left_wall = pygame.Rect(0, 0, self.wall_width_pixels, self.playground_height_pixels)
        self.right_wall = pygame.Rect(self.playground_width_pixels - self.wall_width_pixels, 0, self.wall_width_pixels, self.playground_height_pixels)

        self.static_BG = pygame.Surface((self.playground_width_pixels, self.playground_height_pixels))
        self.obstacles_surf = pygame.Surface((self.playground_width_pixels, self.playground_height_pixels), pygame.SRCALPHA)

        self.parking_spots: list[Rect] = []

        self.obstacles = [self.top_wall, self.bottom_wall, self.left_wall, self.right_wall]

        # Top-row parking spots
        for i in range(self.parking_spot_count_on_side):
            x_position = (self.parking_spot_width_pixels * i) + self.wall_width_pixels
            y_position = self.wall_width_pixels
            
            parking_spot = pygame.Rect(x_position, y_position, self.parking_spot_width_pixels, self.parking_spot_height_pixels)

            self.parking_spots.append(parking_spot)

        # Bottom-row parking spots
        for i in range(self.parking_spot_count_on_side):
            x_position = (self.parking_spot_width_pixels * i) + self.wall_width_pixels
            y_position = self.playground_height_pixels - self.parking_spot_height_pixels - self.wall_width_pixels
            
            parking_spot = pygame.Rect(x_position, y_position, self.parking_spot_width_pixels, self.parking_spot_height_pixels)
            self.parking_spots.append(parking_spot)

    def reset(self, seed: Optional[int] = None, options: Optional[dict] = None):
        """Reset the environment state and randomly choose a free parking spot."""
        super().reset(seed=seed)

        self.velocity = 0
        self.angular_velocity = 0
        self.car_angle = 0
        self.car_pos = self.car_default_center_pixels
        self.closest_to_park_spot = 1

        self.original_car_surf = pygame.Surface((self.car_width_pixels, self.car_height_pixels), pygame.SRCALPHA)
        self.original_car_surf.fill(Colors.CAR)
        self.original_car_rect = self.original_car_surf.get_rect(center=self.car_pos)

        self.static_BG.fill(Colors.BACKGROUND)

        self.current_step = 0

        # Randomly mark some parking spots as occupied by parked cars
        parked_cars = []
        empty_parking_spots: list[Rect] = []
        for parking_spot in self.parking_spots:
            pygame.draw.rect(self.static_BG, Colors.PARKING_SPOT, parking_spot, width=4)

            if len(parked_cars) < self.parked_cars_count and self.np_random.uniform(0.0, 1.0) < 0.5:
                parked_car = pygame.Rect(0, 0, self.car_height_pixels, self.car_width_pixels)
                parked_car.center = parking_spot.center
                pygame.draw.rect(self.static_BG, Colors.PARKED_CAR, parked_car)
                parked_cars.append(parked_car)
            else:
                empty_parking_spots.append(parking_spot)

        # Any parked car becomes an obstacle for collision checking
        self.obstacles = self.obstacles[:4]
        self.obstacles.extend(parked_cars)

        # Choose one of the free spots as the target parking location
        self.target_parking_spot = empty_parking_spots[self.np_random.integers(0, len(empty_parking_spots))]

        self.obstacles_surf.fill((0, 0, 0, 0))

        pygame.draw.rect(self.static_BG, Colors.WALL, self.top_wall)
        pygame.draw.rect(self.static_BG, Colors.WALL, self.bottom_wall)
        pygame.draw.rect(self.static_BG, Colors.WALL, self.left_wall)
        pygame.draw.rect(self.static_BG, Colors.WALL, self.right_wall)

        # Obstacles surface is used only to build a collision mask
        pygame.draw.rect(self.obstacles_surf, Colors.WALL, self.top_wall)
        pygame.draw.rect(self.obstacles_surf, Colors.WALL, self.bottom_wall)
        pygame.draw.rect(self.obstacles_surf, Colors.WALL, self.left_wall)
        pygame.draw.rect(self.obstacles_surf, Colors.WALL, self.right_wall)
        for parked_car in parked_cars:
            pygame.draw.rect(self.obstacles_surf, Colors.PARKED_CAR, parked_car)

        # Pre-computed masks used for pixel-perfect collision detection
        self.obstacles_mask = pygame.mask.from_surface(self.obstacles_surf)
        self.car_mask = pygame.mask.from_surface(self.original_car_surf)

        return self.get_obs, {}

    def render(self):
        """Draw the current frame: static background, car and raycasts."""
        if not self.screen:
            self.screen = pygame.display.set_mode((self.playground_width_pixels, self.playground_height_pixels))

        self.screen.blit(self.static_BG, (0, 0))

        self.screen.blit(self.rotated_car_surf, self.rotated_car_rect)

        # Compute current raycasts relative to car position and orientation
        raycasts = self.get_raycast()

        for raycast in raycasts:
            if raycast.hit_info.point:
                pygame.draw.line(self.screen, Colors.WALL, raycast.start_pos, raycast.hit_info.point, width=2)
            else:
                pygame.draw.line(self.screen, Colors.WALL, raycast.start_pos, raycast.end_pos)

        # Keep the window responsive and update the display at ~60 FPS
        pygame.event.pump()
        pygame.display.flip()
        self.clock.tick(60)

    def get_raycast(self):
        """Cast rays from the corners and side midpoints of the car.

        Each ray starts at a car-relative point and is projected outward in the
        direction of that point (relative to the center). The distances are
        later used as part of the observation for obstacle awareness.
        """
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

        # Rays are cast from both corners and side midpoints
        offsets = corners_offsets + sides_offsets

        rays: list[tuple[Vector2, Vector2, Vector2]] = []

        for offset in offsets:
            # Rotate the offset by the negative car angle so that the local
            # car geometry follows the car orientation in world space
            rotated_offset = offset.rotate(-self.car_angle)
            corner_pos = self.original_car_rect.center + rotated_offset 

            # Ray direction is simply the normalized offset vector
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
        """Return the closest intersection (if any) of a ray with all obstacles."""
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


        # Normalize distance to [0, 1]; 1.0 means no hit within ray length
        distance: float = np.clip(min_dist / self.raycast_length, 0.0, 1.0)

        return HitPoint(point=closest_hit, distance=distance)

    def get_obs(self):
        """Build the observation dictionary used by the agent."""
        raycasts: list[float] = [raycast.hit_info.distance for raycast in self.get_raycast()]
        car_angular_velocity = self.angular_velocity
        car_velocity = self.velocity
        angle = self.car_angle / 360
        # Distance from car center to the target parking spot center, normalized
        distance_between = Vector2(self.car_pos).distance_to(Vector2(self.target_parking_spot.center)) / self.max_distance_car_spot

        #print(f"angular_velocity: {car_angular_velocity}")
        #print(f"velocity: {car_velocity}")
        #print(f"angle: {angle}")
        #print(f"distance: {distance_between}")
        #print(f"raycasts: {raycasts}")
        #print("-------------------------------------------")

        return {
            # raycasts: values from 0.0 (very close obstacle) to 1.0 (no hit)
            # car_angle: current car angle normalized to [0, 1]
            # velocity: signed forward/backward speed command ([-1, 1])
            # angular_velocity: normalized steering command after processing
            "distance": distance_between,
            "car_angle": angle,
            "velocity": car_velocity,
            "angular_velocity": car_angular_velocity,
            "raycasts": raycasts
        }

    def step(self, action):
        """Advance the simulation by one time step given (steer, gas) actions."""
        # Both actions are expected to be in [-1, 1]
        steer_action, gas_action = action

        steer_action = np.clip(steer_action, -1.0, 1.0)
        gas_action = np.clip(gas_action, -1.0, 1.0)

        self.current_step += 1

        # Turning rate grows with steering and gas, capped by turn_speed.
        # Negative values mean turning in the opposite direction.
        self.angular_velocity = np.clip(steer_action * -gas_action * self.turn_speed, -self.turn_speed, self.turn_speed)

        # Integrate angular velocity into the car's orientation (degrees)
        self.car_angle += self.angular_velocity * self.dt
        self.car_angle = self.car_angle % 360

        # Keep a normalized angular velocity in [-1, 1] for observations
        self.angular_velocity /= self.turn_speed

        # Convert car orientation to radians to compute velocity components
        rad = math.radians(self.car_angle)

        velocity_x = math.cos(rad) * gas_action * self.car_speed
        velocity_y = -math.sin(rad) * gas_action * self.car_speed

        x, y = self.car_pos

        x_new = x + velocity_x * self.dt
        y_new = y + velocity_y * self.dt

        # Update car position and rect center
        self.car_pos = (x_new, y_new)
        self.original_car_rect.center = self.car_pos

        # Store signed, normalized speed (-1 reverse, +1 forward)
        self.velocity = gas_action

        # Rotate the car surface to match current orientation for rendering
        self.rotated_car_surf = pygame.transform.rotate(self.original_car_surf, self.car_angle)
        self.rotated_car_rect = self.rotated_car_surf.get_rect(center=self.original_car_rect.center)

        # Update mask to match rotated car for collision checks
        self.car_mask = pygame.mask.from_surface(self.rotated_car_surf)

        reward = 0
        terminated = False
        observation = self.get_obs()
        truncated = False

        parking_info = self.check_parking_spot(observation["distance"])

        if self.check_collison():
            reward += self.collision_penalty
            terminated = True

        if observation["distance"] < self.closest_to_park_spot:
            self.closer_to_park_spot = observation["distance"]
            reward += self.closer_to_park_spot_reward

        if parking_info[0]:
            reward += self.parked_reward
            terminated = True

        if self.current_step >= self.max_step:
            truncated = True

        reward += self.step_penalty
        
        info = {}

        return observation, reward, terminated, truncated, info

    def check_collison(self):
        """Return True if the car collides with any obstacle."""
        offset_x = -self.rotated_car_rect.x
        offset_y = -self.rotated_car_rect.y

        if self.car_mask.overlap(self.obstacles_mask, offset=(offset_x, offset_y)):
            return True
        return False

    def check_parking_spot(self, distance: float):
        """Check whether the car is fully inside the target spot and well aligned.

        Returns a tuple (is_inside, angle_score) where angle_score is in [0, 1]
        and rewards being parallel to the parked cars (i.e., aligned with spot).
        """

        result = (False, 0)

        if distance > 0.01:
            return result

        car_top_left_corner_offset = Vector2(-self.car_width_pixels / 2, -self.car_height_pixels / 2)
        car_bottom_right_corner_offset = Vector2(self.car_width_pixels / 2, self.car_height_pixels / 2)

        # Rotate car corners so we can compare them in world coordinates
        car_top_left_rotated_offset = car_top_left_corner_offset.rotate(-self.car_angle)
        car_bottom_right_rotated_offset = car_bottom_right_corner_offset.rotate(-self.car_angle)

        car_top_left_pos = self.original_car_rect.center + car_top_left_rotated_offset
        car_bottom_right_pos = self.original_car_rect.center + car_bottom_right_rotated_offset

        # Check that the car's bounding corners are inside the parking rectangle
        if (self.target_parking_spot.topleft[0] < car_top_left_pos.x < self.target_parking_spot.bottomright[0] 
            and self.target_parking_spot.topleft[1] < car_top_left_pos.y < self.target_parking_spot.bottomright[1]
            and self.target_parking_spot.topleft[0] < car_bottom_right_pos.x < self.target_parking_spot.bottomright[0] 
            and self.target_parking_spot.topleft[1] < car_bottom_right_pos.y < self.target_parking_spot.bottomright[1]):
            # angle_diff rewards car angles close to perpendicular relative to spot edges
            angle_diff = 1 - abs((self.car_angle % 180 - 90) / 90)

            if angle_diff > 0.95:
                result = (True, angle_diff)

            return result
        return result

# Simple manual-control loop for debugging the environment with keyboard.
# Use WASD keys:
# - A / D: steer left / right
# - W / S: drive forward / reverse
# Close the window or interrupt the process to stop.
# This block runs only when the module is executed directly.
# (In RL training, Gym would call reset/step instead.)
# NOTE: This is intentionally kept minimal and blocking.
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