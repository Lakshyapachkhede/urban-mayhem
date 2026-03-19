import pygame
from map import Map
from player import Player
import sys
import os
import threading

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from settings import *
from client import Client
import json
import time

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_NAME)
        self.map = Map(MAP_FILE_PATH)

        self.state = GAME_STATE_START

    
        self.run = True
        self.clock = pygame.Clock()
        self.camera = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.map_size_pixels = self.map.get_map_width_pixels()

    
        self.font_small = pygame.font.Font(FONT_PATH, 8)
        self.font_medium = pygame.font.Font(FONT_PATH, 16)
        self.font_large = pygame.font.Font(FONT_PATH, 30)

        self.players = {}

        # start screen
        self.player_types = []
        self.load_player_types()
        self.player_types_rects = []
        self.player_types_positions = [
            pygame.Rect(
                    i * PLAYER_SIZE*2 + (SCREEN_WIDTH - (NUM_PLAYER_TYPES * PLAYER_SIZE*2)) // 2, 
                    200,  # y-position
                    PLAYER_SIZE * 2, 
                    PLAYER_SIZE * 2
                    )
            for i in range(NUM_PLAYER_TYPES)
        ]
    
        self.name = ""
        self.selected_player_type = None
        self.start_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - SCREEN_WIDTH // 8, 400, SCREEN_WIDTH // 4, 50)

        
    def update_camera(self):
        self.camera.centerx = max(
            SCREEN_WIDTH // 2,
            min(self.player.rect.centerx, self.map_size_pixels[0] - SCREEN_WIDTH // 2)
        )

        self.camera.centery = max(
            SCREEN_HEIGHT // 2,
            min(self.player.rect.centery, self.map_size_pixels[1] - SCREEN_HEIGHT // 2)
        )

    def handle_input(self):
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                self.run = False
                return

            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.run = False
                return
            
            if self.state == GAME_STATE_START and e.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = e.pos
                for idx, rect in enumerate(self.player_types_positions):
                    if rect.collidepoint(mouse_pos):
                        self.selected_player_type = idx
                        print (idx)
                        return
                if self.start_button_rect.collidepoint(mouse_pos):
                    if self.name.strip() != "" and self.selected_player_type != None:
                        self.start_game(self.selected_player_type, self.name)

                    
            if self.state == GAME_STATE_START and e.type == pygame.KEYDOWN:
                if e.key == pygame.K_BACKSPACE:
                    self.name = self.name[:-1]
                else:
                    if len(self.name) < 10:
                        self.name += e.unicode

                       


    def receive_state(self):
        buffer = ""
        self.client.s.setblocking(False)
        while self.run and self.state == GAME_STATE_LOOP:
            try:
                buffer += self.client.s.recv(MAX_PACKET_SIZE).decode()
                while "\n" in buffer:
                    received, buffer = buffer.split("\n", 1)
                    packet = json.loads(received)
                    self.process_packet(packet)
            except BlockingIOError:
                pass
            time.sleep(0.001)
            
        
    def process_packet(self, packet):
        data = packet["data"]

        if packet['type'] == 'player_join':
            if(data['id'] != self.player.id):
                self.players[int(data['id'])] = Player(data['player_color'], data['x'], data['y'], data['health'], data['name'], data['id'])
                print("player joined")


        elif packet['type'] == "players_state":
            
            for player in data.values():
                
                if int(player["id"]) == self.player.id:
                    self.player.move_to(player['x'], player['y'])
                    self.player.health = player['health']
         
                else:
                    if player['id'] not in self.players:
                        continue
                    self.players[int(player["id"])].move_to(player['x'], player['y'])
                    self.players[int(player["id"])].health = player['health']
        
        elif packet['type'] == "other_players_state":
            for player in data.values():
                if(player['id'] != self.player.id):
                    self.players[player['id']] = Player(player['player_color'], player['x'], player['y'], player['health'], player['name'], player['id'])


    def load_player_types(self):
        sprite_sheet = pygame.image.load(PLAYER_FILE_PATH).convert_alpha()
        for i in range(NUM_PLAYER_TYPES):
            rect = pygame.Rect(i * PLAYER_SIZE, 0, PLAYER_SIZE, PLAYER_SIZE)
            image = sprite_sheet.subsurface(rect)
            image = pygame.transform.scale(image, (2 * PLAYER_SIZE, 2 * PLAYER_SIZE))
            self.player_types.append(image)

        
    def start_game(self, player_type, name):
        self.client = Client()

        received = self.client.join_game(player_type, name)
        data = received["data"]

        self.player = Player(player_type, data['x'], data['y'], data['health'], data['name'], data['id'])
        print(received)
        print("self joined")

        self.state = GAME_STATE_LOOP
        threading.Thread(target=self.receive_state, daemon=True).start()
        return


    def game_state_start(self):
        self.screen.fill(COLOR_BLACK)

        self.show_text_x_center(GAME_NAME, self.font_large, 100, COLOR_MAGENTA)
        self.show_text_x_center("select player", self.font_small, 185, COLOR_YELLOW)
        for i, sprite in enumerate(self.player_types):
            rect = self.player_types_positions[i]
            self.screen.blit(sprite, rect) 
            mouse_pos = pygame.mouse.get_pos()
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, COLOR_WHITE, rect, 2, 5)

            if self.selected_player_type != None:
                pygame.draw.rect(self.screen, COLOR_GREEN, self.player_types_positions[self.selected_player_type], 2, 5)

            
        
        self.show_text_x_center("Enter your name", self.font_small, 280, COLOR_YELLOW)
        pygame.draw.rect(self.screen, COLOR_WHITE, (SCREEN_WIDTH // 4, 295, SCREEN_WIDTH // 2, 50), 2, 5)
        self.show_text_x_center(self.name, self.font_medium, 310, COLOR_ORANGE)


        pygame.draw.rect(self.screen, COLOR_WHITE, self.start_button_rect, 2, 5)
        self.show_text_x_center("start", self.font_medium, 415, COLOR_GREEN)





    def game_state_loop(self):
        dt = self.clock.tick(FPS) / 1000.0
    
        self.client.send_keys()

        self.player.update_anim(dt)
        
        for player in self.players.values():
            player.update_anim(dt)

        self.update_camera()

        self.screen.fill(COLOR_BLACK)

        self.map.render(self.screen, self.camera, list(self.players.values()) + [self.player], self.font_small)

    def game_state_pause(self):
        pass
    def game_state_result(self):
        pass

    def loop(self):
        self.run = True

        while self.run:
            self.handle_input()

            if self.state == GAME_STATE_START:
                self.game_state_start()
            elif self.state == GAME_STATE_LOOP:
                self.game_state_loop()
            else:
                print("your phone ringing")
                



            self.show_fps()
            pygame.display.flip()



    def show_fps(self):
        fps = int(self.clock.get_fps())       
        fps_text = self.font_medium.render(f"FPS: {fps}", True, (255, 255, 0))
        self.screen.blit(fps_text, (10, 10)) 

    def show_text_x_center(self, text, font, y, color, show_border=False):
        text = font.render(text, True, color)
        x = (SCREEN_WIDTH // 2) - text.get_width()//2
        rect = pygame.rect.Rect(x, y, text.get_width(), text.get_height())
        self.screen.blit(text, rect)
        if show_border:
            pygame.draw.rect(self.screen, COLOR_WHITE, rect, 2, 5)


    
        
