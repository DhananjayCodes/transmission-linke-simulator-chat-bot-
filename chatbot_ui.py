import tkinter as tk


class ChatbotUI:

    def __init__(self, parent, chatbot, get_system_data):
        self.parent = parent
        self.chatbot = chatbot
        self.get_system_data = get_system_data

        self.window = None

        self.create_button()

    def create_button(self):
        self.button = tk.Button(
            self.parent,
            text="💬",
            font=("Arial", 18, "bold"),
            width=3,
            height=1,
            bg="#0A192F",
            fg="white",
            activebackground="#1B4965",
            activeforeground="white",
            relief="raised",
            bd=3,
            cursor="hand2",
            command=self.toggle_chat
        )

        # Bottom-right corner
        self.button.place(
            relx=0.97,
            rely=0.96,
            anchor="se"
        )

    def toggle_chat(self):
        if self.window is None or not self.window.winfo_exists():
            self.open_chat()
        else:
            self.window.destroy()

    def open_chat(self):
        self.window = tk.Toplevel(self.parent)

        self.window.title("Power System Assistant")
        self.window.geometry("420x560")
        self.window.minsize(360, 450)

        self.window.configure(bg="#F0F0F0")

        self.create_chat_header()
        self.create_chat_area()
        self.create_input_area()

    def create_chat_header(self):
        header = tk.Frame(
            self.window,
            bg="#0A192F",
            height=55
        )

        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="POWER SYSTEM ASSISTANT",
            bg="#0A192F",
            fg="#00FFFF",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=12)

        tk.Button(
            header,
            text="×",
            bg="#0A192F",
            fg="white",
            activebackground="#0A192F",
            activeforeground="red",
            relief="flat",
            font=("Arial", 18, "bold"),
            command=self.window.destroy
        ).pack(side="right", padx=8)

    def create_chat_area(self):
        frame = tk.Frame(self.window, bg="#E8EDF2")
        frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        self.chat_area = tk.Text(
            frame,
            bg="white",
            fg="#111111",
            font=("Arial", 10),
            wrap="word",
            state="disabled",
            yscrollcommand=scrollbar.set,
            padx=10,
            pady=10
        )

        self.chat_area.pack(fill="both", expand=True)

        scrollbar.config(command=self.chat_area.yview)

        self.add_message(
            "Power Assistant",
            "Hello! Ask me about your transmission line calculations."
        )

    def create_input_area(self):
        bottom = tk.Frame(
            self.window,
            bg="#D9D9D9",
            padx=8,
            pady=8
        )

        bottom.pack(fill="x")

        self.entry = tk.Entry(
            bottom,
            font=("Arial", 10)
        )

        self.entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 5)
        )

        self.entry.bind(
            "<Return>",
            lambda event: self.send_message()
        )

        tk.Button(
            bottom,
            text="SEND",
            font=("Arial", 9, "bold"),
            command=self.send_message
        ).pack(side="right")

        tk.Button(
            self.window,
            text="CLEAR CHAT HISTORY",
            font=("Arial", 9, "bold"),
            command=self.clear_history
        ).pack(fill="x", padx=8, pady=(0, 8))

    def add_message(self, sender, message):
        self.chat_area.config(state="normal")

        self.chat_area.insert(
            "end",
            f"{sender}:\n",
            "sender"
        )

        self.chat_area.insert(
            "end",
            f"{message}\n\n"
        )

        self.chat_area.config(state="disabled")
        self.chat_area.see("end")

    def send_message(self):
        message = self.entry.get().strip()

        if not message:
            return

        self.add_message("You", message)

        system_data = self.get_system_data()

        response = self.chatbot.reply(
            message,
            system_data
        )

        self.add_message(
            "Power Assistant",
            response
        )

        self.entry.delete(0, "end")

    def clear_history(self):
        self.chat_area.config(state="normal")
        self.chat_area.delete("1.0", "end")
        self.chat_area.config(state="disabled")

        self.add_message(
            "Power Assistant",
            "Chat history cleared. How can I help?"
        )