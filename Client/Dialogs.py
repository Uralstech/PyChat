from tkinter.simpledialog import Dialog
from tkinter import Frame, Label, Entry, Button, Checkbutton, OptionMenu, StringVar, BooleanVar, ACTIVE, END

from Common import PyChatConfig, PyChatConfigs

class PyChatSignInDialog(Dialog):
    def __init__(self, master, title: str) -> None:
        self.username: str = ""
        self.password: str = ""
        self.title_text: str = title

        super().__init__(master, title)

    def body(self, master) -> Frame:
        self.resizable(False, False)

        Label(master, text=self.title_text).pack()

        frame_1: Frame = Frame(master)
        frame_2: Frame = Frame(master)

        Label(frame_1, text="Username: ").pack(side="left")
        Label(frame_2, text="Password: ").pack(side="left")

        self.username_entry: Entry = Entry(frame_1)
        self.password_entry: Entry = Entry(frame_2, show='*')
        self.username_entry.pack(side="right")
        self.password_entry.pack(side="right")

        frame_1.pack(fill="x", expand=1, padx=2)
        frame_2.pack(fill="x", expand=1, padx=2)
        return master
    
    def buttonbox(self) -> None:
        box: Frame = Frame(self)
        
        select: Button = Button(box, text="Sign In", width=10, command=self.ok, default=ACTIVE)
        select.pack(fill='x', expand=1, padx=5, pady=5)
        
        self.bind("<Return>", lambda _:self.ok())
        box.pack(fill='x', expand=1)

    def ok(self) -> None:
        self.username = self.username_entry.get()
        self.password = self.password_entry.get()
        self.destroy()

class PyChatConfigChoosingDialog(Dialog):
    def __init__(self, master, configs_to_choose_from: PyChatConfigs, title: str) -> None:
        self.configs: PyChatConfigs = configs_to_choose_from
        self.selected: PyChatConfig | None = None
        self.create_new: bool = False
        self.title_text: str = title
        
        super().__init__(master, title)

    def body(self, master) -> Frame:
        self.resizable(False, False)
        
        Label(master, text=self.title_text).pack()

        frame_1: Frame = Frame(master)
        
        self.chosen: StringVar = StringVar(master, self.configs.most_recent)
        dropdown: OptionMenu = OptionMenu(frame_1, self.chosen, *(self.configs.configs.keys()))
        dropdown.config(width=21)
        dropdown.pack()
        
        frame_1.pack(fill="x", expand=1)

        return master
        
    def buttonbox(self) -> None:
        box: Frame = Frame(self)
        
        select: Button = Button(box, text="Connect", width=10, command=self.ok, default=ACTIVE)
        select.grid(row=0, column=0, padx=5)
        
        create_new: Button = Button(box, text="Add Server", width=10, command=self.add_server, default=ACTIVE)
        create_new.grid(row=0, column=1, padx=5)
        
        self.bind("<Return>", lambda _:self.ok())
        box.pack(fill='x', expand=1, pady=5)

    def add_server(self) -> None:
        self.create_new = True
        self.destroy()

    def ok(self) -> None:
        self.selected = self.configs.configs[self.chosen.get()]
        self.destroy()
    
class PyChatConfigCreateDialog(Dialog):
    def __init__(self, master, title: str) -> None:
        self.new_config: PyChatConfig | None = None
        self.overwrite: bool = False
        self.title_text = title

        super().__init__(master, title)

    def body(self, master) -> Frame:
        self.resizable(False, False)

        Label(master, text=self.title_text).pack()

        frame_1: Frame = Frame(master)
        frame_2: Frame = Frame(master)
        frame_3: Frame = Frame(master)
        frame_4: Frame = Frame(master)
        frame_5: Frame = Frame(master)

        Label(frame_1, text="Server name: ").pack(side="left")
        Label(frame_2, text="Server port: ").pack(side="left")
        Label(frame_3, text="Server IP: ").pack(side="left")
        Label(frame_4, text="Connection timeout: ").pack(side="left")
        Label(frame_5, text="Overwrite configs with same name: ").pack(side="left")
        self.overwrite_setting: BooleanVar = BooleanVar(master, False)

        self.name_entry: Entry = Entry(frame_1)
        self.port_entry: Entry = Entry(frame_2)
        self.host_ip_entry: Entry = Entry(frame_3)
        self.timeout_entry: Entry = Entry(frame_4)
        overwrite_checkbutton: Checkbutton = Checkbutton(frame_5, variable=self.overwrite_setting)
        
        self.name_entry.pack(side="right")
        self.name_entry.insert(END, "localhost")
        self.port_entry.pack(side="right")
        self.port_entry.insert(END, "5050")
        self.host_ip_entry.pack(side="right")
        self.host_ip_entry.insert(END, "127.0.0.1")
        self.timeout_entry.pack(side="right")
        self.timeout_entry.insert(END, "60")
        overwrite_checkbutton.pack(side="right")

        frame_1.pack(fill="x", expand=1, padx=2)
        frame_2.pack(fill="x", expand=1, padx=2)
        frame_3.pack(fill="x", expand=1, padx=2)
        frame_4.pack(fill="x", expand=1, padx=2)
        frame_5.pack(fill="x", expand=1, padx=2)

        return master
    
    def buttonbox(self) -> None:
        box: Frame = Frame(self)
        
        select: Button = Button(box, text="Add Server", width=10, command=self.ok, default=ACTIVE)
        select.pack(fill='x', expand=1, padx=5, pady=5)
        
        self.bind("<Return>", lambda _:self.ok())
        box.pack(fill='x', expand=1)

    def ok(self) -> None:
        self.overwrite = self.overwrite_setting.get()

        try:
            self.new_config = PyChatConfig(self.name_entry.get(), (int)(self.port_entry.get()), (int)(self.timeout_entry.get()), self.host_ip_entry.get())
        except Exception:
            self.new_config = None

        self.destroy()