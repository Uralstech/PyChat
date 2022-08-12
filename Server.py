import cmd
import socket
import threading
from datetime import datetime
from os import environ

HOST = socket.gethostbyname(socket.gethostname())
PORT = 9090
LOGFILE = environ["HOMEPATH"] + r"\Desktop\PyChat\Log.log" # Replace with path to log file

print(HOST)

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
                elif cmd.startswith("\\DM\\"):
                    user = ""
                    lastIndex = 0
                    for i in range(4, len(cmd[4:])):
                        if cmd[i] != '\\': user += cmd[i]
                        else: lastIndex = i + 1;  break

                    if user in usernames:
                        index = usernames.index(user)
                        clientName = usernames[clients.index(client)]
                        message = f"{clientName} whispers to {user}: {cmd[lastIndex:]}"

                        log = f"[{currentTime}] {repr(message)}"
                        with open(LOGFILE, 'a') as file: file.write(log + '\n')
                        print(log)

                        clients[index].send((message + '\n').encode('utf-8'))
                        client.send((message + '\n').encode('utf-8'))
                    else:
                        client.send("__SERVER__: UNKNOWN USER\n".encode('utf-8'))
                else:
                    with open(LOGFILE, 'a') as file: file.write(log + '\n')
                    print(log)

                    broadcast(message + '\n')
        except:
            index = clients.index(client)
            broadcast(f"__SERVER__: {usernames[index]} has left the chat.\n")

            clients.pop(index)
            usernames.pop(index)

            client.close()
            break

def receive():
    while True:
        client, address = server.accept()

        client.send("USRNME".encode('utf-8'))
        username = client.recv(1024).decode('utf-8')
        legal = True
        for i in username:
            if i in " \n\t\r\a\f\v\b\\": legal = False

        if username not in usernames and legal and len(username) > 0 and username != "__SERVER__":
            usernames.append(username)
            clients.append(client)
            broadcast(f"__SERVER__: {username} has joined!\n")

            thread = threading.Thread(target=handle, args=(client,))
            thread.start()
        else:
            client.send("E000".encode('utf-8'))

print("Server online.")
receive()