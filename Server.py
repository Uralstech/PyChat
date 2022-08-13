import socket
import hashlib
import threading
from os.path import isfile
from datetime import datetime
from os.path import join, abspath, dirname

class ChainedDataBlock:
    def __init__(self, previous_hash, raw_data):
        self.previous_hash = previous_hash
        self.raw_data = raw_data

        self.block_data = '-'.join((*raw_data, previous_hash))
        self.block_hash = self.makeHash()

    def makeHash(self):
        data = self.block_data

        _hash = hashlib.sha3_256(data.encode(), usedforsecurity=True).hexdigest()
        __hash = hashlib.sha3_256('-'.join((data, _hash)).encode(), usedforsecurity=True).hexdigest()
        ___hash = hashlib.sha3_256('-'.join((data, __hash, _hash)).encode(), usedforsecurity=True).hexdigest()
        return ___hash

HOST = socket.gethostbyname(socket.gethostname())
PORT = 9090
VERSION = '1.4.0' # DO NOT CHANGE
print(abspath(dirname(__file__)))
LOGFILE = join(abspath(dirname(__file__)), "Log.log")
USRFILE = join(abspath(dirname(__file__)), "PyChatusers.block")

if not isfile(USRFILE): file = open(USRFILE, 'x'); file.close()

userData = {}
with open(USRFILE, 'r') as file:
    data = file.read().split('\n')[:-1]

    if len(data) > 0:
        for i in data: userData[i.split()[0]] = i.split()[1]
usrnmeData = list(userData)

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
    
    currentTime = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    log = f"[{currentTime}] "
    if message[-1] == '\n': message = message[:-1]
    log += repr(message) + '\n'
    with open(LOGFILE, 'a') as file: file.write(log)
    print(log, end='')

def handle(client):
    while True:
        try:
            message = client.recv(1024).decode('utf-8')[:-1]
            cmd = message[len(usernames[clients.index(client)])+2:]

            if cmd != '':
                if cmd == r"\LOGS":
                    if LOGFILE != "":
                        with open(LOGFILE, 'r') as file:
                            client.send('\n'.join((r"[SERVER]: LOGS- (\t = tab-space, \n = new-line):", file.read())).encode('utf-8'))
                    else: client.send("[SERVER]: AN ERROR OCCURED WHILE TRYING TO RETRIEVE CHAT LOGS.".encode('utf-8'))
                elif cmd == r"\ONLINE":
                    msg = "[SERVER]: ONLINE-"
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
                        actualMessage = cmd[lastIndex:]
                        
                        rplcstr = ''.join(('\n', *[' ' for _ in range(len(clientName) + len(user) + 15)]))
                        actualMessage = str(actualMessage).replace('\n', rplcstr)

                        message = f"{clientName} whispers to {user}: {actualMessage}"

                        clients[index].send((message + '\n').encode('utf-8'))
                        client.send((message + '\n').encode('utf-8'))
                    else:
                        client.send("[SERVER]: UNKNOWN USER\n".encode('utf-8'))
                else:
                    rplcstr = ''.join(('\n', *[' ' for _ in range(len(usernames[clients.index(client)]) + 2)]))
                    message = str(message).replace('\n', rplcstr)
                    broadcast(message + '\n')
        except:
            index = clients.index(client)
            broadcast(f"[SERVER]: {usernames[index]} has left the chat.\n")

            clients.pop(index)
            usernames.pop(index)

            client.close()
            break

def receive():
    global userData
    global usrnmeData
    userData = userData
    usrnmeData = usrnmeData

    while True:
        client, address = server.accept()

        client.send("USRNME".encode('utf-8'))
        username = client.recv(1024).decode('utf-8')

        if username not in usernames:
            client.send(f"::SERVER::{VERSION}".encode('utf-8'))
            confirmation = client.recv(1024).decode('utf-8')
            if confirmation == "1":
                client.send("PASWRD".encode('utf-8'))
                password = client.recv(1024).decode('utf-8')

                base = None

                if username not in usrnmeData:
                    if len(usrnmeData) > 0: base = userData[usrnmeData[-1]]
                    else: base = "INIT"
                elif usrnmeData.index(username) == 0: base = "INIT"
                else: base = userData[usrnmeData[usrnmeData.index(username)-1]]

                password_hash = ChainedDataBlock(base, password).block_hash

                if username not in usrnmeData:
                    userData[username] = password_hash
                    usrnmeData = list(userData)
                    with open(USRFILE, 'a') as file: file.write(f"{username} {password_hash}\n")
                
                print(base, "    ", repr(password))
                print(password_hash)
                print(userData[username])
                if password_hash != userData[username]:
                    client.send("E001".encode('utf-8'))
                else:
                    usernames.append(username)
                    clients.append(client)
                    broadcast(f"[SERVER]: {username} has joined!\n")

                    thread = threading.Thread(target=handle, args=(client,))
                    thread.start()
        else:
            client.send("E000".encode('utf-8'))

print("Server online.")
receive()