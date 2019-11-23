# Import section
from random import randint, random
from pygame import image, draw, font, mixer

# Set mixer
mixer.init(buffer=512)  # Default 4096, but smaller makes sound less laggy
mixer.music.set_volume(0.2)

# Constant sections
throwSound = mixer.Sound("Resources/SoundEffects/throw.wav")
hitSound = mixer.Sound("Resources/SoundEffects/hit.wav")
gruntSound = mixer.Sound("Resources/SoundEffects/pain.wav")
potionSound = mixer.Sound("Resources/SoundEffects/potion.wav")
background_music = mixer.music.load("Resources/SoundEffects/background_music.mp3")


# Classes section
class World:
    """2D rectangular world where game takes place"""
    gravitational_acceleration = 2.8
    background_img = image.load('Resources/bg.jpg')

    def __init__(self, ground_padding=3):
        """
        Initialize new world from background image
        :param ground_padding: How much of screen bottom is inaccessible to characters (as percentage of total height)
        """
        self.size = (World.background_img.get_width(), World.background_img.get_height())
        self.ground_level = self.height * (100 - ground_padding) / 100
        self.score = 0
        self.max_num_goblins = 3
        self.baldy = MainCharacter((self.width / 2, self.ground_level - MainCharacter.height))
        self.goblins = []
        self.bullets = []
        self.potions = []

    def draw_intro(self, win):
        """
        Displays intro
        :param win: Window where game is drawn
        """
        # Draw background
        win.blit(World.background_img, (0, 0))

        # Draw main character
        win.blit(MainCharacter.facing_camera_sprite, self.baldy.hit_box.position)

        # Draw title
        opening_img = image.load('Resources/opening_text.png')

        y = self.height / 30
        x = (self.width - opening_img.get_width()) / 2

        win.blit(opening_img, (x, y))

        # Start music
        mixer.music.play(-1)

    def draw_game_over(self, win):
        """
        Displays game over
        :param win: Window where game is drawn
        """
        # Draw background
        win.blit(World.background_img, (0, 0))

        # Draw main character dead
        baldy_position = (self.baldy.hit_box.x_coord, self.ground_level - self.baldy.hit_box.height)
        win.blit(MainCharacter.laying_dead_sprite, baldy_position)

        # Draw goblins
        for goblin in self.goblins:
            goblin.draw(win)

        # Draw score board
        score_count = f"Score: {self.score}"
        text = font.SysFont("comicsansms", 22).render(score_count, True, (0, 0, 0))
        win.blit(text, ((self.width - text.get_width()) // 2, self.height / 30))

        # Draw game over text
        opening_img = image.load('Resources/game_over.png')

        y = self.height / 30 + text.get_height() + 5
        x = (self.width - opening_img.get_width()) / 2

        win.blit(opening_img, (x, y))

    @property
    def main_character_died(self):
        """Checks if main character is dead"""
        return self.baldy.is_dead

    def spawn_potion(self):
        """Spawn potion in random position"""
        max_x = self.width - Potion.width
        x_coord = randint(0, max_x)
        y_coord = randint(0, 10) - 2 + self.ground_level - Potion.height

        self.potions.append(Potion((x_coord, y_coord)))

    def spawn_goblin(self):
        """Spawn goblin in random position"""
        r = random()
        x_coord = 0 if r < .5 else self.width
        y_coord = randint(0, 10) - 2 + self.ground_level - Goblin.height

        self.goblins.append(Goblin((x_coord, y_coord)))

    def give_commands(self, commands):
        """Gives list of commands to world"""
        move_left = "left" in commands
        move_right = "right" in commands
        if move_left and move_right or "down" in commands:
            self.baldy.stand_still(face_camera=True)
        elif move_left:
            self.baldy.set_walking_direction(is_going_right=False)
        elif move_right:
            self.baldy.set_walking_direction(is_going_right=True)
        if "up" in commands:
            self.baldy.jump(self)
        elif not move_right and not move_left:
            self.baldy.stand_still()
        if "shoot" in commands:
            new_bullet = self.baldy.shoot()
            if new_bullet is not None:
                self.bullets.append(new_bullet)

    @property
    def width(self):
        """World width in pixels"""
        return self.size[0]

    @property
    def height(self):
        """World height in pixels"""
        return self.size[1]

    def increase_score(self, increase_amount):
        """Increases score by given amount"""
        self.score += increase_amount
        self.max_num_goblins = self.score // 200 + 3

    def go_to_next_frame(self):
        """Move world to next frame"""
        self.baldy.go_to_next_frame(self)
        for potion in self.potions:
            # Check collision between potion and main character
            if self.baldy.hit_box.collided_with(potion.hit_box):
                self.baldy.hp_bar.heal(5)
                potionSound.play()
                self.potions.remove(potion)
            else:
                potion.go_to_next_frame()
                if potion.is_expired:
                    self.potions.remove(potion)

        for goblin in self.goblins:
            goblin.go_to_next_frame(self)
            # Check collision between goblin and main character
            if self.baldy.hit_box.collided_with(goblin.hit_box):

                if self.baldy.damaged_by_goblin():
                    gruntSound.play()

        for bullet in self.bullets:
            bullet.go_to_next_frame()
            if bullet.left_world(self):
                self.bullets.remove(bullet)
            else:
                # Check collision between bullet and goblin
                for goblin in self.goblins:
                    if bullet.collided_with(goblin.hit_box):
                        hitSound.play()
                        self.bullets.remove(bullet)
                        goblin.hp_bar.deal_damage(5)
                        if goblin.is_dead:
                            self.increase_score(10)
                            self.goblins.remove(goblin)
                        else:
                            self.increase_score(1)
                        break

        # Spawn new potion
        if len(self.potions) == 0:
            r = random()
            if r < 0.01:
                self.spawn_potion()

        # Spawn new goblins
        num_goblins = len(self.goblins)
        if num_goblins == 0:
            # Prevents game from having 0 goblins
            self.spawn_goblin()
        elif num_goblins < self.max_num_goblins:
            r = random()
            if r < 0.01:
                self.spawn_goblin()

    def draw(self, win):
        """
        Draw world on given window
        :param win: Game window
        """
        # Redraw background
        win.blit(World.background_img, (0, 0))

        # Draw score board
        score_count = f"Score: {self.score}"
        text = font.SysFont("comicsansms", 22).render(score_count, True, (0, 0, 0))
        win.blit(text, ((self.width - text.get_width()) // 2, self.height / 30))

        # Draw potion
        for potion in self.potions:
            potion.draw(win)
            # potion.draw_hit_box(win)  # -> Useful for debugging

        # Draw goblins
        for goblin in self.goblins:
            goblin.draw(win)
            # goblin.draw_hit_box(win)  # -> Useful for debugging

        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(win)

        # Draw main character
        self.baldy.draw(win)
        # self.baldy.draw_hit_box(win)  #-> Useful for debugging

    def __str__(self):
        return f"\tWorld size (width, height): {self.size}\n\tGround level: {self.ground_level}"


class Animation:
    """
    Class for list of sprites that are displayed sequentially
    """

    def __init__(self, sprites, frames_per_sprite=3):
        """
        Initialize new animation from list of sequential sprites
        :param sprites: List of sprites in sequence
        :param frames_per_sprite: How long each sprite should be displayed
        """
        self.dimensions = (sprites[0].get_width(), sprites[0].get_height())
        '''
        for sprite in sprites:
            dimension = (sprite.get_width(), sprite.get_height())
            if self.dimensions != dimension:
                raise Exception("All sprites must have the same width and height")
        '''
        self.sprites = sprites
        self.frames_per_sprite = frames_per_sprite
        self.max_animation_count = len(self.sprites) * self.frames_per_sprite

    def get_sprite(self, sprite_index):
        """Returns sprite with given index"""
        return self.sprites[sprite_index]

    def draw_and_increment(self, animation_count, position, win):
        """
        Draws animation in given position and window
        :param animation_count: Index of animation frame
        :param position: Position of top/left vertex
        :param win: Window where animation is displayed
        :return: Index of next animation count
        """
        sprite_index = animation_count // self.frames_per_sprite
        win.blit(self.sprites[sprite_index], position)

        new_animation_count = animation_count + 1
        if new_animation_count >= self.max_animation_count:
            new_animation_count = 0
        return new_animation_count

    def __str__(self):
        frames_plural = "frames" if self.frames_per_sprite != 1 else "frame"
        return f"\t{len(self.sprites)} sprites" \
               f"\n\tEach sprite is displayed for {self.frames_per_sprite} {frames_plural}"


class Rectangle:
    """Rectangle with given width and height"""

    def __init__(self, size=(10, 10), position=(0, 0)):
        """
        Initialize new rectangle
        :param size: Rectangle size (width, height)
        :param position: 2D position of top/left vertex
        """
        self.position = position
        self.size = size

    def collided_with(self, other):
        """Checks if rectangle has collided with another rectangle"""
        if self.x_coord > other.x_coord + other.width:
            return False

        if self.x_coord + self.width < other.x_coord:
            return False

        if self.y_coord > other.y_coord + other.height:
            return False

        if self.y_coord + self.height < other.y_coord:
            return False

        return True

    @property
    def width(self):
        """Rectangle width in pixels"""
        return self.size[0]

    @property
    def height(self):
        """Rectangle height in pixels"""
        return self.size[1]

    @property
    def x_coord(self):
        """X coordinate of top/left vertex"""
        return self.position[0]

    @x_coord.setter
    def x_coord(self, new_x):
        """Sets new x_coordinate"""
        self.position = (new_x, self.position[1])

    @property
    def y_coord(self):
        """Y coordinate of top/left vertex"""
        return self.position[1]

    @y_coord.setter
    def y_coord(self, new_y):
        """Sets new y coordinate"""
        self.position = (self.position[0], new_y)

    def draw(self, win, color=(255, 0, 0), fill=True):
        """
        Draw rectangle with given color in window
        :param win: Window where rectangle is drawn
        :param color: Color to color rectangle
        :param fill: Indicates if rectangle should be filled or not
        """
        rectangle = (
            self.x_coord, self.y_coord, self.width, self.height)
        if fill:
            draw.rect(win, color, rectangle)
        else:
            draw.rect(win, color, rectangle, 1)

    def keep_in_world(self, world: World):
        """
        Keeps rectangle within screen, and sets velocity and acceleration to 0 in direction of infringement
        :param world: World with width and height
        """
        max_x = world.width - self.width
        if self.x_coord < 0:
            self.x_coord = 0
        elif self.x_coord > max_x:
            self.x_coord = max_x

        max_y = world.ground_level - self.height
        if self.y_coord < 0:
            self.y_coord = 0
        elif self.y_coord > max_y:
            self.y_coord = max_y

    def __str__(self):
        return f"\tPosition (x, y): {self.position}\n\tSize (width, height): {self.size}"


class HealthPoints:
    """Class for storing and drawing health points"""
    bar_height = 8
    spacing = 10
    vertical_displacement = spacing + bar_height
    bar_width = 70

    def __init__(self, character_width, max_health_points=100):
        """Initialize new HP to store"""
        self.max_health_points = max_health_points
        self.health_points = max_health_points
        self.horizontal_displacement = (HealthPoints.bar_width - character_width) / 2
        self.green_rectangle_width = HealthPoints.bar_width

    def deal_damage(self, damage):
        """Remove given amount from health points"""
        self.health_points -= damage
        self.set_green_rectangle_width()

    def heal(self, extra_health_points):
        """Give extra health points to character"""
        self.health_points += extra_health_points
        if self.health_points > self.max_health_points:
            self.health_points = self.max_health_points
        self.set_green_rectangle_width()

    def health_bar_position(self, character):
        """
        Sets health bar position where character is
        :param character: Character to whom life bar belongs
        """
        x_coord = character.hit_box.x_coord - self.horizontal_displacement
        y_coord = character.hit_box.y_coord - HealthPoints.vertical_displacement
        return x_coord, y_coord

    def set_green_rectangle_width(self):
        """Sets health bar width when damage is taken"""
        new_width = HealthPoints.bar_width * self.health_points / self.max_health_points
        if new_width < 0:
            new_width = 0
        self.green_rectangle_width = new_width

    def draw(self, character, win):
        """Draw HP bar in given window"""
        position = self.health_bar_position(character)

        # Draw red rectangle
        red_rectangle = (position[0], position[1], HealthPoints.bar_width, HealthPoints.bar_height)
        draw.rect(win, (200, 50, 60), red_rectangle)

        # Draw green rectangle
        if self.green_rectangle_width > 0:
            green_rectangle = (position[0], position[1], self.green_rectangle_width, HealthPoints.bar_height)
            draw.rect(win, (0, 168, 107), green_rectangle)

        # Draw border
        draw.rect(win, (0, 0, 0), red_rectangle, 1)

    def __str__(self):
        return f"Health points: {self.health_points}/{self.max_health_points}"


class Potion:
    """Potion for healing main character"""
    potion_image = image.load("Resources/potion.png")
    life_span = 200  # Number of frames that potion exists for
    height = potion_image.get_height()
    width = potion_image.get_width()
    progress_bar_height = 10
    max_progress_bar_width = 80
    spacing = 10
    horizontal_displacement = (width - max_progress_bar_width) / 2
    vertical_displacement = height + spacing

    def __init__(self, position):
        """Initialize new potion"""
        self.hit_box = Rectangle((Potion.width, Potion.height), position)
        self.timer = Potion.life_span
        timer_bar_x_coord = self.hit_box.x_coord + Potion.horizontal_displacement
        timer_bar_y_coord = self.hit_box.y_coord - Potion.vertical_displacement
        self.bar_position = (timer_bar_x_coord, timer_bar_y_coord)

    @property
    def is_expired(self):
        """Check if potion expired"""
        return self.timer <= 0

    def go_to_next_frame(self):
        """Moves potion to next frame"""
        self.timer -= 1

    def draw(self, win):
        win.blit(Potion.potion_image, self.hit_box.position)

        # Draw timer bar
        width = Potion.max_progress_bar_width * self.timer / Potion.life_span
        rect = (self.bar_position[0], self.bar_position[1], width, Potion.progress_bar_height)
        draw.rect(win, (0, 0, 255), rect)

    def __str__(self):
        return f"\tEnclosing box: {self.hit_box}\n\tTimer: {self.timer}/{Potion.life_span}"


class Bullet:
    """Bullet that main character shoots"""
    bullet_speed = 20  # In pixels per frame
    bullet_radius = 3

    def __init__(self, initial_position, is_going_right):
        """
        Initialize new bullet
        :param initial_position: Initial x,y coordinates
        :param is_going_right: True if bullet is going right, false otherwise
        """
        self.x = int(initial_position[0])
        self.y = int(initial_position[1])
        self.is_going_right = is_going_right
        self.signed_speed = Bullet.bullet_speed
        if not self.is_going_right:
            self.signed_speed *= -1

    def go_to_next_frame(self):
        """Move bullet to next frame"""
        self.x += self.signed_speed

    def left_world(self, world):
        """Checks if bullet has left the world"""
        return self.x - Bullet.bullet_radius > world.width or self.x + Bullet.bullet_radius < 0

    def collided_with(self, rectangle):
        """Checks if bullet has collided with rectangle"""
        if self.x - Bullet.bullet_radius > rectangle.x_coord + rectangle.width:
            return False

        if self.x + Bullet.bullet_radius < rectangle.x_coord:
            return False

        if self.y - Bullet.bullet_radius > rectangle.y_coord + rectangle.height:
            return False

        if self.y + Bullet.bullet_radius < rectangle.y_coord:
            return False

        return True

    def draw(self, win):
        """Draw bullet on given window"""
        draw.circle(win, (0, 0, 0), (self.x, self.y), Bullet.bullet_radius)

    def __str__(self):
        direction = "right" if self.is_going_right else "left"
        return f"\tbullet going {direction}\n\tPosition (x, y): {self.x}, {self.y}"


class Character:
    """Super class for game characters"""

    def __init__(self, initial_position, walk_right_animation, walk_left_animation, walking_velocity=3,
                 max_health_points=100):
        """
        Initialize new character
        :param walk_right_animation: Animation for character walking right
        :param walk_left_animation: Animation for character walking left
        :param initial_position: Initial position (x, y)
        :param walking_velocity: Initial horizontal velocity (in pixels/frame)
        :param max_health_points: Maximum health points
        """
        self.walk_right_animation = walk_right_animation
        self.walk_left_animation = walk_left_animation
        # Enclosing box has the same size as animation
        self.hit_box = Rectangle(walk_right_animation.dimensions, initial_position)
        self.walking_velocity = walking_velocity
        self.is_walking_right = True
        self.animation_count = 0
        self.hp_bar = HealthPoints(self.hit_box.width, max_health_points)

    @property
    def is_dead(self):
        """Checks if character has no health points left"""
        return self.hp_bar.health_points <= 0

    def reset_animation_count(self):
        """Sets animation count back to 0"""
        self.animation_count = 0

    def set_direction(self, is_going_right):
        """
        Sets character direction
        :param is_going_right: True if character is walking right, false otherwise
        :return:
        """
        if is_going_right != self.is_walking_right:
            self.is_walking_right = is_going_right
            self.reset_animation_count()

    def go_to_next_frame(self, world):
        """
        Move character in direction he's walking
        :param world: World that constrains character
        """
        if self.is_walking_right:
            horizontal_displacement = self.walking_velocity
        else:
            horizontal_displacement = -self.walking_velocity
        self.hit_box.x_coord += horizontal_displacement
        self.hit_box.keep_in_world(world)

    def draw(self, win):
        """
        Draw character on given window
        :param win: Window where character is to be drawn
        """
        if self.is_walking_right:
            self.animation_count = self.walk_right_animation.draw_and_increment(self.animation_count,
                                                                                self.hit_box.position, win)
        else:
            self.animation_count = self.walk_left_animation.draw_and_increment(self.animation_count,
                                                                               self.hit_box.position, win)

        self.hp_bar.draw(self, win)

    def draw_hit_box(self, win):
        """Draw enclosing rectangle around character"""
        self.hit_box.draw(win, (255, 0, 0), False)

    def __str__(self):
        direction = "right" if self.is_walking_right else "left"
        return f"\tEnclosing box: {self.hit_box}\n\tDirection: {direction}\n\tWalking velocity: {self.walking_velocity}\n\t{self.hp_bar}"


class Goblin(Character):
    goblin_walking_right = Animation(
        [image.load('Resources/R1E.png'), image.load('Resources/R2E.png'), image.load('Resources/R3E.png'),
         image.load('Resources/R4E.png'), image.load('Resources/R5E.png'), image.load('Resources/R6E.png'),
         image.load('Resources/R7E.png'), image.load('Resources/R8E.png'), image.load('Resources/R9E.png'),
         image.load('Resources/R10E.png'), image.load('Resources/R11E.png')])
    goblin_walking_left = Animation(
        [image.load('Resources/L1E.png'), image.load('Resources/L2E.png'), image.load('Resources/L3E.png'),
         image.load('Resources/L4E.png'), image.load('Resources/L5E.png'), image.load('Resources/L6E.png'),
         image.load('Resources/L7E.png'), image.load('Resources/L8E.png'), image.load('Resources/L9E.png'),
         image.load('Resources/L10E.png'), image.load('Resources/L11E.png')])
    height = goblin_walking_right.dimensions[1]

    def __init__(self, initial_position, velocity_range=(2, 5)):
        """
        Initialize new goblin
        :param initial_position: Initial position in pixels
        """
        walking_velocity = randint(velocity_range[0], velocity_range[1])
        super().__init__(initial_position, Goblin.goblin_walking_right, Goblin.goblin_walking_left, walking_velocity)

    def change_direction_randomly(self):
        """0.5% Chance of changing goblin's direction"""
        r = random()
        if r < 0.005:
            self.set_direction(not self.is_walking_right)

    def go_to_next_frame(self, world):
        """
        Moves goblin in world, and changes his direction randomly
        :param world: World where goblin is
        """
        super().go_to_next_frame(world)
        # Check if hit the wall
        if self.hit_box.x_coord <= 0:
            self.set_direction(is_going_right=True)
        elif self.hit_box.x_coord + self.hit_box.width >= world.width:
            self.set_direction(is_going_right=False)
        else:
            self.change_direction_randomly()


class MainCharacter(Character):
    facing_camera_sprite = image.load('Resources/standing.png')
    laying_dead_sprite = image.load('Resources/dead_baldy.png')
    char_walking_right = Animation(
        [image.load('Resources/R1.png'), image.load('Resources/R2.png'), image.load('Resources/R3.png'),
         image.load('Resources/R4.png'), image.load('Resources/R5.png'), image.load('Resources/R6.png'),
         image.load('Resources/R7.png'), image.load('Resources/R8.png'), image.load('Resources/R9.png')])
    char_walking_left = Animation(
        [image.load('Resources/L1.png'), image.load('Resources/L2.png'), image.load('Resources/L3.png'),
         image.load('Resources/L4.png'), image.load('Resources/L5.png'), image.load('Resources/L6.png'),
         image.load('Resources/L7.png'), image.load('Resources/L8.png'), image.load('Resources/L9.png')])
    walking_velocity = 3
    height = char_walking_right.dimensions[1]
    damage_immunity_time = 60  # Number of frames that character is immune from new damage after taking damage
    bullet_latency = 14  # Number of frames that character must wait between shots

    def __init__(self, initial_position):
        """
        Initialize new main character
        :param initial_position: Initial position in pixels
        """
        super().__init__(initial_position, MainCharacter.char_walking_right, MainCharacter.char_walking_left,
                         MainCharacter.walking_velocity)
        self.is_walking = False
        self.is_facing_left = False
        self.is_facing_right = False
        self.is_jumping = False
        self.vertical_velocity = 0
        self.horizontal_jump_velocity = 0
        self.damage_count = 0  # Counts down when character took damage
        self.bullet_latency_count = 0  # Counts down when character shoots

    def shoot(self):
        """Returns new bullet if character can make a shot. Otherwise returns None"""
        if self.bullet_latency_count > 0 or self.is_immune:
            return None
        if self.is_facing_left:
            is_going_right = False
        elif self.is_facing_right:
            is_going_right = True
        else:
            return None
        self.bullet_latency_count = MainCharacter.bullet_latency
        position = (self.hit_box.x_coord + self.hit_box.width / 2, self.hit_box.y_coord + self.hit_box.height / 2)
        # Play bullet sound
        throwSound.play()
        return Bullet(position, is_going_right)

    @property
    def is_immune(self):
        """Checks if character is immune to damage"""
        return self.damage_count > 0

    def damaged_by_goblin(self):
        """Indicates that character was hit by goblin"""
        if not self.is_immune:
            self.hp_bar.deal_damage(5)
            self.damage_count = MainCharacter.damage_immunity_time
            return True
        return False

    def is_mid_air(self, world):
        """Checks if character is not touching the ground"""
        return self.hit_box.height + self.hit_box.y_coord < world.ground_level

    def jump(self, world):
        """Make main character jump (if he's not in mid air already)"""
        if not self.is_mid_air(world):
            self.animation_count = 0
            self.vertical_velocity = 30
            self.is_jumping = True
            if self.is_walking:
                # Horizontal jump velocity is higher than walking velocity
                self.horizontal_jump_velocity = 2.2 * self.walking_velocity if self.is_walking_right else - 2.2 * self.walking_velocity

            self.is_walking = False

    def set_walking_direction(self, is_going_right):
        """
        Sets characters walking direction
        :param is_going_right: True if character is walking right, false otherwise
        """
        if not self.is_jumping:
            self.is_facing_right = is_going_right
            self.is_facing_left = not is_going_right
            self.is_walking = True
            if is_going_right != self.is_walking_right:
                self.reset_animation_count()
                self.is_walking_right = is_going_right

    def stand_still(self, face_camera=False):
        """
        Make character stand still
        :param face_camera: True if character should face camera
        """
        if not self.is_jumping:
            if self.is_walking:
                self.is_walking = False
            if face_camera:
                self.is_facing_right = False
                self.is_facing_left = False

    def go_to_next_frame(self, world):
        """Move character to next frame"""
        if self.is_walking:
            super().go_to_next_frame(world)
        elif self.is_jumping:
            self.hit_box.y_coord -= self.vertical_velocity
            if self.is_mid_air(world):
                self.vertical_velocity -= World.gravitational_acceleration
                self.hit_box.x_coord += self.horizontal_jump_velocity
            else:
                # Landing from jump
                self.is_jumping = False
                self.vertical_velocity = 0
                self.horizontal_jump_velocity = 0
            self.hit_box.keep_in_world(world)

        # Count down damage immunity time
        if self.damage_count > 0:
            self.damage_count -= 1

        # Count down bullet latency time
        if self.bullet_latency_count > 0:
            self.bullet_latency_count -= 1

    def flicker(self):
        """Indicates if character should not be  drawn on this frame"""
        if not self.is_immune:
            return False
        m = self.damage_count % 6
        return m >= 3

    def draw(self, win):
        """
        Draw main character
        :param win: Window where character is to be drawn
        """
        if self.flicker():
            self.hp_bar.draw(self, win)
        else:
            if self.is_walking:
                super().draw(win)
            else:
                if self.is_facing_left:
                    img = MainCharacter.char_walking_left.get_sprite(0)
                elif self.is_facing_right:
                    img = MainCharacter.char_walking_right.get_sprite(0)
                else:
                    img = MainCharacter.facing_camera_sprite
                win.blit(img, self.hit_box.position)
                self.hp_bar.draw(self, win)
