"""Industrial-Grade Power System Chatbot Engine.
Combines:
1. High-precision offline IEEE/IEC transmission line calculation & physics engine.
2. Typos & fuzzy keyword normalization (e.g., 'teh conductors' -> 'the conductors').
3. Multi-turn conversation memory with separate Clear Screen vs Persistent Audit Trail.
4. Concise, commercial-ready answers (direct, crisp explanations without fluff).
5. Cloud Knowledge RAG / API Fallback for any questions outside core tables.
"""

import math
import re
import json
import urllib.request
import urllib.parse
from datetime import datetime
from power_calculations import (
    calculate_full_system,
    calculate_gmd,
    calculate_rac,
    calculate_inductance,
    calculate_capacitance,
    determine_line_model,
    CONDUCTOR_DATABASE
)

class Chatbot:
    """Industrial Power System AI Assistant with offline intelligence and cloud fallback."""

    def __init__(self):
        self.name = "Industrial Power Assistant"
        self.history = []  # Persistent audit trail
        self._init_knowledge_base()

    def get_history(self):
        return list(self.history)

    def clear_history(self):
        self.history.clear()

    def record_turn(self, user_msg, bot_msg):
        now_str = datetime.now().strftime("%H:%M:%S")
        self.history.append({"timestamp": now_str, "role": "user", "message": user_msg})
        self.history.append({"timestamp": now_str, "role": "bot", "message": bot_msg})

    def _normalize_text(self, text):
        """Fix common engineering typos and normalize tokens."""
        clean = text.lower().strip()
        # Common typos
        typo_map = {
            r"\bteh\b": "the",
            r"\binductence\b": "inductance",
            r"\bresistence\b": "resistance",
            r"\bcapacitence\b": "capacitance",
            r"\bfrequncy\b": "frequency",
            r"\breactence\b": "reactance",
            r"\bcondutor\b": "conductor",
            r"\btransmision\b": "transmission",
        }
        for pattern, replacement in typo_map.items():
            clean = re.sub(pattern, replacement, clean)
        return clean

    def _init_knowledge_base(self):
        """Comprehensive dictionary of core engineering concepts and formulas."""
        self.knowledge_dict = {
            "inductive_reactance": {
                "keywords": ["inductive reactance", "what is inductive reactance", "formula for inductive reactance", "x_l", "xl"],
                "answer": (
                    "Inductive Reactance (X_L = 2πfL = ωL):\n"
                    "• The opposition offered by an inductor or transmission line inductance to alternating current (AC).\n"
                    "• Measured in Ohms (Ω).\n"
                    "• Proportional to frequency (f) and inductance (L). Higher frequency or longer line directly increases X_L."
                )
            },
            "capacitive_reactance": {
                "keywords": ["capacitive reactance", "x_c", "xc"],
                "answer": (
                    "Capacitive Reactance (X_C = 1 / (2πfC)):\n"
                    "• The opposition offered by capacitance to alternating current (AC).\n"
                    "• Measured in Ohms (Ω).\n"
                    "• Inversely proportional to frequency and capacitance. As frequency or line length increases, X_C decreases."
                )
            },
            "reactance": {
                "keywords": ["what is reactance", "electrical reactance"],
                "answer": (
                    "Reactance (X = X_L - X_C):\n"
                    "• Non-resistive opposition of electrical elements to AC current.\n"
                    "• Caused by energy storage in magnetic fields (Inductive, X_L) and electric fields (Capacitive, X_C)."
                )
            },
            "impedance": {
                "keywords": ["what is impedance", "line impedance"],
                "answer": (
                    "Impedance (Z = R + jX):\n"
                    "• The total opposition a circuit presents to AC current, combining AC resistance (R) and reactance (X).\n"
                    "• Measured in Ohms (Ω)."
                )
            },
            "admittance": {
                "keywords": ["what is admittance", "line admittance"],
                "answer": (
                    "Admittance (Y = G + jB = 1 / Z):\n"
                    "• Measure of how easily a circuit allows AC current to flow.\n"
                    "• Conductance (G) is real part; Susceptance (B) is imaginary part. Measured in Siemens (S)."
                )
            },
            "skin_effect": {
                "keywords": ["skin effect", "skin depth"],
                "answer": (
                    "Skin Effect:\n"
                    "• The tendency of AC current to concentrate near conductor surface, reducing effective cross-section.\n"
                    "• Skin depth δ = √(2ρ / (ω·μ)). Decreases with higher frequency, making R_ac > R_dc."
                )
            },
            "ferranti_effect": {
                "keywords": ["ferranti", "voltage rise"],
                "answer": (
                    "Ferranti Effect:\n"
                    "• Receiving-end voltage (Vr) exceeds sending-end voltage (Vs) under no-load or light load on medium/long lines.\n"
                    "• Caused by line charging current flowing through series line inductance."
                )
            },
            "abcd_parameters": {
                "keywords": ["abcd", "two port parameter"],
                "answer": (
                    "ABCD Parameters:\n"
                    "• Two-port matrix relating sending & receiving ends: Vs = A·Vr + B·Ir, Is = C·Vr + D·Ir.\n"
                    "• For symmetrical lines: A = D. Reciprocity condition: A·D - B·C = 1."
                )
            },
            "acsr": {
                "keywords": ["acsr"],
                "answer": (
                    "ACSR (Aluminum Conductor Steel Reinforced):\n"
                    "• Outer aluminum strands provide high conductivity; central steel core provides high tensile strength.\n"
                    "• Standard sizes: Weasel, Rabbit, Dog, Panther, Zebra."
                )
            },
            "gmd_gmr": {
                "keywords": ["gmd", "gmr"],
                "answer": (
                    "GMD & GMR:\n"
                    "• GMD (Geometric Mean Distance): Equivalent geometric distance between conductor phases.\n"
                    "• GMR (Geometric Mean Radius): Effective radius of conductor accounting for internal flux (r' = 0.7788·r)."
                )
            },
            "surge_impedance": {
                "keywords": ["surge impedance", "sil", "characteristic impedance"],
                "answer": (
                    "Surge Impedance (Zc) & SIL:\n"
                    "• Zc = √(L / C) ≈ 250–400 Ω for overhead lines.\n"
                    "• Surge Impedance Loading (SIL) = V_rated² / Zc: The load where line reactive power generated equals reactive power consumed."
                )
            },
            "corona": {
                "keywords": ["corona"],
                "answer": (
                    "Corona Effect:\n"
                    "• Ionization of air around high-voltage conductors when surface electric field exceeds air dielectric breakdown (~30 kV/cm peak).\n"
                    "• Causes power loss, ozone, and audible hiss. Reduced by increasing conductor diameter or using bundles."
                )
            },
            "sag": {
                "keywords": ["sag", "tension"],
                "answer": (
                    "Conductor Sag:\n"
                    "• S = (w · L²) / (8 · T), where w is weight per unit length, L is span length, T is tension.\n"
                    "• Increases with temperature due to thermal expansion."
                )
            },
            "power_factor": {
                "keywords": ["power factor", "lagging", "leading"],
                "answer": (
                    "Power Factor (cos φ):\n"
                    "• Ratio of Real Power (P) to Apparent Power (S).\n"
                    "• Low lagging PF increases current and line losses; leading PF can cause voltage rise."
                )
            }
        }

    def _query_cloud_api(self, query):
        """Query Cloud Knowledge API when local knowledge doesn't contain a direct match."""
        search_term = query.replace("what is", "").replace("what are", "").replace("explain", "").replace("tell me about", "").strip()
        if not search_term:
            return None

        # 1. Wikipedia OpenSearch API to find the exact encyclopedic title
        try:
            opensearch_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(search_term)}&limit=1&namespace=0&format=json"
            req = urllib.request.Request(opensearch_url, headers={"User-Agent": "TransmissionAssistant/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    titles = data[1]
                    descriptions = data[2]
                    if titles:
                        # If description is available from opensearch
                        if descriptions and descriptions[0] and len(descriptions[0]) > 25:
                            return descriptions[0]

                        # Fetch summary for top title
                        best_title = titles[0]
                        sum_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(best_title)}"
                        sum_req = urllib.request.Request(sum_url, headers={"User-Agent": "TransmissionAssistant/1.0"})
                        with urllib.request.urlopen(sum_req, timeout=3.0) as s_resp:
                            if s_resp.status == 200:
                                s_data = json.loads(s_resp.read().decode("utf-8"))
                                ext = s_data.get("extract", "").strip()
                                if ext:
                                    sentences = ext.split(". ")
                                    return ". ".join(sentences[:2]) + "."
        except Exception:
            pass

        # 2. DuckDuckGo Instant Answer API fallback
        try:
            params = urllib.parse.urlencode({
                "q": f"electrical engineering transmission {search_term}",
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1"
            })
            url = f"https://api.duckduckgo.com/?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": "TransmissionAssistant/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    abstract = data.get("AbstractText", "").strip()
                    if abstract and len(abstract) > 25:
                        sentences = abstract.split(". ")
                        return ". ".join(sentences[:2]) + "."
        except Exception:
            pass

        return None

    def _handle_conductor_spacing_questions(self, clean):
        """Answer conductor spacing questions concisely."""
        is_spacing = any(k in clean for k in ["distance", "spacing", "separation", "space"])
        is_conductor = any(k in clean for k in ["conductor", "conductors", "phase", "line"])

        if is_spacing and (is_conductor or "between" in clean):
            # Check which parameter
            has_r = "resistance" in clean or "ac resistance" in clean
            has_l = "inductance" in clean or "inductive" in clean
            has_c = "capacitance" in clean or "capacitive" in clean

            if has_r and not has_l and not has_c:
                return (
                    "When conductor spacing/distance increases:\n"
                    "• Total Resistance: Remains approximately unchanged (constant).\n"
                    "Reason: Resistance depends only on conductor material, length, and cross-section, not spacing."
                )
            elif has_l and not has_r and not has_c:
                return (
                    "When conductor spacing/distance increases:\n"
                    "• Total Inductance: Increases (↑).\n"
                    "Reason: L = (μ₀/2π)·ln(GMD/GMR). Increasing spacing increases GMD, which increases magnetic flux linkage and line inductance."
                )
            elif has_c and not has_r and not has_l:
                return (
                    "When conductor spacing/distance increases:\n"
                    "• Total Capacitance: Decreases (↓).\n"
                    "Reason: C = 2πε₀/ln(GMD/r). Larger spacing weakens electric-field coupling between conductors, lowering capacitance."
                )
            else:
                # All three or general
                return (
                    "When distance between conductors increases:\n"
                    "• Resistance: Constant (≈ unchanged)\n"
                    "• Inductance: Increases (↑)\n"
                    "• Capacitance: Decreases (↓)\n"
                    "Summary: Resistance ≈ Constant | Inductance ↑ | Capacitance ↓."
                )
        return None

    def _handle_line_length_questions(self, clean):
        """Answer line length questions concisely."""
        is_length = "length" in clean
        if is_length:
            has_r = "resistance" in clean
            has_l = "inductance" in clean
            has_c = "capacitance" in clean

            if has_r and not has_l and not has_c:
                return (
                    "When transmission line length increases:\n"
                    "• Total AC Resistance: Increases (↑).\n"
                    "Reason: Resistance is directly proportional to conductor length (R = r_per_km × Length)."
                )
            elif has_l and not has_r and not has_c:
                return (
                    "When transmission line length increases:\n"
                    "• Total Inductance: Increases (↑).\n"
                    "Reason: Each additional meter adds series magnetic flux (L_total = L_per_km × Length)."
                )
            elif has_c and not has_r and not has_l:
                return (
                    "When transmission line length increases:\n"
                    "• Total Capacitance: Increases (↑).\n"
                    "Reason: Capacitance is distributed along the entire conductor length (C_total = C_per_km × Length)."
                )
            elif has_r and has_l and has_c:
                return (
                    "When transmission line length increases:\n"
                    "• Total AC Resistance: Increases (↑)\n"
                    "• Total Inductance: Increases (↑)\n"
                    "• Total Capacitance: Increases (↑)\n"
                    "Summary: All three total parameters scale directly with line length."
                )
        return None

    def _handle_what_if_comparative_sim(self, clean, system_data):
        """Perform on-the-fly comparative power flow for parametric what-if questions."""
        # Check if user is asking to change/test a parameter
        has_change_trigger = any(k in clean for k in [
            "what if", "if i change", "change", "increase", "decrease", "set", "at", "what would", "calculate for"
        ])
        if not has_change_trigger:
            return None

        # Baseline values
        if not system_data:
            system_data = {
                "voltage": "132 kV", "frequency": "50 Hz", "load": "50", "load_unit": "MW",
                "power_factor": "0.85", "conductor": "ACSR Zebra", "length": "150",
                "topology": "Equilateral/Triangular", "spacing": "6", "radius": "7.5", "rdc": "0.046"
            }

        try:
            cur_v = float(str(system_data.get("voltage", "132")).split()[0])
            cur_f = float(str(system_data.get("frequency", "50")).split()[0])
            cur_len = float(system_data.get("length", 150))
            cur_spacing = float(system_data.get("spacing", 6.0))
            cur_radius = float(system_data.get("radius", 7.5))
            cur_rdc = float(system_data.get("rdc", 0.046))
            cur_top = system_data.get("topology", "Equilateral/Triangular")
            cur_load = float(system_data.get("load", 50))
            if system_data.get("load_unit") == "kW":
                cur_load /= 1000.0
            cur_pf = float(system_data.get("power_factor", 0.85))
            cur_cond = system_data.get("conductor", "ACSR Zebra")
        except Exception:
            cur_v, cur_f, cur_len, cur_spacing, cur_radius, cur_rdc = 132.0, 50.0, 150.0, 6.0, 7.5, 0.046
            cur_top, cur_load, cur_pf, cur_cond = "Equilateral/Triangular", 50.0, 0.85, "ACSR Zebra"

        target_v, target_f, target_len, target_spacing = cur_v, cur_f, cur_len, cur_spacing
        target_radius, target_rdc, target_top = cur_radius, cur_rdc, cur_top
        target_load, target_pf, target_cond = cur_load, cur_pf, cur_cond

        detected = False
        desc = ""

        # Frequency change
        m = re.search(r"(?:frequency|freq|hz)\s*(?:to|is|=|of)?\s*(\d+(?:\.\d+)?)\s*(?:hz)?", clean)
        if not m:
            m = re.search(r"(\d+(?:\.\d+)?)\s*hz", clean)
        if m:
            val = float(m.group(1))
            if 10 <= val <= 500:
                target_f = val
                detected = True
                desc = f"Frequency: {cur_f} Hz → {target_f} Hz"

        # Length change
        if not detected:
            m = re.search(r"length\s*(?:to|is|=|of)?\s*(\d+(?:\.\d+)?)\s*(?:km)?", clean)
            if not m:
                m = re.search(r"(\d+(?:\.\d+)?)\s*km", clean)
            if m:
                val = float(m.group(1))
                if val > 0:
                    target_len = val
                    detected = True
                    desc = f"Length: {cur_len} km → {target_len} km"

        # Voltage change
        if not detected:
            m = re.search(r"voltage\s*(?:level)?\s*(?:to|is|=|of)?\s*(\d+(?:\.\d+)?)\s*(?:kv)?", clean)
            if not m:
                m = re.search(r"(\d+(?:\.\d+)?)\s*kv", clean)
            if m:
                val = float(m.group(1))
                if val > 0:
                    target_v = val
                    detected = True
                    desc = f"Voltage: {cur_v} kV → {target_v} kV"

        # Load change
        if not detected:
            m = re.search(r"(?:load|power)\s*(?:to|is|=|of)?\s*(\d+(?:\.\d+)?)\s*(?:mw)?", clean)
            if m:
                val = float(m.group(1))
                if val > 0:
                    target_load = val
                    detected = True
                    desc = f"Load: {cur_load} MW → {target_load} MW"

        # Spacing change
        if not detected:
            m = re.search(r"spacing\s*(?:d)?\s*(?:to|is|=|of)?\s*(\d+(?:\.\d+)?)\s*(?:m|meters)?", clean)
            if m:
                val = float(m.group(1))
                if val > 0:
                    target_spacing = val
                    detected = True
                    desc = f"Spacing: {cur_spacing} m → {target_spacing} m"

        if detected:
            base_res = calculate_full_system(cur_v, cur_f, cur_len, cur_spacing, cur_radius, cur_rdc, cur_top, cur_load, cur_pf)
            new_res = calculate_full_system(target_v, target_f, target_len, target_spacing, target_radius, target_rdc, target_top, target_load, target_pf)

            # Concise summary + compact table
            return (
                f"🔬 Calculation Result ({desc}):\n"
                f"• Receiving Voltage (Vr): {base_res['vr_kv']:.2f} kV → {new_res['vr_kv']:.2f} kV\n"
                f"• Voltage Regulation: {base_res['regulation_pct']:.2f}% → {new_res['regulation_pct']:.2f}%\n"
                f"• Line Losses: {base_res['losses_kw']:.1f} kW → {new_res['losses_kw']:.1f} kW\n"
                f"• Efficiency: {base_res['efficiency_pct']:.2f}% → {new_res['efficiency_pct']:.2f}%\n"
                f"• Model: {new_res['model']}"
            )
        return None

    def _handle_system_state_query(self, clean, system_data):
        """Retrieve live parameters from parent application."""
        if not system_data:
            return None

        has_calc = system_data.get("vr") not in (None, "", "—")

        if any(k in clean for k in ["voltage regulation", "regulation", "reg %"]):
            if has_calc:
                return f"Current Voltage Regulation: {system_data['regulation']}%\nStandard IEEE Limit: ≤ 5.0%."
            return "Click 'CALCULATE SYSTEM PARAMETERS' first to view voltage regulation."

        if any(k in clean for k in ["receiving end voltage", "receiving voltage", "vr"]):
            if has_calc:
                return f"Receiving-End Voltage (V_R): {system_data['vr']} kV Line-to-Line."
            return "Run calculation first to determine receiving-end voltage."

        if any(k in clean for k in ["losses", "loss", "line loss"]):
            if has_calc:
                return f"Calculated Line Losses: {system_data['losses']} kW."
            return "Run calculation first to determine line losses."

        if any(k in clean for k in ["efficiency"]):
            if has_calc:
                return f"Calculated Transmission Efficiency: {system_data['efficiency']}%."
            return "Run calculation first to determine efficiency."

        if any(k in clean for k in ["summary", "status", "telemetry", "report"]):
            if has_calc:
                return (
                    f"⚡ Live System Telemetry:\n"
                    f"• V_R: {system_data['vr']} kV | Regulation: {system_data['regulation']}%\n"
                    f"• Losses: {system_data['losses']} kW | Efficiency: {system_data['efficiency']}%\n"
                    f"• Model: {system_data['model']} | Length: {system_data.get('length')} km"
                )
            return f"System Setup: {system_data.get('voltage')}, {system_data.get('length')} km, {system_data.get('conductor')}. (Click Calculate for outputs)"

        return None

    def _handle_math_expression(self, text):
        """Safely compute math calculations."""
        m = re.search(r"(?:calculate|compute|solve|what is)\s+([0-9\.\s\+\-\*\/\(\)\^e]+)", text, re.IGNORECASE)
        if m:
            expr = m.group(1).replace("^", "**").strip()
            if re.fullmatch(r"^[0-9\.\s\+\-\*\/\(\)]+$", expr):
                try:
                    res = eval(expr, {"__builtins__": None, "math": math, "sqrt": math.sqrt, "pi": math.pi})
                    return f"{expr} = {res:.6g}"
                except Exception as e:
                    return f"Error: {e}"
        return None

    def reply(self, message, system_data=None):
        """Generate concise, accurate response using offline engine + Cloud fallback."""
        if not message:
            return "Please enter a question or calculation."

        clean = self._normalize_text(message)

        # 1. Greetings
        if clean in ("hi", "hello", "hey", "help", "start"):
            resp = (
                "Hello! Power System Assistant ready.\n"
                "Ask any question about transmission lines, calculations, formulas, or active results."
            )
            self.record_turn(message, resp)
            return resp

        # 2. Conductor spacing questions (typo-tolerant)
        spacing_resp = self._handle_conductor_spacing_questions(clean)
        if spacing_resp:
            self.record_turn(message, spacing_resp)
            return spacing_resp

        # 3. Line length questions
        length_resp = self._handle_line_length_questions(clean)
        if length_resp:
            self.record_turn(message, length_resp)
            return length_resp

        # 4. Parametric what-if comparative simulation
        what_if_resp = self._handle_what_if_comparative_sim(clean, system_data)
        if what_if_resp:
            self.record_turn(message, what_if_resp)
            return what_if_resp

        # 5. Local Knowledge Dictionary lookup (e.g., 'what is inductive reactance')
        for item in self.knowledge_dict.values():
            if any(k in clean for k in item["keywords"]):
                resp = item["answer"]
                self.record_turn(message, resp)
                return resp

        # 6. Live App Telemetry
        state_resp = self._handle_system_state_query(clean, system_data)
        if state_resp:
            self.record_turn(message, state_resp)
            return state_resp

        # 7. Math expressions
        math_resp = self._handle_math_expression(message)
        if math_resp:
            self.record_turn(message, math_resp)
            return math_resp

        # 8. Cloud API Fallback (RAG / Online summary for any other queries)
        cloud_resp = self._query_cloud_api(clean)
        if cloud_resp:
            self.record_turn(message, cloud_resp)
            return cloud_resp

        # 9. Clean concise fallback
        default_resp = (
            "Could you clarify your question? You can ask about:\n"
            "• Inductive or capacitive reactance formulas\n"
            "• Effects of line length or conductor spacing\n"
            "• System simulations (e.g. 'what if frequency is 60 Hz')\n"
            "• Live system status (regulation %, losses kW, efficiency %)"
        )
        self.record_turn(message, default_resp)
        return default_resp