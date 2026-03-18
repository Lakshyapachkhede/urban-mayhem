# Import socket module 
import socket             
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from settings import SERVER_URL, SERVER_PORT, MAX_PACKET_SIZE, NETWORK_FREQUENCY
import pygame


class Client:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((SERVER_URL, SERVER_PORT))
        self.frequency = 1 / NETWORK_FREQUENCY


    def send_packet(self, message):
        packet = json.dumps(message) + "\n"
        self.s.send(packet.encode())

    def receive_packet(self):
        return json.loads(self.s.recv(MAX_PACKET_SIZE).decode())

    def join_game(self, player_color, name):
        join_packet = {"type":"join", "name":name, "player_color": player_color}
        self.send_packet(join_packet)

        return self.receive_packet()
    

    def send_keys(self):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        
        input_packet = {"dx": dx, "dy":dy, "type":"input"}
        self.send_packet(input_packet)

    def update(self):
        self.send_keys()
        data = self.receive_packet()
        return data



