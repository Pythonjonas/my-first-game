import win32api  # Windows API for system information
import pygame  # Game development library
import random  # Library for random choices

# Get the screen's FPS from the system display settings
def get_fps():
    settings = win32api.EnumDisplaySettings(win32api.EnumDisplayDevices().DeviceName, -1)
    return getattr(settings, 'DisplayFrequency')

# Get the screen's resolution
def get_resolution():
    return win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)

# System Information
FPS = get_fps()
SCREEN_SIZE = get_resolution()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LIGHT_GREY = (200, 200, 200)

# Load images for dino, bird, cactus, clouds, and restart button
DINO1 = pygame.image.load('Sprites/dino-1.png')
DINO2 = pygame.image.load('Sprites/dino-2.png')
CROUCH_DINO1 = pygame.image.load('Sprites/dino-ducking-1.png')
CROUCH_DINO2 = pygame.image.load('Sprites/dino-ducking-2.png')
BIRB1 = pygame.image.load('Sprites/flappy-bird-1.png')
BIRB2 = pygame.image.load('Sprites/flappy-bird-2.png')
CACTUS1 = pygame.image.load('Sprites/cactus-1.png')
CACTUS2 = pygame.image.load('Sprites/cactus-2.png')
CACTUS3 = pygame.image.load('Sprites/cactus-3.png')
CLOUD1 = pygame.image.load('Sprites/cloud-1.png')
CLOUD2 = pygame.image.load('Sprites/cloud-2.png')
RESTART = pygame.image.load('Sprites/restart_button.png')

# Game mechanics variables defining update rates for different elements
JUMP_FRAMES = FPS // 1.75
LEG_SWAP_FRAMES = FPS // 10
FLAP_FRAMES = FPS // 15
SCORE_FRAMES = FPS // 10
CACTUS_FRAMES_LOW = 50
CACTUS_FRAMES_HIGH = 200
FAR_CLOUD_FRAMES_LOW = 150
FAR_CLOUD_FRAMES_HIGH = 400
CLOSE_CLOUD_FRAMES_LOW = 150
CLOSE_CLOUD_FRAMES_HIGH = 300
BIRB_FRAMES_LOW = 100
BIRB_FRAMES_HIGH = 300

# Base coordinates for ground level and starting X position
BASE_X = SCREEN_SIZE[0] // 15
BASE_Y = 4 * SCREEN_SIZE[1] // 5

# Cactus appearance delay limits
CACTUS_DELAY_LOW = 10
CACTUS_DELAY_HIGH = 15

# Speed settings for difficulty increase
SPEED_LOWER_BOUND = 1000
SPEED_UPPER_BOUND = 2000

# Cactus class: handles creation, movement, and removal of cacti
class Cactus(pygame.sprite.Sprite):
    def __init__(self, dt):
        # Initialize cactus sprite with random appearance
        self.dt = dt
        self.image = random.choice((CACTUS1, CACTUS2, CACTUS3))
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_SIZE[0] - 1
        self.rect.y = BASE_Y - self.image.get_size()[1]
        self.mask = pygame.mask.from_surface(self.image)
        pygame.sprite.Sprite.__init__(self)

    def update(self):
        # Move cactus to the left based on FPS and dt (time factor)
        self.rect.x -= FPS // 10 * self.dt
        # Remove cactus if it moves off the screen
        if self.rect.x + self.image.get_size()[0] < 0:
            self.kill()

# FlappyBirb class: handles creation, animation, and movement of birds
class FlappyBirb(pygame.sprite.Sprite):
    def __init__(self, dt):
        # Initialize bird sprite with random height and alternating wing position
        self.dt = dt
        self.count = 0
        self.wing_orientation = 0
        self.image = BIRB1
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_SIZE[0] - 1
        self.rect.y = random.randint(SCREEN_SIZE[0] // 5, BASE_Y - SCREEN_SIZE[0] // 20) - self.image.get_size()[1]
        self.mask = pygame.mask.from_surface(self.image)
        pygame.sprite.Sprite.__init__(self)

    def update(self):
        # Control wing animation speed
        self.count = (self.count + 1) % FLAP_FRAMES
        if self.count == 0:
            self.wing_orientation = 1 - self.wing_orientation
            self.image = BIRB1 if self.wing_orientation == 0 else BIRB2
        # Move bird to the left
        self.rect.x -= FPS // 15 * self.dt
        # Remove bird if it moves off the screen
        if self.rect.x + self.image.get_size()[0] < 0:
            self.kill()

# Cloud class: handles creation, size, color, and speed of clouds
class Cloud(pygame.sprite.Sprite):
    def __init__(self, dt, far):
        # Initialize cloud with different appearance and speed based on distance (far or close)
        self.dt = dt
        self.far = far
        if self.far:
            self.image = random.choice((CLOUD1, CLOUD2))
            self.image = pygame.transform.scale(self.image, (75, 75))
            self.image.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_ADD)
            self.div_speed = random.randint(30, 60)
        else:
            self.image = random.choice((CLOUD1, CLOUD2))
            self.image = pygame.transform.scale(self.image, (150, 150))
            self.div_speed = random.randint(15, 25)

        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_SIZE[0] - 1
        if self.far:
            self.rect.y = random.randint(self.image.get_size()[1] + SCREEN_SIZE[0] // 15,
                                         self.image.get_size()[1] + SCREEN_SIZE[0] // 6) - self.image.get_size()[1]
        else:
            self.rect.y = random.randint(self.image.get_size()[1],
                                         self.image.get_size()[1] + SCREEN_SIZE[0] // 10) - self.image.get_size()[1]
        pygame.sprite.Sprite.__init__(self)

    def update(self):
        # Move cloud to the left with varying speed based on distance
        self.rect.x -= FPS // self.div_speed * self.dt
        if self.rect.x + self.image.get_size()[0] < 0:
            self.kill()

# DinoRunner: main class to manage the game's state, interactions, and visuals
class DinoRunner:
    def __init__(self):
        pygame.init()  # Initialize pygame
        self.font = pygame.font.SysFont('Comic Sans MS', 75)
        self.screen = pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN)
        self.clock_tick = pygame.time.Clock()

        # Game state variables
        self.score = 0
        self.score_counter = 0
        self.crouch_info = {'crouching': False}
        self.jump_info = {'jumping': False, 'count': JUMP_FRAMES}
        self.dt = 1
        self.cur_x = BASE_X
        self.cur_y = BASE_Y - DINO1.get_rect().size[1]
        self.current_image = DINO1
        self.leg_counter = 0
        self.leg_orientation = 0
        self.paused = self.lost = False

        # Groups to manage game entities
        self.cacti = pygame.sprite.OrderedUpdates()
        self.birbs = pygame.sprite.OrderedUpdates()
        self.far_clouds = pygame.sprite.OrderedUpdates()
        self.close_clouds = pygame.sprite.OrderedUpdates()

        while True:  # Game loop
            # Main game loop code here...
            pass  # Placeholder

    # Additional methods like jump, crouch, game_over, reset, etc.
    
# Run game
if __name__ == '__main__':
    DinoRunner()

