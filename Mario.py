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

SPRITE_WIDTH = 34
SPRITE_HEIGHT = 26
ANIMATION_SPEED = 150

game_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
screen = pygame.display.set_mode((screen_width, screen_height))

pygame.init()
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("ST2DO")
clock = pygame.time.Clock()
screen.fill((50,50,50))

def load_coin_frames(sheet_path, frame_width=11, frame_height=16, scale_to=TILE_SIZE):
    sheet = pygame.image.load(sheet_path).convert_alpha()
    frames = []
    sheet_height= sheet.get_height()

    frame_count = 2
    for i in range(frame_count):
        y = i * frame_height
        frame_rect = pygame.Rect(0, y, frame_width, frame_height)

        if y + frame_height > sheet_height:
            continue

        frame = sheet.subsurface(frame_rect)
        scaled = pygame.transform.scale(frame, (scale_to, scale_to))
        frames.append(scaled)

        return frames

def load_frames(sheet_path, frame_count):
    sheet = pygame.image.load(sheet_path).convert_alpha()

    frames = []
    for i in range (frame_count):
        x = i * (SPRITE_WIDTH + 1.5)
        frame = sheet.subsurface(pygame.Rect(x, 0, SPRITE_WIDTH, SPRITE_HEIGHT))
        frames.append(frame)

    return frames

test = load_frames("toadstand.png", 1)

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()

        self.grounded_timer = 0

        self.idle_frames = load_frames("toadstand.png", 1)
        self.walk_frames = load_frames("toadsheet.png", 2)
        self.jump_frames = load_frames("Toadjump.png", 1)

        self.current_frame_list = self.idle_frames
        self.frame_index = 0

        self.image = self.current_frame_list[self.frame_index]
        self.rect = self.image.get_rect(topleft=(x, y))

        self.animation_timer = 0
        self.facing_left = False

        self.pos = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0,0)
        self.onground = False

    def update(self, collision_objects):
        keys = pygame.key.get_pressed()
       
        dt = clock.get_time()

        self.velocity.x = (keys[pygame.K_d] - keys[pygame.K_a]) * 2.5
       
       
        if self.velocity.x < 0:
            self.facing_left = True
        elif self.velocity.x > 0:
            self.facing_left = False

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
    
        if self.grounded_timer == 0:
            if self.current_frame_list != self.jump_frames:
                print("[jup]")
            self.current_frame_list = self.jump_frames

        elif self.velocity.x != 0:
            if self.current_frame_list != self.walk_frames:
                print("[wup]")
            self.current_frame_list = self.walk_frames
        else:
            self.grounded_timer = max(0, self.grounded_timer - dt)
            self.current_frame_list = self.idle_frames

        if len(self.current_frame_list) > 1:
            self.animation_timer += clock.get_time()
            if self.animation_timer >= ANIMATION_SPEED:
                self.animation_timer = 0
                self.frame_index = (self.frame_index + 1) % len (self.current_frame_list)
        else:
            self.frame_index = 0

        self.image = self.current_frame_list[self.frame_index]
        if self.facing_left:
            self.image = pygame.transform.flip(self.image, True, False)

    def check_collision(self, collision_objects, direction):
        grounded = False

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
                        self.velocity.y = 0
                        self.pos.y = self.rect.y
                        grounded = True

                        if grounded and not self.onground:
                            self.grounded_timer = 100

                    elif self.velocity.y < 0:
                        self.rect.top = obj.bottom
                    self.pos.y = self.rect.y
                    self.velocity.y = 0

        if direction == "vertical":
            if grounded and not self.onground:
                self.grounded_timer = 100
            self.onground = grounded

    def trybreakblocks(self, game):
        if self.velocity.y < 0:
            hitbox = pygame.Rect(self.rect.x, self.rect.y - 10, self.rect.width, 10)

            for tile in game.breakabletiles:
                if hitbox.colliderect(tile["rect"]) and not tile["is_animating"] and not tile["has_spawned"]:
                    print(f"pup ({tile['tile_x']}, {tile['tile_y']})")
                    tile ["is_animating"] = True
                    tile["animation_timer"] = 0
                    
                    found_spawn = False

                    for spawn in game.reward_spawn_points:
                        spawn_rect = pygame.Rect(spawn["x"], spawn["y"], TILE_SIZE, TILE_SIZE)
                        if spawn_rect.colliderect(tile["rect"]):
                            reward = RewardSprite(spawn["x"], spawn["y"])
                            game.spawned_rewards.add(reward)
                            found_spawn = True
                            break

                    if not found_spawn:
                        reward_x = tile["rect"].centerx - 8
                        reward_y = tile["rect"].y - 16
                        reward = RewardSprite(reward_x, reward_y)
                        game.spawned_rewards.add(reward)

                    tile["has_spawned"] = True
                    game.score += 1


class Game:
    def __init__(self, map_file):
        self.tmxdata = pytmx.load_pygame(map_file, pixelalpha=True)
        self.map_width = self.tmxdata.width * self.tmxdata.tilewidth
        self.map_height = self.tmxdata.height * self.tmxdata.tileheight
        self.collision_objects = []
        self.breakabletiles = []

        self.rewards = []
        self.spawned_rewards = pygame.sprite.Group()

        self.loadbreakabletiles()
        self.load_collision_objects()

        self.load_reward_object()
        self.load_reward_spawn_points()

        self.score = 0
        self.font = pygame.font.SysFont("Arial", 25)

    def load_collision_objects(self):
        print("[bup]")
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
                    "animation_timer": 0,
                    "has_spawned": False
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

    def load_reward_object(self):
        reward_layer = self.tmxdata.get_layer_by_name("Rewards")

        for obj in reward_layer:
            rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
            self.rewards.append({
                "rect": rect,
                "is_animating": False,
                "animation_timer": 0,
                "start_y": rect.y,
                "offset_y": 0,
                "spawned": False
            })
                
    def load_reward_spawn_points(self):
        self.reward_spawn_points = []

        try:
            layer = self.tmxdata.get_layer_by_name("reward_spawn")
            for obj in layer:
                self.reward_spawn_points.append({
                    "x": obj.x,
                    "y": obj.y,
                    "type": obj.type
                })
        except:
            print("[tup]")

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, rect):
        return rect.move(-self.camera.x, -self.camera.y)
        
    def update(self, target):
        x = target.rect.centerx - BASE_WIDTH  // 2
        x = max(0, min(x, self.width - BASE_WIDTH))
       
        y = 0

        self.camera.topleft = (x, y)

class RewardSprite(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()

        # self.image = pygame.Surface((16,16), pygame.SRCALPHA)
        # pygame.draw.circle(self.image, (255, 0, 0), (8, 8), 6)
        # self.rect = self.image.get_rect(center= (x + TILE_SIZE // 2, y))

        self.frames = load_coin_frames("coin_spritesheet.png", 11, 16, TILE_SIZE)
        self.frame_index = 0
        self.animation_speed = 150
        self.last_update = pygame.time.get_ticks()

        self.start_y = self.rect.y
        self.phase = 0
        self.timer = 0
        self.float_height = 20
        self.pause_duration = 10

    def update(self):
        now = pygame.time.get_ticks()

        if now - self.last_update > self.animation_speed:
            self.last_update = now
            self.frame_index = (self.frame_index + 1)% len(self.frames)
            self.image = self.frames[self.frame_index]

        if self.phase == 0:
            self.rect.y -= 2
            if self.start_y - self.rect.y >= self.float_height:
                self.phase = 1
                self.timer = 0

        elif self.phase == 1:
            self.timer += 1
            if self.timer >= self.pause_duration:
                self.kill()

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

        score_text = game.font.render(f"score: {game.score}", True, (255, 255, 255))
        game_surface.blit(score_text, (4, 4))

        game_surface.blit(player.image, camera.apply(player.rect))
        game.spawned_rewards.update()
        for reward in game.spawned_rewards:
            game_surface.blit(reward.image, camera.apply(reward.rect))

        scaled_surface = pygame.transform.scale(game_surface, screen.get_size())
        screen.blit(scaled_surface, (0, 0))
        pygame.display.flip()
        clock.tick(fps)
        
if __name__ == "__main__":
    main()

