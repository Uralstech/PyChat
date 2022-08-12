import socket
import threading
from tkinter import *
from tkinter.messagebox import showerror
from tkinter.simpledialog import askstring
from tkinter.scrolledtext import ScrolledText

HOST = "127.0.0.1"
PORT = 9090

class Client:
    def __init__(self, host, port):
        root = Tk()
        root.withdraw()

        self.username = askstring("PyChat", "Enter you username", parent=root)
        assert self.username != "__SERVER__" and self.username != '', "ILLEGAL USERNAME"

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

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

        self.inputArea = Text(self.root, height=2, font=("Consolas", 20))
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

    def stop(self, msg=""):
        if msg != "": showerror("PyChat", msg)

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
            self.sock.send(message.encode('utf-8'))
        
        self.inputArea.delete('0.0', 'end')

    def receive(self):
        while self.running:
            try:
                message = self.sock.recv(1024).decode('utf-8')
                if message == "USRNME": self.sock.send(self.username.encode('utf-8'))
                elif message == "E000": self.stop("E000: USERNAME ALREADY EXISTS"); break
                else:
                    if self.guiDone:
                        self.textArea['state'] = 'normal'
                        self.textArea.insert('end', message)
                        self.textArea.yview('end')
                        self.textArea['state'] = 'disabled'
            except ConnectionAbortedError:
                break
            except:
                self.sock.close()
                break

Client(HOST, PORT)