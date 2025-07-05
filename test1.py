import pygame
import random

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
else:
    joystick = None

green = (128,128,0)
black = (255, 255, 255)
size = (600,600)
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Gretris")
done=False
clock=pygame.time.Clock()
fps=25

colors=[
    (25,51,0),
    (0,204,102),
    (0,153,0)
]

class Figure:
    x=0
    y=0

    figures=[
        [[0,1,2,3],[0,4,8,12]],
        [[1,2,5,6]],
        [[0,5,10,15],[12,9,6,3]]
    ]

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = random.randint(0, len(self.figures)-1)
        self.color = random.randint(1, len(colors)-1)
        self.rotation = 0

    def image(self):
        return self.figures[self.type][self.rotation]

    def rotate(self):
        self.rotation=(self.rotation + 1) % len(self.figures[self.type])

class Tetris:
    def __init__(self,height,width):
        self.height=height
        self.width=width
        self.field=[[0 for _ in range(width)] for _ in range(height)]
        self.score = 0
        self.state = "start"
        self.figure = None
        self.x = 100
        self.y = 60
        self.zoom = 20

    def new_figure(self):
        self.figure = Figure(3,0)

    def intersects(self):
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    if (i + self.figure.y > self.height - 1 or \
                    j + self.figure.x > self.width - 1 or \
                    j + self.figure.x < 0 or \
                    self.field[i + self.figure.y][j + self.figure.x] > 0):
                        return True
        return False
    
    def freeze(self):
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    self.field[i+self.figure.y][j + self.figure.x] = self.figure.color

        self.break_lines()

        self.new_figure()
        if self.intersects():
            self.state = "gameover"

    def go_down(self):
        self.figure.y += 1
        if self.intersects():
            self.figure.y -= 1
            self.freeze()

    def go_side(self, dx):
        old_x = self.figure.x
        self.figure.x += dx
        if self.intersects():
            self.figure.x = old_x

    def rotate(self):
        old_rotation = self.figure.rotation
        self.figure.rotate()
        if self.intersects():
            self.figure.rotation = old_rotation

    def break_lines(self):
        lines=0
        for i in range (1, self.height):
            zeros = 0
            for j in range(self.width):
                if self.field[i][j] == 0:
                    zeros += 1
            if zeros == 0 :
                lines +=1
                for i1 in range(i,1, -1):
                    for j in range(self.width):
                        self.field[i1][j] = self.field[i1 - 1][j]
        self.score += lines ** 2

game = Tetris(20, 10)
counter = 0
pressing_down = False

while not done:
    if game.figure is None:
        game.new_figure()

    counter += 1
    if counter > 100000:
        counter = 0

    if counter % (fps // 2) == 0 or pressing_down:
        if game.state == "start":
            game.go_down()

    joystick_deadzone = 0.3
    last_axis_action = {"x":0,"y":0}

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                game.rotate()
            if event.key == pygame.K_DOWN:
                pressing_down = True
            if event.key == pygame.K_LEFT:
                game.go_side(-1)
            if event.key == pygame.K_RIGHT:
                game.go_side(1)
            if event.key == pygame.K_ESCAPE:
                game.__init__(20,10)

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                pressing_down = False

    screen.fill(green)

    for i in range(game.height):
        for j in range(game.width):
            pygame.draw.rect(screen,black,[game.x + game.zoom * j, 
                                           game.y+ game.zoom * i, 
                                           game.zoom, 
                                           game.zoom],
                                           1)
            if game.field[i][j]>0:
                pygame.draw.rect(screen, colors [game.field[i][j]], 
                                 [game.x + game.zoom * j + 1, 
                                  game.y + game.zoom * i + 1, 
                                  game.zoom - 2, 
                                  game.zoom - 1])
                
    if game.figure is not None:
        for i in range(4):
            for j in range(4):
                p = i * 4 + j
                if p in game.figure.image():
                    pygame.draw.rect(screen, colors[game.figure.color],
                                     [game.x + game.zoom * (j + game.figure.x) + 1,
                                     game.y + game.zoom * (i + game.figure.y) + 1,
                                     game.zoom - 2, game.zoom - 2])
                
    font= pygame.font.SysFont("arial",25,True,False)
    text=font.render("Gcore:"+str(game.score), True, (220, 255, 219))
    screen.blit(text, [400,500])

    if game.state == "gameover":
        font1 = pygame.font.SysFont("arial",50,True,True)
        text_gameover = font1.render("Gou lose", True, (255,255,255), (1,84,0))
        screen.blit(text_gameover, [300,300])

    pygame.display.flip()
    clock.tick(60)

pygame.quit()