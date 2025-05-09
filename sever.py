import socket
import threading
import random
import string
import json
from datetime import datetime

class Room:
    def __init__(self, code):
        self.code = code
        self.players = []
        self.created_at = datetime.now()

class Server:
    def __init__(self, host='0.0.0.0', port=5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()
        
        self.clients = {}
        self.rooms = {}
        self.lock = threading.Lock()
        
        print(f"Server listening on {host}:{port}")
        self.accept_connections()

    def generate_room_code(self):
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(random.choice(chars) for _ in range(6))
            if code not in self.rooms:
                return code

    def broadcast(self, message, room_code=None, sender=None):
        targets = []
        if room_code:
            targets = self.rooms[room_code].players
        else:
            targets = self.clients.values()
        
        for client in targets:
            if client != sender:
                try:
                    client.send(message.encode('utf-8'))
                except:
                    pass

    def update_room_lists(self):
        room_data = {code: {'player_count': len(room.players)} 
                   for code, room in self.rooms.items()}
        update_msg = json.dumps({'type': 'room_update', 'rooms': room_data})
        self.broadcast(update_msg)

    def handle_client(self, conn, addr):
        username = None
        current_room = None
        
        try:
            while True:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break

                msg = json.loads(data)
                
                if msg['type'] == 'login':
                    username = msg['username']
                    with self.lock:
                        self.clients[conn] = {'username': username, 'status': 'online'}
                    conn.send(json.dumps({'type': 'system', 'content': 'Login successful'}).encode('utf-8'))
                    self.update_room_lists()
                
                elif msg['type'] == 'chat':
                    content = f"[{username}] {msg['content']}"
                    self.broadcast(json.dumps({
                        'type': 'chat',
                        'content': content
                    }), room_code=current_room, sender=conn)
                
                elif msg['type'] == 'command':
                    if msg['command'] == '/create_room':
                        code = self.generate_room_code()
                        with self.lock:
                            self.rooms[code] = Room(code)
                            current_room = code
                            self.rooms[code].players.append(conn)
                            self.clients[conn]['status'] = 'in-game'
                        conn.send(json.dumps({
                            'type': 'system',
                            'content': f'Room created! Code: {code}'
                        }).encode('utf-8'))
                        self.update_room_lists()
                    
                    elif msg['command'].startswith('/join_room'):
                        code = msg['command'].split()[1]
                        if code in self.rooms:
                            with self.lock:
                                self.rooms[code].players.append(conn)
                                current_room = code
                                self.clients[conn]['status'] = 'in-game'
                            conn.send(json.dumps({
                                'type': 'system',
                                'content': f'Joined room {code}'
                            }).encode('utf-8'))
                            self.broadcast(json.dumps({
                                'type': 'system',
                                'content': f'{username} joined the room'
                            }), room_code=code, sender=conn)
                            self.update_room_lists()
                        else:
                            conn.send(json.dumps({
                                'type': 'error',
                                'content': 'Invalid room code'
                            }).encode('utf-8'))
                    
                    elif msg['command'] == '/list_rooms':
                        room_data = {code: {'player_count': len(room.players)} 
                                   for code, room in self.rooms.items()}
                        conn.send(json.dumps({
                            'type': 'room_update',
                            'rooms': room_data
                        }).encode('utf-8'))
        
        except Exception as e:
            print(f"Error: {e}")
        finally:
            with self.lock:
                if conn in self.clients:
                    del self.clients[conn]
                if current_room and current_room in self.rooms:
                    self.rooms[current_room].players.remove(conn)
                    self.update_room_lists()
            conn.close()

    def accept_connections(self):
        while True:
            conn, addr = self.server.accept()
            thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            thread.start()

if __name__ == "__main__":
    Server()
