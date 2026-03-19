import pytmx
import pygame
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from settings import COLOR_WHITE, DEBUG


class Map:
    def __init__(self, path):
        self.tmx_data = pytmx.util_pygame.load_pygame(path)

    
        self.object_images = {}
        self.map_objects = []
        self.tile_cache = {}
        self.load_tile_images()
        self.load_map_objects()

        if (DEBUG):
            self.collision_objects = []
            self.load_collision_rects()




    def load_collision_rects(self):
        for layer in self.tmx_data.layers:
            # Only check object layers
            if isinstance(layer, pytmx.TiledObjectGroup) and layer.name == "collision":
                for obj in layer:
                    rect = pygame.Rect( obj.x,obj.y,getattr(obj, 'width', 0),getattr(obj, 'height', 0))
                    self.collision_objects.append(rect)
             

    def load_tile_images(self):
        for gid in range(self.tmx_data.maxgid):
            image = self.tmx_data.get_tile_image_by_gid(gid)
            if image:
                self.tile_cache[gid] = image


    def load_map_objects(self):
        for layer in self.tmx_data.layers:
                if layer.name == "objects":
                    for obj in layer:
                        if hasattr(obj, 'gid'):
                            image = self.tmx_data.get_tile_image_by_gid(obj.gid)
                            if image:
                                self.object_images[obj.gid] = image
                                self.map_objects.append(obj)


        self.map_objects =  sorted(self.map_objects, key = lambda x: x.y )



    def get_map_width_pixels(self):
        map_width_pixels = self.tmx_data.width * self.tmx_data.tilewidth
        map_height_pixels = self.tmx_data.height * self.tmx_data.tileheight
        return (map_width_pixels, map_height_pixels)
    
    
    def render(self, screen, camera, players, font):

        self.draw_layers(screen, camera)
        self.draw_objects(screen, camera, players)

        if (DEBUG):
            self.draw_collision_rect()

        self.draw_player_names(screen, camera, players, font)


        
    def draw_player_names(self, screen, camera, players, font):
        for p in players:
            name_text = font.render(p.name, True, COLOR_WHITE)
            screen.blit(name_text, (p.rect.x + p.rect.w // 2 - name_text.get_width() // 2 - camera.x, p.rect.y - 10 - camera.y))



    def draw_collision_rect(self, screen, camera):
        for rect in self.collision_objects:
            draw_rect = rect.copy()
            draw_rect.x = rect.x - camera.x
            draw_rect.y = rect.y -  camera.y
            pygame.draw.rect(screen, COLOR_WHITE, draw_rect, 2)

    
    def draw_layers(self, screen, camera):
        tw = self.tmx_data.tilewidth
        th = self.tmx_data.tileheight

        start_x = max(0, camera.x // tw)
        start_y = max(0, camera.y // th)

        end_x = min(self.tmx_data.width, (camera.x + camera.width) // tw + 1)
        end_y = min(self.tmx_data.height, (camera.y + camera.height) // th + 1)

        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for y in range(start_y, end_y):
                    for x in range(start_x, end_x):

                        gid = layer.data[y][x]
                        tile = tile = self.tile_cache.get(gid)
                        if tile:
                            screen.blit(tile, (x * tw - camera.x, y * th - camera.y))

        

    def draw_objects(self, screen, camera, players):
        camera_rect = pygame.Rect(camera.x, camera.y, camera.width, camera.height)
        renderables = []

        for obj in self.map_objects:
            if hasattr(obj, 'gid') and obj.gid in self.object_images:
                image = self.object_images[obj.gid]

                width = getattr(obj, 'width', image.get_width())
                height = getattr(obj, 'height', image.get_height())

                obj_rect = pygame.Rect(obj.x, obj.y, width, height)
                if not camera_rect.colliderect(obj_rect):
                    continue

                # Scale image once per frame if needed
                if width != image.get_width() or height != image.get_height():
                    image_to_draw = pygame.transform.scale(image, (int(width), int(height)))
                else:
                    image_to_draw = image

                renderables.append({
                    'image': image_to_draw,
                    'x': obj.x,
                    'y': obj.y,
                    'height': height
                })
        
        for player in players:
            renderables.append({
                'image': player.animations[player.current_animation].get_current_frame(),
                'x': player.rect.x,
                'y': player.rect.y,
                'height': player.rect.height
            })


        renderables.sort(key=lambda r: r['y'] + r['height'])

     
        for r in renderables:
            screen.blit(r['image'], (r['x'] - camera.x, r['y'] - camera.y))