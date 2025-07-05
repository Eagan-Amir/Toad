import pygame
import pytmx

screen_width = 720
screen_height = 480
fps = 60
GRAVITY = 0.5
JUMP = -9
TILE_SIZE = 16
SCALE = 2
BASE_WIDTH = screen_width // SCALE
BASE_HEIGHT = screen_height // SCALE

game_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
screen = pygame.display.set_mode((screen_width, screen_height))

pygame.init()
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Toad")
clock = pygame.time.Clock()
screen.fill((50,50,50))

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()

        self.canbreak = False ######
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill ((255, 0, 0))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.pos = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0,0)
        self.onground = False

    def update(self, collision_objects):
        keys = pygame.key.get_pressed()
       
        self.velocity.x = (keys[pygame.K_d] - keys[pygame.K_a]) * 2.5
       
        self.velocity.y += GRAVITY
        if self.velocity.y > 10:
            self.velocity.y = 10

        if keys[pygame.K_SPACE] and self.onground:
            self.velocity.y = JUMP
            self.canbreak = True
        else:
            self.canbreak = False

        if keys[pygame.K_SPACE] and self.onground:
            self.velocity.y = JUMP

        self.pos.x += self.velocity.x
        self.rect.x = int(self.pos.x)
        self.check_collision(collision_objects,'horizontal')

        self.pos.y += self.velocity.y
        self.rect.y = int(self.pos.y)
        self.onground=False
        self.check_collision(collision_objects,'vertical')
    
    def check_collision(self, collision_objects, direction):
        for obj in collision_objects:
            if self.rect.colliderect(obj):
                print(f"[lup] {obj} {direction}")
                if direction == 'horizontal':
                    if self.velocity.x > 0:
                        self.rect.right = obj.left
                    elif self.velocity.x < 0:
                        self.rect.left = obj.right
                    self.pos.x = self.rect.x
                    self.velocity.x = 0
                elif direction == 'vertical':
                    if self.velocity.y > 0:
                        self.rect.bottom = obj.top
                        self.onground = True
                    elif self.velocity.y < 0:
                        self.rect.top = obj.bottom
                    self.pos.y = self.rect.y
                    self.velocity.y = 0

    def trybreakblocks(self, game):
        if self.velocity.y < 0:
            hitbox = pygame.Rect(self.rect.x, self.rect.y - 10, self.rect.width, 10)

            for tile in game.breakabletiles:
                if hitbox.colliderect(tile["rect"]) and not tile["is_animating"]:
                    print(f"pup ({tile['tile_x']}, {tile['tile_y']})")
                    tile ["is_animating"] = True
                    tile["animation_timer"] = 0
                    break

class Game:
    def __init__(self, map_file):
        self.tmxdata = pytmx.load_pygame(map_file, pixelalpha=True)
        self.map_width = self.tmxdata.width * self.tmxdata.tilewidth
        self.map_height = self.tmxdata.height * self.tmxdata.tileheight
        self.collision_objects = []
        self.breakabletiles = []

        self.loadbreakabletiles()
        self.load_collision_objects()

    def load_collision_objects(self):
        print(f"[bup]")
        self.collision_objects = []
        for obj in self.tmxdata.get_layer_by_name("Collision"):
            x = obj.x
            y = obj.y
            width = obj.width or 0
            height = obj.height or 0

            if width == 0 or height == 0:
                print(f"[dup] {x}, {y}")
                continue

            self.collision_objects.append(pygame.Rect(x, y, width, height))

    def get_spawn_point(self, name="player"):
        spawn_layer = self.tmxdata.get_layer_by_name("Spawn")
        for obj in spawn_layer:
            x = obj.x
            y = obj.y - obj.height

            return(x, y)
        return (0, 0)
    
    def render(self, surface, camera):
        current_time = pygame.time.get_ticks()
        breakable_positions = {(tile["tile_x"], tile["tile_y"]) for tile in self.breakabletiles}

        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    if gid == 0:
                        continue

                    if layer.name == "breakable" and (x, y) in breakable_positions:
                        continue

                    tile = self.tmxdata.get_tile_image_by_gid(gid)
                    surface.blit(tile, (
                        x * self.tmxdata.tilewidth - camera.x, 
                        y * self.tmxdata.tileheight - camera.y))

        for tile in self.breakabletiles:
            tile_image = self.tmxdata.get_tile_image_by_gid(tile["gid"])
            if tile_image:
                surface.blit(tile_image, 
                    (tile["rect"].x - camera.x, 
                    tile["rect"].y - camera.y))



        for rect in self.collision_objects:
            debug_rect = pygame.Rect(rect.x - camera.x, rect.y - camera.y, rect.width, rect.height)
            pygame.draw.rect(surface, (0,255,0), debug_rect, 1)

    def loadbreakabletiles(self):
        break_layer = self.tmxdata.get_layer_by_name("breakable")
        for x, y, gid in break_layer:
            if gid != 0:
                rect = pygame.Rect(
                    x * self.tmxdata.tilewidth,
                    y * self.tmxdata.tileheight,
                    self.tmxdata.tilewidth,
                    self.tmxdata.tileheight
                )
                self.breakabletiles.append({
                    "rect": rect,
                    "tile_x": x,
                    "tile_y": y,
                    "gid": gid,
                    "is_animating": False,
                    "offset_y": 0,
                    "start_y": rect.y,
                    "animation_timer": 0
                })
                self.collision_objects.append(rect)

    def update_breakable_tile_animations(self):
            for tile in self.breakabletiles:
                if tile["is_animating"]:
                    tile["animation_timer"] += 1
                    t = tile["animation_timer"]

                    if t <= 10:
                        tile["offset_y"] = -abs(8 * (1 - t / 10))
                    else:
                        tile["offset_y"] = 0
                        tile["is_animating"] = False
                        tile["animation_timer"] = 0

                    # Apply offset directly to rect.y here
                    tile["rect"].y = tile["start_y"] + tile["offset_y"]


                

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, rect):
        return rect.move(-self.camera.x, -self.camera.y)
        
    def update(self, target):
        x = target.rect.centerx + BASE_WIDTH  // 2
        x = max(0, min(x, self.width - BASE_WIDTH))
       
        y = 0

        self.camera.topleft = (x, y)

def main():
    game = Game("TOC2.tmx")
    spawn_x, spawn_y = game.get_spawn_point()

    player= Player(spawn_x, spawn_y)
    camera= Camera(game.map_width, game.map_height)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        player.update(game.collision_objects)
        player.trybreakblocks(game)
        camera.update(player)
        game.update_breakable_tile_animations()
        game_surface.fill((50, 50, 50))
        game.render(game_surface, camera.camera)
        game_surface.blit(player.image, camera.apply(player.rect))
        scaled_surface = pygame.transform.scale(game_surface, screen.get_size())
        screen.blit(scaled_surface, (0, 0))
        pygame.display.flip()
        clock.tick(fps)
        
if __name__ == "__main__":
    main()