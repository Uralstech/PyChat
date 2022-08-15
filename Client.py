import socket
import threading
from tkinter import *
from tkinter.simpledialog import Dialog, askstring
from tkinter.messagebox import showerror
from tkinter.scrolledtext import ScrolledText

HOST = socket.gethostbyname(socket.gethostname()) # CHANGE THIS TO "HOST = askstring("PyChat", "Enter server IP")" IF YOU WANT THE USER TO ENTER THE SERVER IP
TIMEOUT = 120 # TIMEOUT FOR CONNECTING TO SERVER
PORT = 9090
VERSION = '1.4.2' # DO NOT CHANGE

class PyChatDialog(Dialog):
    def __init__(self, master, title):
        self.inputA = ""
        self.inputB = ""
        
        super().__init__(master, title)

    def body(self, master):
        self.resizable(False, False)
        Label(master, text="Username: ").grid(row=0)
        Label(master, text="Password: ").grid(row=1)

        self.e1 = Entry(master)
        self.e2 = Entry(master, show='+')
        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)

        return master
    
    def buttonbox(self):
        box = Frame(self)
        w = Button(box, text="Submit", width=10, command=self.ok, default=ACTIVE)
        w.pack(fill='x', expand=1, padx=5, pady=5)
        self.bind("<Return>", lambda x:self.ok())
        box.pack(fill='x', expand=1)

    def ok(self):
        self.inputA = self.e1.get()
        self.inputB = self.e2.get()
        self.destroy()

class Client:
    def __init__(self, host, port, timeout):
        root = Tk()
        root.withdraw()

        cd = PyChatDialog(root, "PyChat")
        self.username, self.password = cd.inputA, cd.inputB

        if self.username == '' or self.username == None or ' ' in self.username or 'SERVER' in self.username.upper() or 'ADMIN' in self.username.upper():
            showerror("PyChat", "INVALID USERNAME.")
            return
        if self.password == '' or self.password == None:
            showerror("PyChat", "INVALID PASSWORD.")
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
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
        self.textArea.insert('0.0', "COMMANDS-\n\\DM\\(user)\\(message): Send private message to (user)\n\\LOGS: Show all logged messages\n\\ONLINE: Show online users\n\\CLEAR: Clear chat window\n\\QUIT: Disconnects PyChat from server\n")
        self.textArea['state'] = 'disabled'

        self.inputArea = ScrolledText(self.root, height=2, font=("Consolas", 20))
        self.inputArea.pack(padx=10, pady=2, fill='x', expand=1)

        self.sendButton = Button(self.root, text="Send", font=("Consolas", 20), command=self.write)
        self.sendButton.pack(padx=10, pady=5, fill='x', expand=1)

        self.root.bind('<Return>', lambda x:self.write(returnV=True))
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

    def write(self, returnV=False):
        message = self.inputArea.get('0.0', 'end')
        if returnV: message = message[:-1]

        if message == "\\CLEAR\n":
            self.clear()
        else:
            message = f'{self.username}: {message}'
            try:
                self.sock.send(message.encode('utf-8'))
                if message == "\\QUIT\n": self.stop()
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
                elif message == "PASWRD": self.sock.send(self.password.encode('utf-8'))
                elif message == "E000": self.showerror("USERNAME UNAVAILABLE.", "170x60"); break
                elif message == "E001": self.showerror("INVALID PASSWORD.", "170x60"); break
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


if __name__ == '__main__':
    Client(HOST, PORT, TIMEOUT)