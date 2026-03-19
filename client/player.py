from animation import Animation
import pygame
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from settings import *
class Player:
    ANIMATION_FRAMES = {
        ANIM_DOWN: 3,
        ANIM_RIGHT: 3,
        ANIM_LEFT: 3,
        ANIM_UP: 3,
        ANIM_HIT: 4,
        ANIM_DEATH: 4
    }
    def __init__(self, player_color, x, y, health, name, id):
        self.animations = self.create_animations(player_color)
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.current_animation = ANIM_DOWN
        self.health = health
        self.alive = True
        self.name = name
        self.id = id



    
    def create_animations(self, player_color):
        sprite_sheet = pygame.image.load("../assets/img/players.png").convert_alpha()
        animations = {}

        row_start = 0
        for anim_name, num_frames in self.ANIMATION_FRAMES.items():
            frames = []
            for j in range(num_frames):
                rect = pygame.Rect(
                    PLAYER_SIZE * player_color, 
                    PLAYER_SIZE * (row_start + j),  
                    PLAYER_SIZE,
                    PLAYER_SIZE
                )
                frames.append(sprite_sheet.subsurface(rect))
            animations[anim_name] = Animation(frames)
            row_start += num_frames  

        return animations




    def move_to(self, new_x, new_y, lerp=0.002):
        if not self.alive:
            return
        
        dx = new_x - self.rect.x
        dy = new_y - self.rect.y

       
        if abs(dx) > abs(dy):
            self.current_animation = ANIM_RIGHT if dx > 0 else ANIM_LEFT
        elif dy != 0:
            self.current_animation = ANIM_DOWN if dy > 0 else ANIM_UP

        # interpolate position
        # self.rect.x += dx * lerp
        self.rect.x += dx 
        # self.rect.y += dy * lerp
        self.rect.y += dy

   

    def update_anim(self, dt):
        self.animations[self.current_animation].update(dt)

    def render(self, screen, camera):
        frame = self.animations[self.current_animation].get_current_frame()

        screen_pos = (
            self.rect.x - camera.x,
            self.rect.y - camera.y
        )

        screen.blit(frame, screen_pos)

    def hit(self):
        self.current_animation = ANIM_HIT
        self.animations[self.current_animation].current_frame = 0
    
    def die(self):
        self.current_animation = ANIM_DEATH
        self.animations[self.current_animation].current_frame = 0
        self.alive = False



        
