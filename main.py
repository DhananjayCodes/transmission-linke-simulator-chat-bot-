"""Transmission Line & Power System Analysis - retro Tkinter desktop tool."""

import cmath
import math
import tkinter as tk
from tkinter import messagebox, ttk
from chatbot import Chatbot
from chatbot_ui import ChatbotUI

class PowerSystemApp(tk.Tk):
    CONDUCTORS = {
        "ACSR Weasel": {"radius_mm": 3.25, "rdc": 0.272},
        "ACSR Rabbit": {"radius_mm": 4.12, "rdc": 0.184},
        "ACSR Dog": {"radius_mm": 4.72, "rdc": 0.139},
        "ACSR Panther": {"radius_mm": 6.00, "rdc": 0.070},
        "ACSR Zebra": {"radius_mm": 7.50, "rdc": 0.046},
        "Custom": {"radius_mm": 5.00, "rdc": 0.100},
    }
    EPS0 = 8.8541878128e-12
    MU0 = 4 * math.pi * 1e-7
    ALUMINUM_RHO = 2.82e-8

    def __init__(self):
        super().__init__()

    self.title("TRANSMISSION LINE & POWER SYSTEM ANALYSIS")
    self.geometry("1280x900")
    self.minsize(1080, 760)
    self.configure(bg="#F0F0F0")

    self._make_variables()
    self._make_styles()
    self._build_ui()

    self._update_conductor_fields()
    self._update_sld()

    # Create chatbot
    self.chatbot = Chatbot()

    self.chatbot_ui = ChatbotUI(
        self,
        self.chatbot,
        self.get_system_data
    )

    def _make_variables(self):
        self.voltage = tk.StringVar(value="132 kV")
        self.frequency = tk.StringVar(value="50 Hz")
        self.load = tk.StringVar(value="50")
        self.load_unit = tk.StringVar(value="MW")
        self.pf = tk.StringVar(value="0.85")
        self.conductor = tk.StringVar(value="ACSR Zebra")
        self.length = tk.StringVar(value="150")
        self.topology = tk.StringVar(value="Equilateral/Triangular")
        self.spacing = tk.StringVar(value="6")
        self.radius = tk.StringVar()
        self.rdc = tk.StringVar()
        self.mode = tk.StringVar(value="forward")
        self.status = tk.StringVar(value="READY - ENTER SYSTEM DATA")
        self.status_color = "#222222"
        self.result_vars = {key: tk.StringVar(value="—") for key in (
            "rac", "inductance", "capacitance", "vr", "regulation",
            "losses", "efficiency", "noload", "rise", "capacity", "model"
        )}

    def _make_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#F0F0F0")
        style.configure("TLabelframe", background="#F0F0F0", borderwidth=2, relief="groove")
        style.configure("TLabelframe.Label", background="#F0F0F0", foreground="#111111", font=("Arial", 10, "bold"))
        style.configure("TLabel", background="#F0F0F0", foreground="#111111", font=("Arial", 9))
        style.configure("TButton", padding=(10, 5), relief="raised", borderwidth=2, font=("Arial", 9, "bold"))
        style.configure("TCombobox", padding=2)
        style.configure("Header.TLabel", font=("Arial", 15, "bold"), foreground="#0B1D2A")
        style.configure("Output.TLabel", background="#FFFFFF", relief="sunken", borderwidth=1, anchor="e", padding=4)

    def _build_ui(self):
        outer = ttk.Frame(self, padding=10)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="TRANSMISSION LINE & POWER SYSTEM ANALYSIS", style="Header.TLabel").pack(anchor="w")
        ttk.Label(outer, text="CLASSIC ENGINEERING CALCULATION CONSOLE  |  ABCD PARAMETER MODEL", foreground="#555555").pack(anchor="w", pady=(0, 7))
        self.canvas = tk.Canvas(outer, height=125, bg="white", highlightthickness=1, highlightbackground="#555555")
        self.canvas.pack(fill="x", pady=(0, 8))

        inputs = ttk.Frame(outer)
        inputs.pack(fill="x")
        self._system_box(inputs).pack(side="left", fill="both", expand=True, padx=(0, 5))
        self._geometry_box(inputs).pack(side="left", fill="both", expand=True, padx=5)
        self._controls_box(inputs).pack(side="left", fill="both", expand=True, padx=(5, 0))

        output = ttk.LabelFrame(outer, text="  OUTPUT RESULTS  ", padding=8)
        output.pack(fill="both", expand=True, pady=(9, 0))
        self._output_table(output)
        self.status_label = tk.Label(output, textvariable=self.status, bg="#D9D9D9", fg=self.status_color,
                         font=("Arial", 11, "bold"), relief="raised", bd=2, pady=7)
        self.status_label.pack(fill="x", pady=(12, 0))

        schematic = ttk.LabelFrame(outer, text="  SYSTEM TRANSMISSION SCHEMATIC  ", padding=5)
        schematic.pack(fill="x", pady=(9, 0))
        self.schematic_canvas = tk.Canvas(
            schematic, height=215, bg="#0A192F", highlightthickness=2,
            highlightbackground="#1B4965"
        )
        self.schematic_canvas.pack(fill="x", expand=True)
        self.schematic_canvas.bind("<Configure>", lambda event: self._draw_initial_schematic())
        self._draw_initial_schematic()

    def _draw_initial_schematic(self):
        """Draw a useful preview before the first calculation is performed."""
        if not hasattr(self, "schematic_canvas"):
            return
        try:
            voltage = float(self.voltage.get().split()[0])
            length = float(self.length.get())
            load = float(self.load.get()) * (1000 if self.load_unit.get() == "kW" else 1e6)
        except ValueError:
            voltage, length, load = 0.0, 0.0, 0.0
        self.draw_system_schematic(
            voltage, voltage, length, self.conductor.get(), 0.0, 0.0, 0.0, 0.0,
            load / 1000
        )

    def _draw_lattice_tower(self, canvas, x, ground_y, top_y=45):
        """Draw one steel pylon using only line and polygon primitives."""
        steel = "#D7E3FC"
        shadow = "#6EA8C4"
        canvas.create_polygon(x - 19, ground_y, x - 7, top_y, x + 7, top_y,
                              x + 19, ground_y, outline=steel, fill="", width=2)
        canvas.create_line(x - 7, top_y, x + 7, top_y, fill=steel, width=2)
        canvas.create_line(x - 28, 67, x + 28, 67, fill=steel, width=2)
        canvas.create_line(x - 35, 84, x + 35, 84, fill=steel, width=2)
        canvas.create_line(x - 42, 102, x + 42, 102, fill=steel, width=2)
        canvas.create_line(x - 28, 67, x + 7, 102, fill=shadow)
        canvas.create_line(x + 28, 67, x - 7, 102, fill=shadow)
        canvas.create_line(x - 35, 84, x + 7, 125, fill=shadow)
        canvas.create_line(x + 35, 84, x - 7, 125, fill=shadow)
        canvas.create_line(x - 42, 102, x + 7, ground_y, fill=shadow)
        canvas.create_line(x + 42, 102, x - 7, ground_y, fill=shadow)
        canvas.create_line(x - 7, top_y, x - 7, ground_y, fill=steel, width=2)
        canvas.create_line(x + 7, top_y, x + 7, ground_y, fill=steel, width=2)
        canvas.create_line(x - 42, 102, x + 42, 102, fill=steel, width=2)
        canvas.create_line(x - 9, ground_y, x + 9, ground_y, fill="#FFFF00", width=3)

    def _draw_generator_station(self, canvas, x, center_y, voltage):
        """Draw the sending-end generator and step-up transformer."""
        cyan, yellow, white = "#00FFFF", "#FFFF00", "#FFFFFF"
        canvas.create_text(x, 17, text="SENDING END (Vs)", fill=yellow,
                           font=("Arial", 10, "bold"))
        canvas.create_text(x, 32, text=f"{voltage:.1f} kV", fill=white,
                           font=("Courier", 9, "bold"))
        canvas.create_oval(x - 29, center_y - 29, x + 29, center_y + 29,
                           outline=cyan, width=2)
        canvas.create_text(x, center_y, text="G", fill=yellow, font=("Arial", 18, "bold"))
        wave = [(x - 19, center_y + 6), (x - 13, center_y - 6),
                (x - 7, center_y + 6), (x - 1, center_y - 6),
                (x + 5, center_y + 6), (x + 11, center_y - 6), (x + 18, center_y + 6)]
        canvas.create_line(wave, fill=white, width=1, smooth=True)
        tx = x + 77
        canvas.create_rectangle(tx - 25, center_y - 31, tx + 25, center_y + 31,
                                outline=cyan, width=2)
        canvas.create_oval(tx - 12, center_y - 21, tx + 12, center_y + 21,
                           outline=yellow, width=2)
        canvas.create_oval(tx + 3, center_y - 21, tx + 27, center_y + 21,
                           outline=yellow, width=2)
        canvas.create_text(tx, center_y + 42, text="STEP-UP TX", fill=white,
                           font=("Courier", 8))
        canvas.create_line(x + 30, center_y, tx - 27, center_y, fill=white, width=2)
        return tx + 28

    def _draw_receiving_station(self, canvas, x, center_y, voltage):
        """Draw the receiving-end step-down transformer and load block."""
        cyan, yellow, white = "#00FFFF", "#FFFF00", "#FFFFFF"
        tx = x - 76
        canvas.create_rectangle(tx - 25, center_y - 31, tx + 25, center_y + 31,
                                outline=cyan, width=2)
        canvas.create_oval(tx - 27, center_y - 21, tx - 3, center_y + 21,
                           outline=yellow, width=2)
        canvas.create_oval(tx - 12, center_y - 21, tx + 12, center_y + 21,
                           outline=yellow, width=2)
        canvas.create_text(tx, center_y + 42, text="STEP-DOWN TX", fill=white,
                           font=("Courier", 8))
        canvas.create_line(tx + 27, center_y, x - 30, center_y, fill=white, width=2)
        canvas.create_rectangle(x - 30, center_y - 25, x + 30, center_y + 25,
                                outline=yellow, width=2)
        canvas.create_polygon(x - 18, center_y + 17, x - 12, center_y - 8,
                              x - 3, center_y - 8, x + 3, center_y - 17,
                              x + 12, center_y - 17, x + 19, center_y + 17,
                              outline=cyan, fill="", width=2)
        canvas.create_text(x, 17, text="RECEIVING END (Vr)", fill=yellow,
                           font=("Arial", 10, "bold"))
        canvas.create_text(x, 32, text=f"{voltage:.1f} kV", fill=white,
                           font=("Courier", 9, "bold"))

    def draw_system_schematic(self, vs, vr, length, conductor_type,
                              r_total, l_total, c_total, p_loss, p_load=0.0):
        """Redraw the live transmission schematic after each calculation."""
        canvas = self.schematic_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 900)
        ground_y, center_y = 166, 105
        left_tower, right_tower = width * 0.38, width * 0.68
        left_station, right_station = 92, width - 92
        start_line, end_line = left_station + 105, right_station - 105
        cyan, yellow, white, muted = "#00FFFF", "#FFFF00", "#FFFFFF", "#9FB3C8"

        canvas.create_text(width / 2, ground_y + 18,
                           text="TRANSMISSION CORRIDOR / THREE-PHASE OVERHEAD LINE",
                           fill=muted, font=("Arial", 8, "bold"))
        self._draw_lattice_tower(canvas, left_tower, ground_y)
        self._draw_lattice_tower(canvas, right_tower, ground_y)
        self._draw_generator_station(canvas, left_station, center_y, vs)
        self._draw_receiving_station(canvas, right_station, center_y, vr)

        # Three sagging phase conductors are represented by smooth segmented lines.
        phase_y = (67, 84, 102)
        for index, y in enumerate(phase_y):
            points = []
            for step in range(25):
                fraction = step / 24
                x = start_line + (end_line - start_line) * fraction
                sag = 23 * math.sin(math.pi * fraction)
                points.extend((x, y + sag))
            canvas.create_line(points, fill=(yellow if index == 1 else cyan), width=2, smooth=True)
        for x in (left_tower, right_tower):
            for y in phase_y:
                canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=yellow, outline=white)

        # Conductor callout and live metric panel.
        tag_x, tag_y = width / 2 - 118, 38
        canvas.create_rectangle(tag_x, tag_y, tag_x + 236, tag_y + 21,
                                outline=cyan, fill="#102A43")
        canvas.create_text(tag_x + 118, tag_y + 10, text=f"CONDUCTOR: {conductor_type}",
                           fill=white, font=("Courier", 8, "bold"))
        metrics = (f"R_total = {r_total:.2f} Ω     L_total = {l_total:.2f} mH     "
                   f"C_total = {c_total:.2f} μF")
        canvas.create_rectangle(width / 2 - 245, 126, width / 2 + 245, 147,
                                outline="#4169E1", fill="#102A43")
        canvas.create_text(width / 2, 136, text=metrics, fill=white,
                           font=("Courier", 8, "bold"))

        # Direction arrow and real-power flow annotation.
        arrow_y = 54
        canvas.create_line(left_tower + 48, arrow_y, right_tower - 48, arrow_y,
                           fill=yellow, arrow=tk.LAST, width=2)
        canvas.create_text((left_tower + right_tower) / 2, arrow_y - 10,
                           text=f"P_load = {p_load:.1f} kW   |   P_loss = {p_loss:.1f} kW",
                           fill=yellow, font=("Courier", 8, "bold"))

        # Dimension line is anchored to the towers and therefore scales with the canvas.
        dimension_y = 193
        canvas.create_line(left_tower, dimension_y, right_tower, dimension_y,
                           fill=white, arrow=tk.BOTH, width=1)
        canvas.create_text((left_tower + right_tower) / 2, dimension_y - 8,
                           text=f"<---  Length: {length:.1f} km  --->", fill=white,
                           font=("Courier", 9, "bold"))

    def _field(self, parent, row, label, variable, values=None, width=13, command=None):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=4)
        if values:
            widget = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly", width=width)
            if command:
                widget.bind("<<ComboboxSelected>>", command)
        else:
            widget = ttk.Entry(parent, textvariable=variable, width=width)
        widget.grid(row=row, column=1, sticky="ew", padx=5, pady=4)
        return widget

    def _system_box(self, parent):
        box = ttk.LabelFrame(parent, text="  A. SYSTEM & SOURCE SETUP  ", padding=7)
        self._field(box, 0, "Voltage Level", self.voltage, ["11 kV", "33 kV", "132 kV", "220 kV", "400 kV"], command=lambda e: self._update_sld())
        self._field(box, 1, "Operating Frequency", self.frequency, ["50 Hz", "60 Hz"])
        row = ttk.Frame(box); row.grid(row=2, column=0, columnspan=2, sticky="ew", pady=2)
        ttk.Label(row, text="Target Load P").pack(side="left", padx=(5, 8))
        ttk.Entry(row, textvariable=self.load, width=8).pack(side="left")
        ttk.Combobox(row, textvariable=self.load_unit, values=["kW", "MW"], state="readonly", width=5).pack(side="left", padx=4)
        self._field(box, 3, "Power Factor (lag)", self.pf)
        box.columnconfigure(1, weight=1)
        return box

    def _geometry_box(self, parent):
        box = ttk.LabelFrame(parent, text="  B. CONDUCTOR & GEOMETRY  ", padding=7)
        self._field(box, 0, "ACSR Conductor", self.conductor, list(self.CONDUCTORS), command=lambda e: self._update_conductor_fields())
        self._field(box, 1, "Line Length L (km)", self.length, command=lambda e: self._update_sld())
        self._field(box, 2, "Topology / Spacing", self.topology, ["Equilateral/Triangular", "Horizontal", "Vertical"])
        self._field(box, 3, "Spacing D (m)", self.spacing)
        self._field(box, 4, "Radius r (mm)", self.radius)
        self._field(box, 5, "DC Resistance (Ω/km)", self.rdc)
        box.columnconfigure(1, weight=1)
        return box

    def _controls_box(self, parent):
        box = ttk.LabelFrame(parent, text="  C. CALCULATION CONTROLS  ", padding=7)
        ttk.Button(box, text="CALCULATE SYSTEM PARAMETERS", command=self.calculate).grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=(5, 12))
        ttk.Label(box, text="Operating Mode:").grid(row=1, column=0, columnspan=2, sticky="w", padx=5)
        ttk.Radiobutton(box, text="Forward Mode (Analyze Performance)", variable=self.mode, value="forward").grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=3)
        ttk.Radiobutton(box, text="Reverse Mode (Find Max Load)", variable=self.mode, value="reverse").grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=3)
        ttk.Label(box, text="Reverse mode uses 5% voltage-drop limit.", foreground="#555555", wraplength=250).grid(row=4, column=0, columnspan=2, padx=5, pady=8)
        box.columnconfigure(0, weight=1)
        return box

    def _output_table(self, parent):
        groups = [("TOTAL LINE PARAMETERS", [("Total R_ac (Ω)", "rac"), ("Total Inductance L (mH)", "inductance"), ("Total Capacitance C (μF)", "capacitance")]),
                  ("ELECTRICAL PERFORMANCE", [("Receiving End Voltage V_R (kV)", "vr"), ("Voltage Regulation (%)", "regulation"), ("Line Losses (kW)", "losses"), ("Efficiency (%)", "efficiency")]),
                  ("SPECIAL EFFECTS / CAPACITY", [("No-load V_R (kV)", "noload"), ("No-load Voltage Rise (%)", "rise"), ("Maximum 5% Load Capacity (MW)", "capacity"), ("Selected Model", "model")])]
        for col, (title, rows) in enumerate(groups):
            frame = ttk.LabelFrame(parent, text=f"  {title}  ", padding=5)
            frame.pack(side="left", fill="both", expand=True, padx=4)
            for row, (label, key) in enumerate(rows):
                ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=5)
                ttk.Label(frame, textvariable=self.result_vars[key], style="Output.TLabel", width=17).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=5)
            frame.columnconfigure(1, weight=1)

    def _update_conductor_fields(self):
        data = self.CONDUCTORS[self.conductor.get()]
        self.radius.set(str(data["radius_mm"]))
        self.rdc.set(str(data["rdc"]))
        self._update_sld()

    def _update_sld(self):
        if not hasattr(self, "canvas"):
            return
        c = self.canvas; c.delete("all"); w = max(c.winfo_width(), 900)
        boxes = [(45, "GENERATION SOURCE", self.voltage.get()), (w // 2 - 115, "TRANSMISSION LINE", f"L = {self.length.get()} km"), (w - 275, "RECEIVING LOAD", f"P = {self.load.get()} {self.load_unit.get()}")]
        for x, title, summary in boxes:
            c.create_rectangle(x, 30, x + 230, 91, outline="#222222", width=2, fill="#E6E6E6")
            c.create_text(x + 115, 48, text=title, font=("Arial", 10, "bold"), fill="#111111")
            c.create_text(x + 115, 70, text=summary, font=("Courier", 10), fill="#111111")
        c.create_line(280, 60, w // 2 - 120, 60, arrow=tk.LAST, width=2)
        c.create_line(w // 2 + 120, 60, w - 280, 60, arrow=tk.LAST, width=2)
        c.create_text(w // 2, 108, text="THREE-PHASE TRANSMISSION SYSTEM SINGLE LINE DIAGRAM", font=("Arial", 9, "bold"), fill="#555555")

    def _read_inputs(self):
        vk = float(self.voltage.get().split()[0]) * 1000
        f = float(self.frequency.get().split()[0]); length = float(self.length.get())
        spacing = float(self.spacing.get()); radius = float(self.radius.get()) / 1000; rdc = float(self.rdc.get())
        pf = float(self.pf.get()); load = float(self.load.get()) * (1000 if self.load_unit.get() == "kW" else 1e6)
        if min(vk, f, length, spacing, radius, rdc, pf, load) <= 0 or pf > 1: raise ValueError("All values must be positive; power factor must be ≤ 1.")
        return vk, f, length, spacing, radius, rdc, pf, load

    def _line_model(self, vk, f, length, spacing, radius, rdc):
        if self.topology.get() == "Equilateral/Triangular": gmd = spacing
        else: gmd = spacing * (2 ** (1 / 3))
        gmr = 0.7788 * radius
        omega = 2 * math.pi * f
        delta = math.sqrt(2 * self.ALUMINUM_RHO / (omega * self.MU0))
        rac_km = rdc * (1 + (radius / delta) ** 4 / 48)
        l_h_km = 2e-7 * math.log(gmd / gmr) * 1000
        c_f_km = 2 * math.pi * self.EPS0 / math.log(gmd / radius) * 1000
        z = complex(rac_km, omega * l_h_km / 1000)
        y = complex(0, omega * c_f_km / 1000)
        Z, Y = z * length, y * length
        if length < 80: A, B, C, D, model = 1 + 0j, Z, 0j, 1 + 0j, "SHORT LINE"
        elif length <= 240: A, B, C, D = 1 + Y * Z / 2, Z, Y * (1 + Y * Z / 4), 1 + Y * Z / 2; model = "MEDIUM LINE (NOMINAL-π)"
        else:
            gamma = cmath.sqrt(z * y); zc = cmath.sqrt(z / y)
            A = D = cmath.cosh(gamma * length); B = zc * cmath.sinh(gamma * length); C = cmath.sinh(gamma * length) / zc; model = "LONG LINE (DISTRIBUTED)"
        return A, B, C, D, rac_km * length, l_h_km * length, c_f_km * length, model

    def _performance(self, vs, A, B, load, pf):
        angle = math.acos(pf); S = load / pf * complex(math.cos(angle), math.sin(angle)); vr = vs / A
        for _ in range(100):
            ir = (S / (3 * vr)).conjugate()
            new_vr = (vs - B * ir) / A
            if abs(new_vr - vr) < 1e-5: break
            vr = new_vr
        ir = (S / (3 * vr)).conjugate(); isource = (A * ir + (0 if B == 0 else B * ir))
        losses = max(0, 3 * (abs(ir) ** 2) * (B.real if B else 0))
        return vr, losses, S, isource

    def calculate(self):
        try:
            vk, f, length, spacing, radius, rdc, pf, load = self._read_inputs()
            A, B, C, D, rac, inductance, capacitance, model = self._line_model(vk, f, length, spacing, radius, rdc)
            vs = vk / math.sqrt(3); noload = abs(vs / A) * math.sqrt(3)
            if self.mode.get() == "reverse":
                lo, hi = 0.0, vk * 1e5
                for _ in range(70):
                    mid = (lo + hi) / 2; vr, *_ = self._performance(vs, A, B, mid, pf)
                    if (vk - abs(vr) * math.sqrt(3)) / vk <= 0.05: lo = mid
                    else: hi = mid
                load = lo; self.load.set(f"{load / (1e6 if self.load_unit.get() == 'MW' else 1000):.3f}")
            vr, losses, S, _ = self._performance(vs, A, B, load, pf)
            vr_kv = abs(vr) * math.sqrt(3) / 1000; reg = (vk / 1000 - vr_kv) / vr_kv * 100
            losses_kw = losses / 1000; efficiency = load / (load + losses) * 100 if load else 0
            rise = (noload - vk / 1000) / (vk / 1000) * 100; capacity = load / 1e6
            vals = {"rac": f"{rac:.4f}", "inductance": f"{inductance * 1000:.4f}", "capacitance": f"{capacitance * 1e6:.4f}", "vr": f"{vr_kv:.3f}", "regulation": f"{reg:.2f}", "losses": f"{losses_kw:.2f}", "efficiency": f"{efficiency:.2f}", "noload": f"{noload:.3f}", "rise": f"{rise:.2f}", "capacity": f"{capacity:.3f}", "model": model}
            for key, value in vals.items(): self.result_vars[key].set(value)
            passed = reg <= 5.0
            self.status_color = "#006400" if passed else "#B00000"
            self.status.set("PASS - VOLTAGE DROP WITHIN 5% LIMIT" if passed else "VOLTAGE DROP EXCEEDED (>5%)")
            self.status_label.configure(fg=self.status_color)
            self.draw_system_schematic(
                vk / 1000, vr_kv, length, self.conductor.get(), rac,
                inductance * 1000, capacitance * 1e6, losses_kw, load / 1000
            )
        except (ValueError, ZeroDivisionError, OverflowError) as exc:
            messagebox.showerror("Input Error", str(exc) or "Please enter valid numeric values.")


if __name__ == "__main__":
    def get_system_data(self):

        return {
        "voltage": self.voltage.get(),
        "frequency": self.frequency.get(),
        "load": self.load.get(),
        "load_unit": self.load_unit.get(),
        "power_factor": self.pf.get(),

        "conductor": self.conductor.get(),
        "length": self.length.get(),
        "topology": self.topology.get(),
        "spacing": self.spacing.get(),
        "radius": self.radius.get(),
        "rdc": self.rdc.get(),

        "rac": self.result_vars["rac"].get(),
        "inductance": self.result_vars["inductance"].get(),
        "capacitance": self.result_vars["capacitance"].get(),

        "vr": self.result_vars["vr"].get(),
        "regulation": self.result_vars["regulation"].get(),
        "losses": self.result_vars["losses"].get(),
        "efficiency": self.result_vars["efficiency"].get(),

        "noload": self.result_vars["noload"].get(),
        "rise": self.result_vars["rise"].get(),
        "capacity": self.result_vars["capacity"].get(),
        "model": self.result_vars["model"].get()
    }
    PowerSystemApp().mainloop()
