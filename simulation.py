import pygame
import math

# --- Configuration & Initialization ---
pygame.init()

# Dimensions and Frame Rate
WIDTH, HEIGHT = 1000, 700
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (50, 200, 50)     # Open desk
RED = (200, 50, 50)       # Closed desk
BLUE = (50, 100, 200)     # Passenger agent
GRAY = (200, 200, 200)    # Escalator area
DARK_GRAY = (50, 50, 50)  # Entrance area

# Simulation Logistics
NUM_DESKS = 20
OPEN_DESKS = 10
SPAWN_RATE = 30           # Frames between new passenger spawns
CHECK_IN_TIME = 90        # Frames spent actively processing at the desk
PASSENGER_SPEED = 2.5
PASSENGER_RADIUS = 5
QUEUE_SPACING = 15        # Distance between passengers in line

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Terminal Check-In Flow Simulation")
clock = pygame.time.Clock()

# --- Classes ---
class Desk:
    def __init__(self, index, x, y):
        self.index = index
        self.x = x
        self.y = y
        self.width = 30
        self.height = 20
        # First 10 desks are open, the rest are closed
        self.is_open = index < OPEN_DESKS
        self.queue = [] 

    def draw(self, surface):
        color = GREEN if self.is_open else RED
        pygame.draw.rect(surface, color, 
                         (self.x - self.width//2, self.y - self.height//2, self.width, self.height))

class Passenger:
    def __init__(self, start_x, start_y):
        self.x = start_x
        self.y = start_y
        self.target_desk = None
        self.state = "APPROACHING" # States: APPROACHING, CHECKING_IN, DETOURING, EXITING
        self.check_in_timer = 0
        self.waypoints = []

    def assign_desk(self, desks):
        # Evaluate shortest queue among active servers
        open_desks = [d for d in desks if d.is_open]
        self.target_desk = min(open_desks, key=lambda d: len(d.queue))
        self.target_desk.queue.append(self)

    def update(self):
        if self.state == "APPROACHING":
            try:
                # Calculate dynamic position in line to prevent agent stacking
                queue_index = self.target_desk.queue.index(self)
                target_x = self.target_desk.x
                # Offset y by queue position
                target_y = self.target_desk.y + 25 + (queue_index * QUEUE_SPACING)

                self._move_towards(target_x, target_y)

                # If at the front of the queue and reached the desk
                if queue_index == 0 and self.x == target_x and self.y == target_y:
                    self.state = "CHECKING_IN"

            except ValueError:
                pass # Triggered if unexpectedly removed from queue

        elif self.state == "CHECKING_IN":
            self.check_in_timer += 1
            if self.check_in_timer >= CHECK_IN_TIME:
                # Processing complete, remove from queue
                self.target_desk.queue.pop(0) 
                self.state = "DETOURING"
                # Set spatial waypoints to route around the physical desk
                self.waypoints = [
                    (self.target_desk.x + 25, self.target_desk.y), # Step to the right
                    (self.target_desk.x + 25, 100)                 # Walk up to escalator line
                ]

        elif self.state == "DETOURING":
            if self.waypoints:
                tx, ty = self.waypoints[0]
                if self._move_towards(tx, ty):
                    self.waypoints.pop(0) # Waypoint reached
            else:
                self.state = "EXITING"

        elif self.state == "EXITING":
            # Proceed directly up onto the escalator
            self.y -= PASSENGER_SPEED

    def _move_towards(self, tx, ty):
        """Moves agent towards target. Returns True if arrived."""
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        if dist > PASSENGER_SPEED:
            self.x += (dx / dist) * PASSENGER_SPEED
            self.y += (dy / dist) * PASSENGER_SPEED
            return False
        else:
            self.x, self.y = tx, ty
            return True

    def draw(self, surface):
        pygame.draw.circle(surface, BLUE, (int(self.x), int(self.y)), PASSENGER_RADIUS)


# --- Main Loop ---
def main():
    # Initialize infrastructure
    desks = []
    start_x = 45
    spacing = 48
    for i in range(NUM_DESKS):
        desks.append(Desk(i, start_x + i * spacing, HEIGHT // 2))

    passengers = []
    frame_count = 0
    font = pygame.font.SysFont(None, 32)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 1. Agent Spawner Logic
        frame_count += 1
        if frame_count % SPAWN_RATE == 0:
            p = Passenger(WIDTH // 2, HEIGHT - 20)
            p.assign_desk(desks)
            passengers.append(p)

        # 2. State Updates
        for p in passengers:
            p.update()
            
        # Clean up memory: Despawn agents that have ridden the escalator off-screen
        passengers = [p for p in passengers if p.y > 0]

        # 3. Rendering
        screen.fill(WHITE)
        
        # Draw Escalator (Exit Zone)
        pygame.draw.rect(screen, GRAY, (0, 0, WIDTH, 80))
        text = font.render("ESCALATOR TO SECURITY", True, BLACK)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, 30))

        # Draw Entrance (Spawn Zone)
        pygame.draw.rect(screen, DARK_GRAY, (WIDTH//2 - 60, HEIGHT - 30, 120, 30))
        
        for desk in desks:
            desk.draw(screen)

        for p in passengers:
            p.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
