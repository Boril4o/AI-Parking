from shapely.geometry import Polygon, box
from shapely import affinity
from render import EnvironmenRenderer
import random
import math


class ParkingWarehouse:
    parking_spot_width = 4
    parking_spot_height = 6
    car_width, car_height = 4.46, 1.80
    wall_width = 1
    playground_width = parking_spot_width * 4 + wall_width * 2
    playground_height = (parking_spot_height * 2) + (wall_width * 2) + 5
    parking_spot_count_on_side = 4
    parked_cars_count = 4
    raycast_length = 1

    def __init__(self):
        self.walls = Polygon(
                        shell=[(0, 0), (self.playground_width, 0), (self.playground_width, self.playground_height), (0, self.playground_height)],
                        holes=[
                            [(self.wall_width, self.wall_width),
                            (self.playground_width - self.wall_width, self.wall_width),
                            (self.playground_width - self.wall_width, self.playground_height - self.wall_width),
                            (self.wall_width, self.playground_height - self.wall_width)]]
                    )

        car_template = box(-self.car_width/2, -self.car_height/2, self.car_width/2, self.car_height/2)
        self.car = affinity.translate(car_template, self.playground_width/2, self.playground_height/2)

        self.parking_spots = []
        self.parked_cars = []

        parking_spot_template = box(-self.parking_spot_width/2, -self.parking_spot_height/2, self.parking_spot_width/2, self.parking_spot_height/2)

        for i in range(self.parking_spot_count_on_side):
            start_x = (self.parking_spot_width / 2) + self.wall_width
            stride_x = i * self.parking_spot_width
            final_x = start_x + stride_x

            final_y = self.parking_spot_height / 2 + self.wall_width
    
            parking_spot = affinity.translate(parking_spot_template, final_x, final_y)
            self.parking_spots.append(parking_spot)

            if len(self.parked_cars) < self.parked_cars_count and random.random() < 0.5:  # Randomly decide to park a car
                rotated_car = affinity.rotate(car_template, 90)  # Rotate car to fit parking spot
                parked_car = affinity.translate(rotated_car, final_x, final_y)
                self.parked_cars.append(parked_car)


        for i in range(self.parking_spot_count_on_side):
            start_x = (self.parking_spot_width / 2) + self.wall_width
            stride_x = i * self.parking_spot_width
            final_x = start_x + stride_x

            final_y = self.playground_height - (self.parking_spot_height / 2 + self.wall_width)
    
            parking_spot = affinity.translate(parking_spot_template, final_x, final_y)
            self.parking_spots.append(parking_spot)

            if len(self.parked_cars) < self.parked_cars_count and random.random() < 0.5:  # Randomly decide to park a car
                rotated_car = affinity.rotate(car_template, 90)  # Rotate car to fit parking spot
                parked_car = affinity.translate(rotated_car, final_x, final_y)
                self.parked_cars.append(parked_car)


    def get_car_raycast(self):
        coords = list(self.car.exterior.coords[:-1])  # Exclude the closing point
        n = len(coords)

        lines = []

        for index in range(n):
            p_prev = coords[(index - 1) % n]
            p_curr = coords[index]
            p_next = coords[(index + 1) % n]

            in_dx = p_curr[0] - p_prev[0]
            in_dy = p_curr[1] - p_prev[1]
    
            out_dx = p_next[0] - p_curr[0]
            out_dy = p_next[1] - p_curr[1]

            n1_x, n1_y = in_dy, -in_dx
            n2_x, n2_y = out_dy, -out_dx

            len_n1 = math.hypot(n1_x, n1_y)
            len_n2 = math.hypot(n2_x, n2_y)

            if len_n1 > 0:
                n1_x /= len_n1
                n1_y /= len_n1
            if len_n2 > 0:
                n2_x /= len_n2
                n2_y /= len_n2

            nv_x = n1_x + n2_x
            nv_y = n1_y + n2_y

            angle_radians = math.atan2(nv_y, nv_x)

            new_x = p_curr[0] + self.raycast_length * math.cos(angle_radians)
            new_y = p_curr[1] + self.raycast_length * math.sin(angle_radians)

            line = [(p_curr[0], p_curr[1]), (new_x, new_y)]
            lines.append(line)

        return lines


    def get_obs(self):
        pass


a = ParkingWarehouse()