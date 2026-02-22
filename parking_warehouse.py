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

        top_right = coords[0]
        bottom_right = coords[1]
        bottom_left = coords[2]
        top_left = coords[3]

        top_right_angle = math.radians(45)
        bottom_right_angle = math.radians(135)
        bottom_left_angle = math.radians(-135)
        top_left_angle = math.radians(-45)
        


    def get_obs(self):
        pass


a = ParkingWarehouse()