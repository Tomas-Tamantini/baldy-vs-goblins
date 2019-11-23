# Import section
from pygame import time, init, display, event, key, quit, QUIT, K_SPACE, K_DOWN, K_UP, K_RIGHT, K_LEFT

from game_classes import World

# Constant section
world = World()
win = display.set_mode((852, 480))
clock = time.Clock()
frame_rate = 27

# Setup section
display.set_caption("Baldy vs goblins")


# Auxiliary functions
def redraw_game_window():
    world.draw(win)
    display.update()


def check_events():
    if world.main_character_died:
        global game_over
        game_over = True
        draw_game_over()


def play_intro():
    world.draw_intro(win)
    display.update()
    time.delay(3000)


def draw_game_over():
    world.draw_game_over(win)
    display.update()


# Game starts here
init()

play_intro()

run = True
game_over = False
while run:
    clock.tick(frame_rate)
    for e in event.get():
        if e.type == QUIT:
            run = False
    if not game_over:
        keys = key.get_pressed()
        commands = []
        if keys[K_LEFT]:
            commands.append("left")
        if keys[K_RIGHT]:
            commands.append("right")
        if keys[K_UP]:
            commands.append("up")
        if keys[K_DOWN]:
            commands.append("down")
        if keys[K_SPACE]:
            commands.append("shoot")
        world.give_commands(commands)
        world.go_to_next_frame()
        redraw_game_window()
        check_events()

quit()
