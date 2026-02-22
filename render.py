import pygame

scale = 25  # 1 meter = 50 pixels

def meters_to_pixels(meters):
    return int(meters * scale)

class Colors:
    WALL = (100, 100, 100)
    CAR = (255, 0, 0)
    PARKING_SPOT = (200, 200, 255)
    HOLE = (0, 0, 0)
    PARKED_CAR = (0, 0, 255)

class EnvironmenRenderer:
    def __init__(self, width, height):
        pygame.init()
        self.screen = pygame.display.set_mode((meters_to_pixels(width), meters_to_pixels(height)))
        self.clock = pygame.time.Clock()

    def render(self, walls, car, parked_cars, parking_spots):
        self.screen.fill((255, 255, 255))
    
        self.draw_polygon(self.screen, walls, Colors.WALL)
        self.draw_polygon(self.screen, car, Colors.CAR)  # Red car
        for parked_car in parked_cars:
            self.draw_polygon(self.screen, parked_car, Colors.PARKED_CAR)  # Red parked cars

        for spot in parking_spots:
            self.draw_polygon(self.screen, spot, Colors.PARKING_SPOT, width=2)  # Light blue with outline

        pygame.event.pump()  # Process event queue
        pygame.display.flip()
        self.clock.tick(60)  # Limit to 60 FPS

        

    def shapely_to_pygame(self, shapely_obj):
        """Convert shapely geometry to pygame-drawable coordinates"""
        if shapely_obj.geom_type == 'Polygon':
            # Get exterior coordinates
            exterior = list(shapely_obj.exterior.coords)
            exterior_pixels = [(meters_to_pixels(x), meters_to_pixels(y)) for x, y in exterior]
        
            # Get interior coordinates (holes)
            interiors_pixels = []
            for interior in shapely_obj.interiors:
                interior_pixels = [(meters_to_pixels(x), meters_to_pixels(y)) for x, y in interior.coords]
                interiors_pixels.append(interior_pixels)
        
            return exterior_pixels, interiors_pixels
        return None, None

    def draw_polygon(self, surface, shapely_obj, color, width=0):
        """Draw a shapely polygon on pygame surface"""
        exterior, interiors = self.shapely_to_pygame(shapely_obj)
        if exterior:
            pygame.draw.polygon(surface, color, exterior, width)
            # Draw holes
            for hole in interiors:
                pygame.draw.polygon(surface, (0, 0, 0), hole, 0)  # Fill holes with black