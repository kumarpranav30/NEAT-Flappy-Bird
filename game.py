import neat.population
import pygame
import neat
import time
import os
import random
import pickle

WINDOW_HEIGHT = 800
WINDOW_WIDTH = 500
GEN = 0

BIRD_IMAGES = [
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png"))),
]
PIPE_IMAGE = pygame.transform.scale2x(
    pygame.image.load(os.path.join("imgs", "pipe.png"))
)
BASE_IMAGE = pygame.transform.scale2x(
    pygame.image.load(os.path.join("imgs", "base.png"))
)
BG_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

pygame.font.init()
STAT_FONT = pygame.font.Font(os.path.join("fonts", "PressStart2P-Regular.ttf"), 20)


class Bird:
    IMGS = BIRD_IMAGES
    MAX_ROT = 25
    ROT_V = 20
    ANIM_T = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.ticks = 0
        self.vel = 0
        self.height = self.y
        self.img_cnt = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5  
        self.ticks = 0  
        self.height = self.y

    def move(self):
        self.ticks += 1

        displacement = self.vel * self.ticks + 0.5 * 3 * (self.ticks**2)

        if displacement >= 16:
            displacement = 16

        if displacement < 0:
            displacement -= 2

        self.y += displacement

        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROT:
                self.tilt = self.MAX_ROT
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_V

    def draw(self, win):
        self.img_cnt += 1

        if self.img_cnt < self.ANIM_T:
            self.img = self.IMGS[0]
        elif self.img_cnt < self.ANIM_T * 2:
            self.img = self.IMGS[1]
        elif self.img_cnt < self.ANIM_T * 3:
            self.img = self.IMGS[2]
        elif self.img_cnt < self.ANIM_T * 4:
            self.img = self.IMGS[1]
        elif self.img_cnt == self.ANIM_T * 4 + 1:
            self.img = self.IMGS[0]
            self.img_cnt = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_cnt = self.ANIM_T * 2

        rotated_img = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_img.get_rect(
            center=self.img.get_rect(topleft=(self.x, self.y)).center
        )
        win.blit(rotated_img, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.gap = 100

        self.top = 0
        self.bottom = 0
        self.TOP_PIPE = pygame.transform.flip(
            surface=PIPE_IMAGE, flip_x=False, flip_y=True
        )
        self.BOTTOM_PIPE = PIPE_IMAGE

        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.TOP_PIPE.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.TOP_PIPE, (self.x, self.top))
        win.blit(self.BOTTOM_PIPE, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.TOP_PIPE)
        bottom_mask = pygame.mask.from_surface(self.BOTTOM_PIPE)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True

        return False


class Base:
    VEL = 5
    WIDTH = BASE_IMAGE.get_width()
    IMAGE = BASE_IMAGE

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMAGE, (self.x1, self.y))
        win.blit(self.IMAGE, (self.x2, self.y))


def render_text_with_outline_and_shadow(
    font, text, color, outline_color, shadow_color, shadow_offset, outline_thickness=2
):
    base_text = font.render(text, True, color)
    shadow_text = font.render(text, True, shadow_color)

    width, height = base_text.get_size()
    text_surface = pygame.Surface(
        (
            width + outline_thickness * 2 + shadow_offset,
            height + outline_thickness * 2 + shadow_offset,
        ),
        pygame.SRCALPHA,
    )

    outline_positions = [
        (dx, dy)
        for dx in range(-outline_thickness, outline_thickness + 1)
        for dy in range(-outline_thickness, outline_thickness + 1)
        if dx != 0 or dy != 0
    ]

    outline_texts = [font.render(text, True, outline_color) for _ in outline_positions]

    for i, (dx, dy) in enumerate(outline_positions):
        text_surface.blit(
            outline_texts[i], (dx + outline_thickness, dy + outline_thickness)
        )

    text_surface.blit(
        shadow_text,
        (shadow_offset + outline_thickness, shadow_offset + outline_thickness),
    )
    text_surface.blit(base_text, (outline_thickness, outline_thickness))

    return text_surface


def draw_window(win, birds, pipes, base, score, gen):
    win.blit(BG_IMAGE, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    score_text = render_text_with_outline_and_shadow(
        STAT_FONT,
        "SCORE : " + str(score),
        (255, 255, 255),
        (0, 0, 0),
        (0, 0, 0),
        2,
        outline_thickness=2,
    )
    win.blit(score_text, (WINDOW_WIDTH - 10 - score_text.get_width(), 10))

    
    gen_text = render_text_with_outline_and_shadow(
        STAT_FONT,
        "GEN : " + str(gen),
        (255, 255, 255),
        (0, 0, 0),
        (0, 0, 0),
        2,
        outline_thickness=2,
    )
    win.blit(gen_text, (10, 10))

    base.draw(win)
    
    for bird in birds:
        bird.draw(win)  
    pygame.display.update()


def main(genomes, config):
    global GEN
    GEN += 1
    nets = []
    ge = []
    birds = []

    for g in genomes:
        
        net = neat.nn.FeedForwardNetwork.create(g[1], config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g[1].fitness = 0
        ge.append(g[1])

    
    base = Base(730)
    pipes = [Pipe(600)]
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    run = True

    score = 0

    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0

        if len(birds) > 0:
            if (
                len(pipes) > 1
                and birds[0].x > pipes[0].x + pipes[0].TOP_PIPE.get_width()
            ):
                pipe_ind = 1
        else:
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            
            ge[x].fitness += 0.1

            output = nets[x].activate(
                (
                    bird.y,
                    abs(bird.y - pipes[pipe_ind].height),
                    abs(bird.y - pipes[pipe_ind].bottom),
                )
            )

            if output[0] > 0.5:
                bird.jump()
        rem = []
        add_pipe = False

        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[birds.index(bird)].fitness -= 1
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.TOP_PIPE.get_width() < 0:
                rem.append(pipe)

            pipe.move()

        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        if score > 50:
            break

        base.move()
        draw_window(window, birds, pipes, base, score, GEN)

def run(config_path):
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path,
    )

    p = neat.Population(config)

    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main, 50)
    with open('best_bird.pkl', 'wb') as file:
        pickle.dump(winner, file)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config_feedforward_68c3f3d4a7.txt")
    run(config_path)
