"""Embedded Industrial Chatbot UI for Transmission Line Simulator.
Side-by-side dockable panel matching the app's clean engineering theme.
Features:
- Clear Chat button (clears current chat screen while preserving audit history)
- History view for full persistent audit logging
- Meaningful query chips
- Zero overlapping with app workspace
"""

import tkinter as tk
from tkinter import ttk, messagebox


class ChatbotUI:
    """Embedded chatbot panel that sits side-by-side with the main app."""

    def __init__(self, parent, chatbot, get_system_data):
        self.parent = parent
        self.chatbot = chatbot
        self.get_system_data = get_system_data

        self.is_open = False
        self.is_history_view = False

        self.panel_width = 460
        self._build_toggle_button()
        self._build_panel()

    def _build_toggle_button(self):
        """Header toggle button matching the app's classic engineering style."""
        self.btn_frame = tk.Frame(self.parent, bg="#F0F0F0")
        self.btn_frame.place(relx=0.985, rely=0.012, anchor="ne")

        self.toggle_btn = tk.Button(
            self.btn_frame,
            text="⚡ AI POWER ASSISTANT",
            font=("Arial", 9, "bold"),
            bg="#0B1D2A",
            fg="#FFFFFF",
            activebackground="#1B4965",
            activeforeground="#00FFFF",
            relief="raised",
            bd=2,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.toggle_chat
        )
        self.toggle_btn.pack()

    def _build_panel(self):
        """Construct the dockable side frame styled with the app's theme."""
        self.panel = tk.LabelFrame(
            self.parent,
            text="  ⚡ AI POWER SYSTEM ASSISTANT  ",
            bg="#F0F0F0",
            fg="#0B1D2A",
            font=("Arial", 10, "bold"),
            relief="groove",
            bd=2,
            padx=6,
            pady=6
        )

        # 1. Header Toolbar inside the panel
        header_bar = tk.Frame(self.panel, bg="#E2E8F0", relief="groove", bd=1, padx=4, pady=4)
        header_bar.pack(fill="x", pady=(0, 4))

        tk.Label(
            header_bar,
            text="ENGINEERING AI",
            bg="#E2E8F0",
            fg="#334155",
            font=("Arial", 8, "bold")
        ).pack(side="left", padx=4)

        # Close button
        btn_close = tk.Button(
            header_bar,
            text="✕ Close",
            font=("Arial", 8, "bold"),
            bg="#CBD5E1",
            fg="#0F172A",
            activebackground="#EF4444",
            activeforeground="#FFFFFF",
            relief="raised",
            bd=1,
            cursor="hand2",
            command=self.close_chat
        )
        btn_close.pack(side="right", padx=2)

        # History toggle button (Audit Trail)
        self.history_btn = tk.Button(
            header_bar,
            text="📜 History",
            font=("Arial", 8, "bold"),
            bg="#0B1D2A",
            fg="#FFFFFF",
            activebackground="#1B4965",
            activeforeground="#00FFFF",
            relief="raised",
            bd=1,
            cursor="hand2",
            command=self.toggle_history_view
        )
        self.history_btn.pack(side="right", padx=3)

        # Clear Chat Screen Button (preserves persistent history)
        self.clear_chat_btn = tk.Button(
            header_bar,
            text="🧹 Clear Chat",
            font=("Arial", 8, "bold"),
            bg="#E2E8F0",
            fg="#0F172A",
            activebackground="#CBD5E1",
            activeforeground="#000000",
            relief="raised",
            bd=1,
            cursor="hand2",
            command=self.clear_current_chat
        )
        self.clear_chat_btn.pack(side="right", padx=3)

        # 2. Helpful Action Chips Bar
        self._build_quick_chips(self.panel)

        # 3. Content Container (swaps between Chat and History)
        self.content_container = tk.Frame(self.panel, bg="#F0F0F0")
        self.content_container.pack(fill="both", expand=True, pady=2)

        # --- CHAT VIEW ---
        self.chat_view_frame = tk.Frame(self.content_container, bg="#F0F0F0")
        self.chat_view_frame.pack(fill="both", expand=True)

        chat_scroll_frame = tk.Frame(self.chat_view_frame, bg="#F0F0F0")
        chat_scroll_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(chat_scroll_frame)
        scrollbar.pack(side="right", fill="y")

        self.chat_area = tk.Text(
            chat_scroll_frame,
            bg="#FFFFFF",
            fg="#111111",
            font=("Courier", 9),
            wrap="word",
            state="disabled",
            yscrollcommand=scrollbar.set,
            padx=8,
            pady=8,
            bd=2,
            relief="sunken"
        )
        self.chat_area.pack(fill="both", expand=True)
        scrollbar.config(command=self.chat_area.yview)

        # Tag formatting
        self.chat_area.tag_config("user_sender", foreground="#0B1D2A", font=("Arial", 9, "bold"))
        self.chat_area.tag_config("user_msg", foreground="#1E293B", font=("Courier", 9))
        self.chat_area.tag_config("bot_sender", foreground="#0284C7", font=("Arial", 9, "bold"))
        self.chat_area.tag_config("bot_msg", foreground="#0F172A", font=("Courier", 9))

        # Input Frame
        self.input_frame = tk.Frame(self.chat_view_frame, bg="#E2E8F0", relief="sunken", bd=1, padx=4, pady=4)
        self.input_frame.pack(fill="x", pady=(4, 0))

        self.entry = tk.Entry(
            self.input_frame,
            font=("Arial", 9),
            bg="#FFFFFF",
            fg="#111111",
            relief="solid",
            bd=1
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.entry.bind("<Return>", lambda event: self.send_message())

        send_btn = tk.Button(
            self.input_frame,
            text="ASK",
            font=("Arial", 8, "bold"),
            bg="#0B1D2A",
            fg="#FFFFFF",
            activebackground="#0284C7",
            activeforeground="#FFFFFF",
            relief="raised",
            bd=1,
            cursor="hand2",
            padx=6,
            command=self.send_message
        )
        send_btn.pack(side="right")

        # --- HISTORY VIEW ---
        self.history_view_frame = tk.Frame(self.content_container, bg="#F0F0F0")

        hist_bar = tk.Frame(self.history_view_frame, bg="#E2E8F0", relief="groove", bd=1, padx=4, pady=3)
        hist_bar.pack(fill="x")
        tk.Label(
            hist_bar,
            text="PERMANENT SESSION AUDIT LOG",
            bg="#E2E8F0",
            fg="#0B1D2A",
            font=("Arial", 8, "bold")
        ).pack(side="left")

        clear_hist_btn = tk.Button(
            hist_bar,
            text="Delete Audit Log",
            font=("Arial", 8, "bold"),
            bg="#EF4444",
            fg="#FFFFFF",
            relief="raised",
            bd=1,
            cursor="hand2",
            command=self.clear_all_history
        )
        clear_hist_btn.pack(side="right")

        hist_scroll_frame = tk.Frame(self.history_view_frame, bg="#F0F0F0")
        hist_scroll_frame.pack(fill="both", expand=True, pady=4)

        hist_scroll = tk.Scrollbar(hist_scroll_frame)
        hist_scroll.pack(side="right", fill="y")

        self.history_area = tk.Text(
            hist_scroll_frame,
            bg="#FFFFFF",
            fg="#0F172A",
            font=("Courier", 8),
            wrap="word",
            state="disabled",
            yscrollcommand=hist_scroll.set,
            padx=8,
            pady=6,
            bd=2,
            relief="sunken"
        )
        self.history_area.pack(fill="both", expand=True)
        hist_scroll.config(command=self.history_area.yview)

        # Initial message
        self.add_message(
            "Power Assistant",
            "Connected to system telemetry & engineering knowledge engine.\n"
            "Ask any question about transmission parameters, formulas, physics, or simulations."
        )

    def _build_quick_chips(self, parent):
        """Action chips for instant assistance."""
        chips_frame = tk.Frame(parent, bg="#F0F0F0", pady=2)
        chips_frame.pack(fill="x")

        chips = [
            ("Reactance", "What is inductive reactance?"),
            ("Length Trend", "When line length increases, what changes occur in resistance, inductance, and capacitance?"),
            ("Spacing Trend", "What happens when we increase the distance between the conductors?"),
            ("Status", "Summarize current system status"),
        ]

        for label, query in chips:
            btn = tk.Button(
                chips_frame,
                text=label,
                font=("Arial", 8),
                bg="#E2E8F0",
                fg="#0F172A",
                activebackground="#0B1D2A",
                activeforeground="#FFFFFF",
                relief="raised",
                bd=1,
                cursor="hand2",
                command=lambda q=query: self._submit_quick_query(q)
            )
            btn.pack(side="left", padx=1, expand=True, fill="x")

    def _submit_quick_query(self, query):
        """Submit pre-built query."""
        if self.is_history_view:
            self.toggle_history_view()
        self.entry.delete(0, "end")
        self.entry.insert(0, query)
        self.send_message()

    def toggle_chat(self):
        """Toggle side-by-side panel without overlapping the app."""
        if self.is_open:
            self.close_chat()
        else:
            self.open_chat()

    def open_chat(self):
        """Dock the chatbot panel side-by-side with the main application frame."""
        self.is_open = True
        self.toggle_btn.config(text="✕ CLOSE ASSISTANT", bg="#1B4965", fg="#00FFFF")

        self.panel.pack(side="right", fill="both", padx=(0, 10), pady=10)

        cur_w = self.parent.winfo_width()
        cur_h = self.parent.winfo_height()
        if cur_w < 1550:
            target_w = min(1700, cur_w + self.panel_width)
            self.parent.geometry(f"{target_w}x{cur_h}")

        self.entry.focus_set()

    def close_chat(self):
        """Hide the chatbot panel and restore full width to the simulator."""
        self.is_open = False
        self.toggle_btn.config(text="⚡ AI POWER ASSISTANT", bg="#0B1D2A", fg="#FFFFFF")
        self.panel.pack_forget()

    def clear_current_chat(self):
        """Clear visible chat screen without deleting persistent audit trail."""
        self.chat_area.config(state="normal")
        self.chat_area.delete("1.0", "end")
        self.chat_area.config(state="disabled")
        self.add_message(
            "Power Assistant",
            "Chat screen cleared. (Past conversations remain saved in 📜 History)."
        )

    def toggle_history_view(self):
        """Switch between chat and history logs."""
        if not self.is_history_view:
            self.is_history_view = True
            self.history_btn.config(text="💬 Chat", bg="#0284C7", fg="#FFFFFF")
            self.chat_view_frame.pack_forget()
            self.history_view_frame.pack(fill="both", expand=True)
            self._refresh_history_text()
        else:
            self.is_history_view = False
            self.history_btn.config(text="📜 History", bg="#0B1D2A", fg="#FFFFFF")
            self.history_view_frame.pack_forget()
            self.chat_view_frame.pack(fill="both", expand=True)

    def _refresh_history_text(self):
        """Populate conversation history."""
        history = self.chatbot.get_history()
        self.history_area.config(state="normal")
        self.history_area.delete("1.0", "end")

        if not history:
            self.history_area.insert("end", "No conversation history recorded in this session.\n")
        else:
            for item in history:
                prefix = f"[{item['timestamp']}] " + ("USER: " if item['role'] == "user" else "ASSISTANT:\n")
                self.history_area.insert("end", prefix + item['message'] + "\n" + ("-" * 45) + "\n")

        self.history_area.config(state="disabled")
        self.history_area.see("end")

    def add_message(self, sender, message):
        """Append message to chat area."""
        self.chat_area.config(state="normal")

        if sender == "You":
            self.chat_area.insert("end", f"\n🧑 You:\n", "user_sender")
            self.chat_area.insert("end", f"{message}\n", "user_msg")
        else:
            self.chat_area.insert("end", f"\n⚡ {sender}:\n", "bot_sender")
            self.chat_area.insert("end", f"{message}\n", "bot_msg")

        self.chat_area.config(state="disabled")
        self.chat_area.see("end")

    def send_message(self):
        """Process user input and get reply."""
        message = self.entry.get().strip()
        if not message:
            return

        self.add_message("You", message)
        self.entry.delete(0, "end")

        system_data = None
        if callable(self.get_system_data):
            system_data = self.get_system_data()

        response = self.chatbot.reply(message, system_data)
        self.add_message("Power Assistant", response)

    def clear_all_history(self):
        """Clear permanent conversation history audit trail."""
        if messagebox.askyesno("Delete Audit Log", "Permanently delete all session history records?"):
            self.chatbot.clear_history()
            self._refresh_history_text()