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

        self.client = Client()
        received = self.client.join_game(PLAYER_RED, 'yash')
        data = received["data"]

        self.player = Player(PLAYER_RED, data['x'], data['y'], data['health'], data['name'], data['id'])
        print(received)
        print("self joined")


        self.run = True
        self.clock = pygame.Clock()
        self.camera = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.map_size_pixels = self.map.get_map_width_pixels()
        self.font = pygame.font.Font(None, 24)
        self.players = {}

        threading.Thread(target=self.receive_state, daemon=True).start()

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

    def receive_state(self):
        buffer = ""
        self.client.s.setblocking(False)
        while self.run:
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


    def loop(self):
        self.run = True

        while self.run:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_input()

            self.client.send_keys()

            self.player.update_anim(dt)
            
            for player in self.players.values():
                player.update_anim(dt)

            self.update_camera()

            self.screen.fill(COLOR_BLACK)

            self.map.render(self.screen, self.camera, list(self.players.values()) + [self.player])

            self.show_fps()

            pygame.display.flip()



    def show_fps(self):
        fps = int(self.clock.get_fps())       
        fps_text = self.font.render(f"FPS: {fps}", True, (255, 255, 0))
        self.screen.blit(fps_text, (10, 10)) 

    
        
