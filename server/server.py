import socket             
import json
from random import randint
import threading
import time
import sys
import os
import xml.etree.ElementTree as ET
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from settings import TILE_SIZE, MAP_SIZE, PLAYER_SPEED, SERVER_PORT, SERVER_URL, MAX_PACKET_SIZE, TICK_DELAY, MAP_FILE_PATH, PLAYER_SIZE, DEBUG
import traceback
import pygame

class Server:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print ("Socket successfully created")
        self.s.bind((SERVER_URL, SERVER_PORT))    
        self.s.settimeout(0.01) 
        self.s.listen(5)
        print (f"server started on {SERVER_URL}:{SERVER_PORT}")
        self.players = {}
        self.sockets = {}
        self.count = 0
        self.last_broadcast = 0
        self.lock = threading.Lock()
        self.map_collision_rects = []
        self.load_map_collision_rects()
        if DEBUG:
            for r in self.map_collision_rects:
                print(r)
        
        
        
    def load_map_collision_rects(self):
        tree = ET.parse(MAP_FILE_PATH)
        root = tree.getroot()

        collision_layer = None

        for objectgroup in root.findall('objectgroup'):
            if objectgroup.attrib.get("name") == "collision":
                collision_layer = objectgroup
                break

        if collision_layer is None:
            print("No collision layer found!")
        else:
            for obj in collision_layer.findall("object"):
                x = float(obj.attrib.get('x'))
                y = float(obj.attrib.get('y'))
                width = float(obj.attrib.get('width', 0))  # width may be missing
                height = float(obj.attrib.get('height', 0))  # height may be missing
                self.map_collision_rects.append(pygame.Rect(x, y, width, height))

    def get_state_dict(self):
        with self.lock:
            state = {}
            for player in self.players.values():
                state[player['id']] = {"id": player['id'], "x":player['x'], "y":player['y'], "health":player['health']}
    
            return state



    def broadcast_state(self):
        packet = {"type": "players_state", "data":self.get_state_dict()}
        self.broadcast(packet)

    def broadcast(self, message):
        packet = json.dumps(message) + "\n"
        packet = packet.encode()
        dead = [] # for cleaning dead sockets
        for pid, s in self.sockets.items():
            try:
                s.send(packet)
            except:
                dead.append(pid)
        
        for pid in dead:
            del self.sockets[pid]
            print(f"pid {pid} removed")
            if pid in self.players:
                del self.players[pid]

    def handle_client(self, conn, addr, player_id):
        print(f"player connected {player_id}")
        buffer = ""
        try:
            while True:
                data = conn.recv(MAX_PACKET_SIZE).decode()

                if not data:
                    break
                    
                buffer += data

                while "\n" in buffer:
                    raw, buffer = buffer.split("\n", 1)
                    try:
                        packet = json.loads(raw)
                    except:
                        continue

                    if packet["type"] == "input":
                        dx = packet['dx']
                        dy = packet['dy']

                        length = (dx*dx + dy*dy) ** 0.5
                        if length > 0:
                            dx /= length
                            dy /= length

                        with self.lock:
                            old_x = self.players[player_id]['x']
                            old_y = self.players[player_id]['y']

                            new_x = old_x + dx * PLAYER_SPEED
                            new_y = old_y + dy * PLAYER_SPEED

                            # new_rect = pygame.Rect(new_x, new_y + PLAYER_SIZE // 2, PLAYER_SIZE, PLAYER_SIZE // 2)
                            new_rect = pygame.Rect(new_x, new_y , PLAYER_SIZE, PLAYER_SIZE)

         
                            if any(new_rect.colliderect(r) for r in self.map_collision_rects):
                                # Collision: do not move
                                self.players[player_id]['x'] = old_x
                                self.players[player_id]['y'] = old_y
                            else:

                                self.players[player_id]['x'] = new_x
                                self.players[player_id]['y'] = new_y
                        

  
            
        except Exception as e:
            print("Client error:", e)
            traceback.print_exc()
        finally:
            print("Player disconnected:", addr)
            if player_id in self.players:
                del self.players[player_id]
            if player_id in self.sockets:
                del self.sockets[player_id]

            conn.close()

    def add_player(self, c, addr):
        print ('Got connection from', addr )

        received = c.recv(MAX_PACKET_SIZE).decode()
        packet = json.loads(received)

        player_id = self.count
        self.count += 1

        self.players[player_id] = {'id': player_id, **packet, "x":randint(0, MAP_SIZE * TILE_SIZE), 'y':randint(0, MAP_SIZE * TILE_SIZE), 'health':100}
        self.sockets[player_id] = c
        
        join_packet = {"type": "you_join", "data": self.players[player_id]} 


        c.send((json.dumps(join_packet) + "\n").encode())

        join_packet["type"] = "player_join"

        self.broadcast(join_packet)

        others_packet = {"type": "other_players_state", "data": self.players}

        c.send((json.dumps(others_packet) + "\n").encode())

        thread = threading.Thread(
            target=self.handle_client,
            args=(c, addr, player_id),
            daemon=True
        )
        thread.start()




    def loop(self):
        self.start_broadcast_loop()
        try:
            while True:
                try:
                    c, addr = self.s.accept()
                    self.add_player(c, addr)
                except BlockingIOError:
                    pass
                except socket.timeout:
                    pass


        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.s.close()

    def broadcast_loop(self):
        while True:
            now = time.time()
            if now - self.last_broadcast >= TICK_DELAY:
                self.broadcast_state()
    
                self.last_broadcast = now
                time.sleep(TICK_DELAY)

    def start_broadcast_loop(self):
        thread = threading.Thread(
            target=self.broadcast_loop,
            daemon=True
        )
        thread.start()

if __name__ == '__main__':
    server = Server()
    server.loop()

