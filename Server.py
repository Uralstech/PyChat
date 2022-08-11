from dataclasses import replace
import socket
import threading
from datetime import datetime

HOST = "127.0.0.1" # Get public IP with command 'ipconfig' on Windows
PORT = 9090
LOGFILE = r"C:\Users\asus\Desktop\PyChat\Log.log"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

server.listen()

clients = []
usernames = []

def broadcast(message):
    for client in clients:
        try: client.send(message.encode('utf-8'))
        except: pass

def handle(client):
    while True:
        try:
            message = client.recv(1024).decode('utf-8')[:-1]
            cmd = message[len(usernames[clients.index(client)])+2:]
            currentTime = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            log = f"[{currentTime}] {repr(message)}"
            print(log)

            if cmd != '':
                if cmd == r"\LOGS":
                    if LOGFILE != "":
                        with open(LOGFILE, 'r') as file:
                            client.send('\n'.join((r"__SERVER__: LOGS- (\t = tab-space, \n = new-line):", file.read())).encode('utf-8'))
                    else: client.send("__SERVER__: AN ERROR OCCURED WHILE TRYING TO RETRIEVE CHAT LOGS.".encode('utf-8'))
                elif cmd == r"\ONLINE":
                    msg = "__SERVER__: ONLINE-"
                    for i in range(len(usernames)): msg = '\n'.join((msg, f"{i}: {usernames[i]}"))
                    client.send((msg + '\n').encode('utf-8'))
                else:
                    if LOGFILE != "":
                        with open(LOGFILE, 'a') as file:
                            file.write(log + '\n')

                    broadcast(message + '\n')
        except:
            index = clients.index(client)
            broadcast(f"{usernames[index]} has left the chat.\n")

            clients.pop(index)
            usernames.pop(index)

            client.close()
            break

def receive():
    while True:
        client, address = server.accept()

        client.send("USRNME".encode('utf-8'))
        username = client.recv(1024)

        usernames.append(username)
        clients.append(client)
        broadcast(f"{username} has joined!\n")

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

print("Server online.")
receive()