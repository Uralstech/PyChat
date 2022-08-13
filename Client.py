import socket
import threading
from tkinter import *
from tkinter.messagebox import showerror
from tkinter.simpledialog import askstring
from tkinter.scrolledtext import ScrolledText

HOST = "127.0.0.1"
PORT = 9090
VERSION = '1.3.0' # DO NOT CHANGE

class Client:
    def __init__(self, host, port):
        root = Tk()
        root.withdraw()

        self.username = askstring("PyChat", "Enter you username", parent=root)

        if self.username == '' or ' ' in self.username or 'SERVER' in self.username.upper() or 'ADMIN' in self.username.upper():
            showerror("PyChat", "INVALID USERNAME.")
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, port))
        except:
            showerror("PyChat", "COULD NOT CONNECT TO SERVER.")
            return

        self.guiDone = False
        self.running = True
        
        guiThread = threading.Thread(target=self.guiLoop)
        receiveThread = threading.Thread(target=self.receive)

        guiThread.start()
        receiveThread.start()
    
    def guiLoop(self):
        self.root = Tk()
        self.root.title("PyChat Main")
        self.root.geometry("850x640")

        self.textArea = ScrolledText(self.root, height=15, font=("Consolas", 20))
        self.textArea.pack(padx=10, pady=5, fill='x', expand=1)
        self.textArea.insert('0.0', "Successfully connected. COMMANDS-\n\\DM\\(user)\\(message): Send private message to (user)\n\\LOGS: Show all logged messages\n\\ONLINE: Show online users\n\\CLEAR: Clear chat window\n")
        self.textArea['state'] = 'disabled'

        self.inputArea = ScrolledText(self.root, height=2, font=("Consolas", 20))
        self.inputArea.pack(padx=10, pady=2, fill='x', expand=1)

        self.sendButton = Button(self.root, text="Send", font=("Consolas", 20), command=self.write)
        self.sendButton.pack(padx=10, pady=5, fill='x', expand=1)

        self.root.protocol("WM_DELETE_WINDOW", self.stop)
        self.root.resizable(True, False)

        self.guiDone = True
        self.root.mainloop()
    
    def clear(self):
        self.textArea['state'] = 'normal'
        self.textArea.delete('0.0', 'end')
        self.textArea['state'] = 'disabled'
    
    def showerror(self, text, size):
        def stop():
            root.destroy()
            quit(0)

        root = Tk()
        root.title("PyChat")
        root.geometry(size)
        Label(root, text=text, font=("Consolas", 10)).pack()
        Button(root, text="Ok", font=("Consolas", 10), command=stop).pack(padx=10, fill='x', expand=1)
        root.mainloop()

    def stop(self):
        self.running = False
        self.root.destroy()
        self.sock.close()
        exit(0)

    def write(self):
        message = self.inputArea.get('0.0', 'end')

        if message == "\\CLEAR\n":
            self.clear()
        else:
            message = f'{self.username}: {message}'
            try: self.sock.send(message.encode('utf-8'))
            except OSError: self.showerror("COULD NOT SEND MESSAGE.\nPLEASE RESTART PYCHAT.", "200x75")

        self.inputArea.delete('0.0', 'end')

    def receive(self):
        while self.running:
            try:
                message = self.sock.recv(1024).decode('utf-8')
                if message.startswith("::SERVER::"):
                    if message[10:] != VERSION:
                        self.showerror(f"SERVER VERSION ({message[10:]})\nIS DIFFERENT FROM\nCLIENT VERSION ({VERSION})", "180x85")
                        self.sock.send('0'.encode('utf-8'))
                    else: self.sock.send('1'.encode('utf-8'))
                elif message == "USRNME": self.sock.send(self.username.encode('utf-8'))
                elif message == "E000": self.showerror("USERNAME UNAVAILABLE.", "170x60"); break
                else:
                    if self.guiDone:
                        self.textArea['state'] = 'normal'
                        self.textArea.insert('end', message)
                        self.textArea.yview('end')
                        self.textArea['state'] = 'disabled'
            except ConnectionAbortedError:
                self.running = False
                break
            except:
                self.running = False
                self.sock.close()
                break

Client(HOST, PORT)