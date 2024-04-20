import sys
from typing import Iterable, Union
import pygame as pg
import math



WATER_FRICTION = 0.05

def calculate_new_xy(old_xy,speed,angle):
    new_x = old_xy[0] + (speed*math.cos(angle/360*2*math.pi))
    new_y = old_xy[1] - (speed*math.sin(angle/360*2*math.pi))
    return new_x, new_y

def find_angle(pos1, angle1, pos2):
    angle1 = angle1 % 360
    if angle1 < 0:
        angle1 += 360
    dx=pos2[0] - pos1[0] 
    dy=pos2[1] - pos1[1]
    if dx == 0:
        if dy > 0:
            angle=90
        else:
            angle=-90
    else:
        angle=math.atan(dy/dx) / math.pi * 180 

    if dy < 0 and dx < 0:
        angle = 180 - angle

    if dy < 0 and dx > 0:
        angle = angle * -1

    if dy > 0 and dx < 0:
        angle = angle * -1 + 180

    if dy > 0 and dx > 0:
        angle = (90-angle) + 270

    res = (angle - angle1) % 360
    if res < 0 :
        res += 360
    

    return res


class SpriteRotate(pg.sprite.Sprite):
    def __init__(self, imageName, id, origin, pivot):
        super().__init__() 
        self.image = pg.image.load(f"./assets/{imageName}_{id}.png")
        self.original_image = self.image
        self.rect = self.image.get_rect(topleft = (origin[0]-pivot[0], origin[1]-pivot[1]))
        self.origin = origin
        self.pivot = pivot
      
    def update(self):
        self.origin = calculate_new_xy(self.origin, self.speed, self.angle)
        image_rect = self.original_image.get_rect(topleft = (self.origin[0] - self.pivot[0], self.origin[1]-self.pivot[1]))
        offset_center_to_pivot = pg.math.Vector2(self.origin) - image_rect.center
        rotated_offset = offset_center_to_pivot.rotate(-self.angle)
        rotated_image_center = (self.origin[0] - rotated_offset.x, self.origin[1] - rotated_offset.y)
        self.image = pg.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center = rotated_image_center)
  
class Submarine(SpriteRotate):
    def __init__(self, imageName, id, origin, pivot, keys, torpedos, submarines):
        super().__init__(imageName, id, origin, pivot) 
        self.angle = 0
        self.speed = 0
        self.acceleration = 0.15
        self.agility = 1
        self.id = id
        self.keys = keys
        self.torpedos = torpedos
        self.torpedo_reload = 1000
        self.torpedo_fired_last = 0
        self.submarines = submarines


    def process_keys(self, keys_pressed):
        if keys_pressed[self.keys[0]]:
            self.turn_left()
        if keys_pressed[self.keys[1]]:
            self.turn_right()
        if keys_pressed[self.keys[2]]:
            self.accelerate()
        if keys_pressed[self.keys[3]]:    
            self.deccelerate()
        if keys_pressed[self.keys[4]]:    
            self.launch_torpedo()

    def accelerate(self):
       self.speed = self.speed + self.acceleration
    
    def deccelerate(self):
       self.speed = self.speed - self.acceleration

    def turn_left(self):       
       self.speed = self.speed + self.acceleration * 0.05
       self.angle = self.angle + self.agility
  
    def turn_right(self):       
       self.speed = self.speed + self.acceleration * 0.05
       self.angle = self.angle - self.agility
       
    def update(self):
        self.speed = self.speed - self.speed * WATER_FRICTION
        super().update()
  
    def launch_torpedo(self):
        if self.torpedo_fired_last + self.torpedo_reload < pg.time.get_ticks():
            torpedo = Torpedo("torpedo", self.id, tuple(map(lambda i, j: i + j, self.origin, calculate_new_xy((0,0), 32, self.angle))), (32, 15), self.speed, self.angle, self.submarines)
            torpedo.find_nearest(self)
            self.torpedos.add(torpedo)
            self.torpedo_fired_last = pg.time.get_ticks()

 
class SubmarineGroup(pg.sprite.Group):
    def process_keys(self, keys_pressed):
        for sprite in self.spritedict:
           sprite.process_keys(keys_pressed)


class Torpedo(SpriteRotate):
    def __init__(self, imageName, id, origin, pivot, speed, angle, submarines):
        super().__init__(imageName, id, origin, pivot) 
        self.angle = angle
        self.speed = speed
        self.acceleration = 0.35
        self.agility = 5
        self.id = id
        self.submarines = submarines

    def accelerate(self):
       self.speed = self.speed + self.acceleration
    
    def turn_left(self):       
       self.speed = self.speed + self.acceleration * 0.05
       self.angle = self.angle + self.agility
  
    def turn_right(self):       
       self.speed = self.speed + self.acceleration * 0.05
       self.angle = self.angle - self.agility
       
    def find_nearest(self, source):
        enemies = self.submarines.copy()
        enemies.remove(source)
        self.target = min([e for e in enemies], key=lambda e: pow(e.origin[0]-source.origin[0], 2) + pow(e.origin[1]-source.origin[1], 2))        
        print(self.target.id)

    def navigate(self):
        if find_angle(self.origin, self.angle, self.target.origin) > 180:
            self.turn_right()
        else:
            self.turn_left()

    def update(self):
        self.accelerate()
        self.navigate()
        self.speed = self.speed - self.speed * WATER_FRICTION
        super().update()



pg.init()
 
fps = 60
fpsClock = pg.time.Clock()
 
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 1000
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

torpedo_sprites = pg.sprite.Group([]) 
player_sprites = SubmarineGroup([])

player_sprites.add(Submarine('submarine', 1, (64, 64), (55, 32), (pg.K_LEFT, pg.K_RIGHT, pg.K_UP, pg.K_DOWN, pg.K_m), torpedo_sprites, player_sprites))
player_sprites.add(Submarine('submarine', 2, (640, 640), (55, 32), (pg.K_a, pg.K_d, pg.K_w, pg.K_s, pg.K_q), torpedo_sprites, player_sprites))

# Game loop.
run = True
while run:
    screen.fill((0, 0, 0))
    
    for event in pg.event.get():
        if event.type == pg.QUIT:
            run = False
      
    #keys_pressed = pg.key.get_pressed()
    player_sprites.process_keys(pg.key.get_pressed() )

       
    # Update.
        
    player_sprites.update()
    torpedo_sprites.update()
    
    # Draw.
    player_sprites.draw(screen)
    torpedo_sprites.draw(screen)
    
    pg.display.flip() # Updates whole screen
    fpsClock.tick(fps)

pg.display.quit()
pg.quit()

