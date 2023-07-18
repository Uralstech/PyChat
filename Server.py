from socket import socket, gethostname, gethostbyname, AF_INET, SOCK_STREAM
from os.path import join, abspath, dirname, isfile
from json import load, dump, JSONDecodeError
from datetime import datetime
from threading import Thread
from hashlib import sha3_256

# HOST = loads(get("https://jsonip.com", headers={"Content-Type" : "application,json"}).text)["ip"]

class PyChatServer:
    __VERSION: str = "1.5.0"
    __INCIDENT_DATA_FILE: str = join(abspath(dirname(__file__)), "Incidents.log")
    __LOG_DATA_FILE: str = join(abspath(dirname(__file__)), "Log.log")
    __USER_DATA_FILE: str = join(abspath(dirname(__file__)), "PyChatUsers.block")

    def __init__(self) -> None:
        found_host_name: str = gethostname()
        default_port: int = 443

        host_name: str = input(f"Enter host name (press 'enter' key to use: {found_host_name}): ")
        self.host_ip: str = gethostbyname(host_name if host_name != '' else found_host_name)

        user_defined_port: str = input(f"Enter port to use (press 'enter' key to use: {default_port}): ")
        self.port: int = int(user_defined_port) if user_defined_port != '' else default_port

        print(f"HOST IP: {self.host_ip} | PORT: {self.port}")

        self.__get_user_file()
        self.__initialize_server()

    def __get_user_file(self) -> None:
        if not isfile(PyChatServer.__USER_DATA_FILE):
            with open(PyChatServer.__USER_DATA_FILE, "x", encoding="utf-8"):
                pass

        self.defined_users: dict[str] = {}
        with open(PyChatServer.__USER_DATA_FILE, encoding="utf-8") as file:
            try:
                self.defined_users: dict[str] = load(file)
            except JSONDecodeError:
                print("Error: Could not decode user data file.")

    def __initialize_server(self) -> None:
        self.server: socket = socket(AF_INET, SOCK_STREAM)
        self.server.bind((self.host_ip, self.port))
        self.server.listen()

        self.online_users: dict[str, socket] = {}
        print("Server online.")

    def __raw_broadcast(self, message: bytes) -> None:
        for user_socket in self.online_users.values():
            user_socket.send(message)

    def __log_message(self, message: str) -> None:
        log_entry: str = f"[{datetime.now().strftime('%d-%m-%Y %H:%M')}] {repr(message)}\n"

        with open(PyChatServer.__LOG_DATA_FILE, 'a', encoding="utf-8") as file:
            file.write(log_entry)
            print(log_entry, end='')

    def __message_broadcast(self, user_name: str, message: str) -> None:
        self.__log_message(f"{user_name}: {repr(message)}")
        self.__raw_broadcast(0x09.to_bytes() + f"{user_name}\u0000{message}".encode("utf-8"))
    
    def __remove_client(self, user_name: str) -> None:
        self.__raw_broadcast(0x04.to_bytes() + user_name.encode("utf-8"))
        self.__log_message(f"{user_name} left.")
        self.online_users.pop(user_name)

    def __handle(self, user_name: str, user_socket: socket) -> None:
        while True:
            try:
                received: bytes = user_socket.recv(1024)
                match int(received[0:1].hex(), 16):
                    case 0x00:
                        self.__remove_client(user_name)
                        break
                    case 0x02:
                        if PyChatServer.__LOG_DATA_FILE != '':
                            with open(PyChatServer.__LOG_DATA_FILE, encoding="utf-8") as file:
                                user_socket.send(0x05.to_bytes() + file.read().strip().encode("utf-8"))
                        else:
                            user_socket.send(0x0C.to_bytes())
                    case 0x03:
                        user_names: list[str] = list(self.online_users.keys())
                        user_names.remove(user_name)

                        user_socket.send(0x06.to_bytes() + "\u0000".join(user_names).encode("utf-8"))
                    case 0x04:
                        user_names: list[str] = list(self.defined_users.keys())
                        user_names.remove(user_name)

                        user_socket.send(0x07.to_bytes() + "\u0000".join(user_names).encode("utf-8"))
                    case 0x05:
                        user_to_send_to = received[1:].decode("utf-8").split("\u0000")[0]

                        if user_to_send_to not in self.online_users:
                            user_socket.send(0x0D.to_bytes())
                        else:
                            self.online_users[user_to_send_to].send(0x08.to_bytes() + received[1:])
                    case 0x09:
                        self.__message_broadcast(user_name, received[1:].decode("utf-8"))
            except Exception:
                self.__remove_client(user_name)
                break
    
    def __append_new_user(self, user_name: str, generated_hash: str) -> None:
        self.defined_users[user_name] = generated_hash
        with open(PyChatServer.__USER_DATA_FILE, 'w', encoding="utf-8") as file:
            dump(self.defined_users, file, indent=4)

    def __report_incident(self, description: str) -> None:
        incident_entry: str = f"[{datetime.now().strftime('%d-%m-%Y %H:%M')}] {description}\n"

        with open(PyChatServer.__INCIDENT_DATA_FILE, 'a', encoding="utf-8") as file:
            file.write(incident_entry)
            print(incident_entry, end='')

    def receive_users(self) -> None:
        while True:
            user_socket, address = self.server.accept()
            print(f"New connection at: {address}")

            user_name: str = ''
            try:
                user_socket.send(0x00.to_bytes() + PyChatServer.__VERSION.encode("utf-8"))
                match int(user_socket.recv(1).hex(), 16):
                    case 0x00:
                        while True:
                            user_socket.send(0x01.to_bytes())
                            user_data: bytes = user_socket.recv(1024)
                            if int(user_data[0:1].hex(), 16) == 0x01:
                                user_name_bytes, password_hash_bytes = user_data[1:].split(0x00.to_bytes())
                                user_name = user_name_bytes.decode("utf-8")
                                password_hash: str = password_hash_bytes.hex()
                            
                                if len(password_hash) == 64:
                                    if user_name not in self.online_users:
                                        base: str = ''
                                        user_exists: bool = True
                                        defined_user_names: list[str] = list(self.defined_users.keys())
                            
                                        if len(self.defined_users) > 0:
                                            if user_name not in self.defined_users:
                                                base = self.defined_users[defined_user_names[-1]]
                                                user_exists = False
                                            elif defined_user_names.index(user_name) > 0:
                                                base = self.defined_users[defined_user_names[defined_user_names.index(user_name)-1]]
                                        else:
                                            user_exists = False
                            
                                        sign_in_success: bool = True
                                        generated_hash: str = sha3_256((password_hash + base).encode("utf-8"), usedforsecurity=True).hexdigest()
                                        if user_exists:
                                            if generated_hash != self.defined_users[user_name]:
                                                self.__report_incident(f"Connection {address} tried to log into user '{user_name}' and failed: Incorrect password")
                                                sign_in_success = False
                            
                                                user_socket.send(0x0B.to_bytes())
                                        else:
                                            self.__append_new_user(user_name, generated_hash)
                            
                                        if sign_in_success:
                                            user_socket.send(0x14.to_bytes())
                                            Thread(target=self.__handle, args=(user_name, user_socket)).start()
                            
                                            self.online_users[user_name] = user_socket
                                            self.__raw_broadcast(0x03.to_bytes() + user_name.encode("utf-8"))
                                            self.__log_message(f"{user_name} joined.")
                                            break
                                    else:
                                        user_socket.send(0x0A.to_bytes())
                    case 0x0A:
                        self.__report_incident(f"Connection {address} tried to log in and failed: Differing versions")
            except Exception:
                if user_name in self.online_users:
                    self.__remove_client(user_name)
    
if __name__ == '__main__':
    PyChatServer().receive_users()