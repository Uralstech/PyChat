from tkinter import *
from tkinter.messagebox import showerror, askretrycancel
from tkinter.scrolledtext import ScrolledText

import sys
from threading import Thread
from hashlib import sha3_256
from dataclasses import asdict
from json import dump, load, JSONDecodeError
from os.path import join, abspath, dirname, isfile
from socket import socket, AF_INET, SOCK_STREAM
from Common import PyChatConfigStatus, PyChatConfig, PyChatConfigs
from Dialogs import PyChatSignInDialog, PyChatConfigChoosingDialog, PyChatConfigCreateDialog

PATH = abspath(dirname(__file__))
CONFIG_PATH = join(PATH, "PyChatConfigs.json")
VERSION = '1.5.0'

class PyChatConfigManager():
    @staticmethod
    def get_pychat_configs() -> tuple[PyChatConfigs | None, PyChatConfigStatus]:
        configs: PyChatConfigs | None = None

        try:
            with open(CONFIG_PATH, encoding="utf-8") as file:
                data: dict = load(file)
                configs: PyChatConfigs = PyChatConfigs({}, data["most_recent"])
                for config in data["configs"].keys():
                    configs.configs[config] = PyChatConfig(**(data["configs"][config]))
        except IOError:
            return None, PyChatConfigStatus.IO_ERROR
        except JSONDecodeError:
            return None, PyChatConfigStatus.JSON_ERROR
        return configs, PyChatConfigStatus.SUCCESS
    
    @staticmethod
    def add_pychat_config(configs: PyChatConfigs, config: PyChatConfig, overwrite: bool = False) -> tuple[PyChatConfigs | None, PyChatConfigStatus]:
        if configs.configs.get(config.name) != None and not overwrite:
            return None, PyChatConfigStatus.ALREADY_EXISTS
        
        configs.configs[config.name] = config
        configs.most_recent = config.name

        try:
            with open(CONFIG_PATH, "w" if isfile(CONFIG_PATH) else "x") as file:
                dump(asdict(configs), file, indent=4)
        except IOError:
            return None, PyChatConfigStatus.IO_ERROR
        return configs, PyChatConfigStatus.SUCCESS
    
    @staticmethod
    def write_pychat_configs(configs: PyChatConfigs) -> PyChatConfigStatus:
        try:
            with open(CONFIG_PATH, "w" if isfile(CONFIG_PATH) else "x") as file:
                dump(asdict(configs), file, indent=4)
        except IOError:
            return PyChatConfigStatus.IO_ERROR
        return PyChatConfigStatus.SUCCESS

class PyChatClient:
    def __init__(self) -> None:
        self.root: Tk | None = None
        self.message_backlog: str = ''
        self.__select_server()

    def __select_server(self) -> None:
        root: Tk = Tk()
        root.withdraw()

        create_new: bool = False
        configs: PyChatConfigs | None = None
        if isfile(CONFIG_PATH):
            configs, status = PyChatConfigManager.get_pychat_configs()
            if status == PyChatConfigStatus.IO_ERROR:
                if askretrycancel("PyChat", "Could not read configs."):
                    return self.__select_server()
                else:
                    return
            elif status == PyChatConfigStatus.JSON_ERROR:
                if askretrycancel("PyChat", "Could not decode configs."):
                    return self.__select_server()
                else:
                    return

            config_choose_dialog: PyChatConfigChoosingDialog = PyChatConfigChoosingDialog(root, configs, "PyChat: Servers")
            if config_choose_dialog.create_new:
                create_new: bool = config_choose_dialog.create_new
            elif config_choose_dialog.selected != None:
                self.config = config_choose_dialog.selected
                configs.most_recent = self.config.name
                PyChatConfigManager.write_pychat_configs(configs)
            else:
                return self.__select_server()
        else:
            create_new: bool = True
        
        if create_new:
            config_create_dialog: PyChatConfigCreateDialog = PyChatConfigCreateDialog(root, "PyChat: Add Server")
            if config_create_dialog.new_config != None:
                if configs != None:
                    configs, status = PyChatConfigManager.add_pychat_config(configs, config_create_dialog.new_config, config_create_dialog.overwrite)
                else:
                    configs: PyChatConfigs = PyChatConfigs({config_create_dialog.new_config.name : config_create_dialog.new_config}, config_create_dialog.new_config.name)
                    status: PyChatConfigStatus = PyChatConfigManager.write_pychat_configs(configs)
                
                if configs != None:
                    self.config = configs.configs.get(configs.most_recent)

                if status == PyChatConfigStatus.IO_ERROR:
                    if askretrycancel("PyChat", "Could not write configs."):
                        return self.__select_server()
                    else:
                        return
                elif status == PyChatConfigStatus.ALREADY_EXISTS:
                    showerror("PyChat", "Another config with the same name exists and the 'overwrite' option was not selected.")
                    return self.__select_server()
            else:
                return self.__select_server()
        self.__connect()
    
    def __connect(self) -> None:
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.settimeout(self.config.timeout)

        try:
            self.sock.connect((self.config.host_ip, self.config.port))
        except Exception:
            if askretrycancel("PyChat", f"Could not connect to server!"):
                return self.__connect()
            else:
                return self.sock.close()
        
        self.sock.settimeout(None)
        self.__listen()

    def __sign_in(self) -> None:
        root: Tk = Tk()
        root.withdraw()

        sign_in_dialog: PyChatSignInDialog = PyChatSignInDialog(root, "PyChat: Sign In")
        if sign_in_dialog.username.strip() == '':
            showerror("PyChat", "Invalid username.")
            return self.__sign_in()

        self.username, self.password = sign_in_dialog.username, sha3_256(sign_in_dialog.password.encode("utf-8"), usedforsecurity=True).digest()
        root.destroy()
    
    def __gui_loop(self) -> None:
        self.root = Tk()
        self.root.title("PyChat")

        self.textArea = ScrolledText(self.root, font=("Cascadia Code", 10))
        self.textArea.pack(padx=10, pady=10, fill='both', expand=1)
        self.textArea.insert('end', "Type and enter '\\help' for help.\n")
        self.textArea['state'] = 'disabled'

        self.inputArea = ScrolledText(self.root,font=("Cascadia Code", 20))
        self.inputArea.config(height=1)
        self.inputArea.pack(padx=10, pady=1, fill='both', expand=1, anchor="s")

        self.sendButton = Button(self.root, text="Send", font=("Cascadia Code", 20), command=self.__send_input)
        self.sendButton.pack(padx=10, pady=10, fill='x', expand=1, anchor="s")
        self.root.bind('<Return>', lambda _: self.__send_input())

        self.root.protocol("WM_DELETE_WINDOW", self.__close_program)

        if self.message_backlog != '':
            self.__show_message(self.message_backlog)
            self.message_backlog: str = ''

        self.root.mainloop()
    
    def __clear(self) -> None:
        self.textArea['state'] = 'normal'
        self.textArea.delete('0.0', 'end')
        self.textArea['state'] = 'disabled'

    def __show_message(self, message: str) -> None:
        if self.root != None:
            self.textArea['state'] = 'normal'
            self.textArea.insert('end', f"{message}\n")
            self.textArea.yview('end')
            self.textArea['state'] = 'disabled'
        else:
            self.message_backlog += f"{message}\n"

    def __close_program(self) -> None:
        try:
            self.sock.send(0x00.to_bytes())
        except Exception:
            pass

        self.root.destroy()
        self.sock.close()
        sys.exit()

    def __send_input(self) -> None:
        message = self.inputArea.get('0.0', 'end').strip()
        
        try:
            match message:
                case "\\help":
                    self.__show_message("Commands:\n\\dm\\(user)\\(message): Send direct message (DM) to (user)\n\\logs: Show server logs\n\\online: Show all online users\n\\users: Show all users\n\\clear: Clear chat\n\\help: Show this command list")
                case "\\clear":
                    self.__clear()
                case "\\logs":
                    self.sock.send(0x02.to_bytes())
                case "\\online":
                    self.sock.send(0x03.to_bytes())
                case "\\users":
                    self.sock.send(0x04.to_bytes())
                case _:
                    if message.startswith("\\dm\\"):
                        user_to_send_to: str = ''
                        start_of_message: int = -1
                        is_backslash: bool = False

                        for index, char in enumerate(message[4:]):
                            if is_backslash:
                                if char == "\\":
                                    is_backslash = False
                                    user_to_send_to += "\\"
                                    continue
                                else:
                                    is_backslash = False
                                    start_of_message = index
                                    break

                            if char == "\\":
                                is_backslash = True
                            else:
                                user_to_send_to += char

                        if start_of_message == -1 or is_backslash:
                            showerror("PyChat", "Message is empty!")
                            return
                        else:
                            self.sock.send(0x05.to_bytes() + f"{user_to_send_to}\u0000{message[start_of_message:]}".encode("utf-8"))
                    else:
                        if message.strip() != '':
                            self.sock.send(0x09.to_bytes() + message.encode("utf-8"))
        except Exception as s_error:
            if askretrycancel("PyChat", f"Could not send message: {s_error}"):
                self.__send_input()
            return
        self.inputArea.delete('0.0', 'end')

    def __listen(self) -> None:
        while True:
            try:
                received = self.sock.recv(1024)
                match int(received[0:1].hex(), 16):
                    case 0x00:
                        server_version: str = received[1:].decode("utf-8")
                        if server_version != VERSION:
                            self.sock.send(0x0A.to_bytes())
                            showerror("PyChat", f"Server is a different version from the client\nServer: {server_version} | Client: {VERSION}")
                        else:
                            self.sock.send(0x00.to_bytes())
                            self.__sign_in()
                    case 0x01:
                        self.sock.send(0x01.to_bytes() + self.username.encode("utf-8") + 0x00.to_bytes() + self.password)
                    case 0x03:
                        self.__show_message(f"{received[1:].decode('utf-8')} joined!")
                    case 0x04:
                        self.__show_message(f"{received[1:].decode('utf-8')} left!")
                    case 0x05:
                        self.__show_message(f"--Start of logs--\n{received[1:].decode('utf-8')}\n--End of logs--")
                    case 0x06:
                        user_names: list[str] = received[1:].decode("utf-8").split("\u0000")
                        self.__show_message(f"Users online: {f'{self.username} (you)'}{'' if len(user_names) == 0 else ', ' + ', '.join(user_names)}")
                    case 0x07:
                        user_names: list[str] = received[1:].decode("utf-8").split("\u0000")
                        self.__show_message(f"All users: {f'{self.username} (you)'}{'' if len(user_names) == 0 else ', ' + ', '.join(user_names)}")
                    case 0x08:
                        self.__show_message(f"DM from " + ': '.join(received[1:].decode('utf-8').split('\u0000')))
                    case 0x09:
                        self.__show_message(": ".join(received[1:].decode("utf-8").split("\u0000")))
                    case 0x14:
                        Thread(target=self.__gui_loop).start()
                    case 0x0A:
                        showerror("PyChat", "User with same username is already logged in to the server!")
                        self.__sign_in()
                    case 0x0B:
                        showerror("PyChat", "Wrong password!")
                        self.__sign_in()
                    case 0x0C:
                        self.__show_message("Logs not found!")
                    case 0x0D:
                        self.__show_message("User not online!")
            except Exception:
                self.__close_program()
                break

if __name__ == '__main__':
    PyChatClient()