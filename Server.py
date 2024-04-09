import socket
import threading

class ChatServer:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 5555
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}
        self.channels = {}
        self.running = False

    def start(self):
        while True:
            try:
                self.server_socket.bind((self.host, self.port))
                break  # Exit loop if binding is successful
            except OSError as e:
                print("Error binding server socket:", e)
                choice = input("Enter 'retry' to enter IP address again or 'exit' to close the server: ")
                if choice.lower() == 'exit':
                    self.close()
                    return
                elif choice.lower() != 'retry':
                    continue
                self.host = input("Enter server IP address: ")

        self.server_socket.listen()
        print("Server is listening for connections...")
        self.running = True

        # Start a thread to listen for server shutdown command
        threading.Thread(target=self.check_shutdown).start()

        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"New connection from {client_address}")
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            except OSError as e:
                if self.running:
                    print("Error accepting connection:", e)
                    break

    def check_shutdown(self):
        while True:
            command = input("Type 'exit' to close the server: ")
            if command.lower() == 'exit':
                self.close()
                break

    def handle_client(self, client_socket):
        nickname = client_socket.recv(1024).decode()
        self.clients[nickname] = client_socket
        self.broadcast_message(f"{nickname} has joined the chat.", sender="Server")

        while True:
            try:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                if message.startswith("/create "):
                    self.create_channel(message, client_socket)
                elif message.startswith("/invite "):
                    self.invite_to_channel(message, client_socket)
                elif message.startswith("/join "):
                    self.join_channel(message, client_socket)
                elif message.startswith("/exit "):
                    self.exit_channel(message, client_socket)
                    break  # Exit loop for handling client messages
                elif message.startswith("/private "):
                    self.send_private_message(message, client_socket)
                else:
                    self.handle_message(message, nickname, client_socket)
            except ConnectionResetError:
                print(f"{nickname} disconnected.")
                del self.clients[nickname]
                self.broadcast_message(f"{nickname} has left the chat.", sender="Server")
                break

    def create_channel(self, message, client_socket):
        _, channel_name = message.split()
        if channel_name not in self.channels:
            self.channels[channel_name] = [client_socket]
            self.send_message(client_socket, f"Channel '{channel_name}' created successfully.")
        else:
            self.send_message(client_socket, f"Channel '{channel_name}' already exists.")

    def invite_to_channel(self, message, client_socket):
        _, channel_name, invitee = message.split()
        if channel_name in self.channels:
            if invitee in self.clients:
                self.channels[channel_name].append(self.clients[invitee])
                self.send_message(client_socket, f"Invitation sent to {invitee} for channel '{channel_name}'.")
                self.send_message(self.clients[invitee], f"You've been invited to join channel '{channel_name}'.")
            else:
                self.send_message(client_socket, f"User '{invitee}' not found.")
        else:
            self.send_message(client_socket, f"Channel '{channel_name}' does not exist.")

    def join_channel(self, message, client_socket):
        _, channel_name = message.split()
        if channel_name in self.channels:
            self.channels[channel_name].append(client_socket)
            self.send_message(client_socket, f"Joined channel '{channel_name}' successfully.")
        else:
            self.send_message(client_socket, f"Channel '{channel_name}' does not exist.")

    def handle_message(self, message, sender, client_socket):
        print(f"{sender}: {message}")
        in_channel = False
        for channel, members in self.channels.items():
            if client_socket in members:
                in_channel = True
                for member_socket in members:
                    if member_socket != client_socket:
                        self.send_message(member_socket, f"{sender}: {message}")
                break

        if not in_channel:
            self.broadcast_message(f"{sender}: {message}")

    def exit_channel(self, message, client_socket):
        _, channel_name = message.split()
        if channel_name in self.channels:
            if client_socket in self.channels[channel_name]:
                self.channels[channel_name].remove(client_socket)
                self.send_message(client_socket, f"Exited channel '{channel_name}' successfully.")
            else:
                self.send_message(client_socket, f"You're not in channel '{channel_name}'.")
        else:
            self.send_message(client_socket, f"Channel '{channel_name}' does not exist.")

    def send_private_message(self, message, client_socket):
        _, recipient, private_message = message.split(maxsplit=2)
        if recipient in self.clients:
            self.send_message(self.clients[recipient], f"(Private) {client_socket.getpeername()}: {private_message}")
        else:
            self.send_message(client_socket, f"User '{recipient}' not found.")

    def broadcast_message(self, message, sender=None):
        for client_socket in self.clients.values():
            if sender is None or client_socket != sender:
                self.send_message(client_socket, message)

    def send_message(self, client_socket, message):
        client_socket.sendall(message.encode())

    def close(self):
        print("Closing server...")
        self.running = False
        for client_socket in self.clients.values():
            client_socket.close()
        self.server_socket.close()

if __name__ == "__main__":
    server = ChatServer()
    server.start()
