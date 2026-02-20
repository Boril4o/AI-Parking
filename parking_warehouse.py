from shapely.geometry import Polygon, box
from shapely import affinity
from render import EnvironmenRenderer

parking_spot_width = 4
parking_spot_height = 6
car_width, car_height = 4.46, 1.80
wall_width = 1
playground_width = parking_spot_width * 4 + wall_width * 2
playground_height = (parking_spot_height * 2) + (wall_width * 2) + 5

walls = Polygon(
    shell=[(0, 0), (playground_width, 0), (playground_width, playground_height), (0, playground_height)],
    holes=[
        [(wall_width, wall_width),
        (playground_width - wall_width, wall_width),
        (playground_width - wall_width, playground_height - wall_width),
        (wall_width, playground_height - wall_width)]]
)

car_template = box(-car_width/2, -car_height/2, car_width/2, car_height/2)
car = affinity.translate(car_template, playground_width/2, playground_height/2)

parking_spots = []

for i in range(4):
    parking_spot = box(-parking_spot_width/2, -parking_spot_height/2, parking_spot_width/2, parking_spot_height/2)
    
    start_x = (parking_spot_width / 2) + wall_width
    stride_x = i * parking_spot_width
    final_x = start_x + stride_x
    
    parking_spot = affinity.translate(parking_spot, final_x, parking_spot_height / 2 + wall_width)
    parking_spots.append(parking_spot)

for i in range(4):
    parking_spot = box(-parking_spot_width/2, -parking_spot_height/2, parking_spot_width/2, parking_spot_height/2)
    
    start_x = (parking_spot_width / 2) + wall_width
    stride_x = i * parking_spot_width
    final_x = start_x + stride_x
    
    parking_spot = affinity.translate(parking_spot, final_x, playground_height - (parking_spot_height / 2 + wall_width))
    parking_spots.append(parking_spot)

# Pygame rendering
if __name__ == "__main__":
    renderer = EnvironmenRenderer(playground_width, playground_height)
    
    while True:
        renderer.render(walls, car, parking_spots)