import socket
import json
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, font, messagebox

class ClientApp:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.current_room = None
        self.username = ""
        
        self.root = tk.Tk()
        self.root.title("Game Lobby")
        self.root.geometry("800x600")
        self.configure_styles()
        
        self.create_login_gui()
        self.root.mainloop()
    
    def configure_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Color scheme
        self.bg_color = "#2d2d2d"
        self.fg_color = "#ffffff"
        self.accent_color = "#7289da"
        self.secondary_color = "#40444b"
        
        # Configure styles
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        self.style.configure('TButton', background=self.secondary_color, foreground=self.fg_color,
                           borderwidth=1, focusthickness=3, focuscolor='none')
        self.style.map('TButton', 
                      background=[('active', self.accent_color), ('disabled', self.bg_color)])
        self.style.configure('TEntry', fieldbackground=self.secondary_color, foreground=self.fg_color)
        self.style.configure('Treeview', background=self.secondary_color, foreground=self.fg_color,
                           fieldbackground=self.secondary_color)
        self.style.configure('Treeview.Heading', background=self.accent_color, foreground=self.fg_color)
        self.style.configure('TScrollbar', background=self.secondary_color)
        self.style.configure('self_message.TLabel', foreground="#43b581")
    
    def create_login_gui(self):
        self.login_frame = ttk.Frame(self.root, padding=20)
        self.login_frame.pack(expand=True)
        
        login_container = ttk.Frame(self.login_frame)
        login_container.pack(pady=50)
        
        ttk.Label(login_container, text="🎮 Game Lobby", font=('Helvetica', 16, 'bold')).grid(row=0, columnspan=2, pady=20)
        
        ttk.Label(login_container, text="Username:").grid(row=1, column=0, pady=5)
        self.username_entry = ttk.Entry(login_container, width=25)
        self.username_entry.grid(row=1, column=1, pady=5)
        
        connect_btn = ttk.Button(login_container, text="Connect 🚀", command=self.connect_to_server)
        connect_btn.grid(row=2, columnspan=2, pady=15)
        self.username_entry.bind('<Return>', lambda e: connect_btn.invoke())
    
    def create_main_gui(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Chat Panel
        chat_frame = ttk.Frame(self.main_frame)
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.chat_area = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=('Arial', 10),
            bg=self.secondary_color,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            state='disabled'
        )
        self.chat_area.tag_configure('system', foreground="#7289da")
        self.chat_area.tag_configure('self_message', foreground="#43b581")
        self.chat_area.pack(fill=tk.BOTH, expand=True)
        
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.msg_entry = ttk.Entry(input_frame)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.msg_entry.bind("<Return>", lambda e: self.send_message())
        
        send_btn = ttk.Button(input_frame, text="Send ✉️", command=self.send_message)
        send_btn.pack(side=tk.RIGHT)
        
        # Room Panel
        room_frame = ttk.Frame(self.main_frame, width=250)
        room_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        ttk.Label(room_frame, text="🏠 Game Rooms", font=('Helvetica', 12, 'bold')).pack(pady=5)
        
        self.room_list = ttk.Treeview(
            room_frame,
            columns=('code', 'players'),
            show='headings',
            selectmode='browse',
            height=15
        )
        self.room_list.heading('code', text='Room Code')
        self.room_list.heading('players', text='Players')
        self.room_list.column('code', width=120)
        self.room_list.column('players', width=80)
        self.room_list.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = ttk.Frame(room_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Create Room ➕", command=self.create_room).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(btn_frame, text="Join Room 🔑", command=self.join_room).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(btn_frame, text="Refresh ♻️", command=self.refresh_rooms).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # Status Bar
        self.status_bar = ttk.Label(self.main_frame, text="Status: Connected ✅", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def connect_to_server(self):
        username = self.username_entry.get()
        if not username:
            messagebox.showerror("Error", "Please enter a username")
            return
            
        try:
            self.client.connect(('localhost', 5555))
            self.client.send(json.dumps({
                'type': 'login',
                'username': username
            }).encode('utf-8'))
            
            response = json.loads(self.client.recv(1024).decode('utf-8'))
            if response['type'] == 'system':
                self.username = username
                self.login_frame.destroy()
                self.create_main_gui()
                self.connected = True
                threading.Thread(target=self.receive_messages, daemon=True).start()
                self.refresh_rooms()
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
    
    def receive_messages(self):
        while self.connected:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message:
                    msg = json.loads(message)
                    self.root.after(0, self.handle_message, msg)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break
    
    def handle_message(self, msg):
        if msg['type'] == 'chat':
            self.chat_area.configure(state='normal')
            self.chat_area.insert(tk.END, msg['content'] + '\n')
            self.chat_area.configure(state='disabled')
            self.chat_area.see(tk.END)
        elif msg['type'] == 'system':
            self.chat_area.configure(state='normal')
            self.chat_area.insert(tk.END, f"🌟 System: {msg['content']}\n", 'system')
            self.chat_area.configure(state='disabled')
            self.chat_area.see(tk.END)
        elif msg['type'] == 'error':
            messagebox.showerror("Error", msg['content'])
        elif msg['type'] == 'room_update':
            self.update_room_list(msg['rooms'])
    
    def update_room_list(self, rooms):
        self.room_list.delete(*self.room_list.get_children())
        for code, info in rooms.items():
            self.room_list.insert('', 'end', values=(code, info['player_count']))
    
    def send_message(self):
        message = self.msg_entry.get()
        if not message:
            return
        
        # Display message locally first
        self.chat_area.configure(state='normal')
        self.chat_area.insert(tk.END, f"[You] {message}\n", 'self_message')
        self.chat_area.configure(state='disabled')
        self.chat_area.see(tk.END)
        
        # Send to server
        if message.startswith('/'):
            self.client.send(json.dumps({
                'type': 'command',
                'command': message
            }).encode('utf-8'))
        else:
            self.client.send(json.dumps({
                'type': 'chat',
                'content': message
            }).encode('utf-8'))
        self.msg_entry.delete(0, tk.END)
    
    def create_room(self):
        self.client.send(json.dumps({
            'type': 'command',
            'command': '/create_room'
        }).encode('utf-8'))
        self.refresh_rooms()
    
    def join_room(self):
        selected = self.room_list.selection()
        if selected:
            code = self.room_list.item(selected[0])['values'][0]
            self.client.send(json.dumps({
                'type': 'command',
                'command': f'/join_room {code}'
            }).encode('utf-8'))
    
    def refresh_rooms(self):
        self.client.send(json.dumps({
            'type': 'command',
            'command': '/list_rooms'
        }).encode('utf-8'))

if __name__ == "__main__":
    ClientApp()
