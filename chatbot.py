"""Industrial-Grade Power System Chatbot Engine.
Features:
1. Universal Typo & Spelling Auto-Correction (using difflib fuzzy vocabulary matching).
2. Deep Domain Knowledge: Comprehensive offline IEEE/IEC definitions & formulas.
3. Dual-Intent Routing:
   - Recognizes both conceptual questions (e.g. "what is receiving end voltage", "what is sending end voltage")
     AND telemetry requests (e.g. "current receiving voltage", "calculated Vr").
   - If not calculated yet on screen, gives the engineering concept & formula AND reports the software state.
4. Direct calculation & what-if parametric comparison engine.
5. Optional local LLM fallback (Ollama) for broad natural-language questions.
6. Clean conversation memory (Clear Screen vs. Persistent History Audit Trail).
"""

import math
import re
import difflib
from datetime import datetime
from local_llm import LocalLLM
from power_calculations import (
    calculate_full_system,
    calculate_gmd,
    calculate_rac,
    calculate_inductance,
    calculate_capacitance,
    determine_line_model,
    CONDUCTOR_DATABASE
)

DOMAIN_VOCABULARY = [
    "receiving", "sending", "voltage", "inductance", "inductive", "capacitance", "capacitive",
    "resistance", "resistive", "frequency", "reactance", "impedance", "admittance", "ferranti",
    "corona", "conductor", "conductors", "spacing", "distance", "regulation", "efficiency",
    "losses", "skin", "depth", "acsr", "weasel", "rabbit", "dog", "panther",
    "zebra", "surge", "characteristic", "active", "reactive", "apparent", "power",
    "factor", "equilateral", "triangular", "horizontal", "vertical", "hyperbolic",
    "propagation", "constant", "attenuation", "phase", "length", "transmission"
]


class Chatbot:
    """Industrial Power System AI Assistant with offline deterministic and LLM answers."""

    def __init__(self):
        self.name = "Industrial Power Assistant"
        self.history = []  # Persistent audit trail
        self._init_knowledge_base()
        self.local_llm = LocalLLM()

    def get_history(self):
        return list(self.history)

    def clear_history(self):
        self.history.clear()

    def record_turn(self, user_msg, bot_msg):
        now_str = datetime.now().strftime("%H:%M:%S")
        self.history.append({"timestamp": now_str, "role": "user", "message": user_msg})
        self.history.append({"timestamp": now_str, "role": "bot", "message": bot_msg})

    def _normalize_and_spellcheck(self, text):
        """Fix spelling errors, typos, and normalize tokens."""
        clean = text.lower().strip()

        # 1. Exact common typo mapping
        typo_map = {
            r"\bteh\b": "the",
            r"\breciving\b": "receiving",
            r"\breceveing\b": "receiving",
            r"\breceving\b": "receiving",
            r"\bsendng\b": "sending",
            r"\bsendeing\b": "sending",
            r"\binductence\b": "inductance",
            r"\binductace\b": "inductance",
            r"\bresistence\b": "resistance",
            r"\bresistancee\b": "resistance",
            r"\bcapacitence\b": "capacitance",
            r"\bcapacitace\b": "capacitance",
            r"\bfrequncy\b": "frequency",
            r"\bfreqency\b": "frequency",
            r"\breactence\b": "reactance",
            r"\bcondutor\b": "conductor",
            r"\bcondutors\b": "conductors",
            r"\btransmision\b": "transmission",
            r"\btransmisison\b": "transmission",
            r"\bferanti\b": "ferranti",
            r"\bcorna\b": "corona",
            r"\befficiencyy\b": "efficiency",
            r"\befficency\b": "efficiency",
            r"\bregultion\b": "regulation",
            r"\bvoltag\b": "voltage",
            r"\bvolatage\b": "voltage",
            r"\bvoltge\b": "voltage",
        }
        for pattern, replacement in typo_map.items():
            clean = re.sub(pattern, replacement, clean)

        # 2. Difflib fuzzy spelling match for words not in simple typo map
        tokens = clean.split()
        corrected_tokens = []
        for word in tokens:
            # Strip leading/trailing punctuation for check
            alpha_word = re.sub(r"[^\w]", "", word)
            if len(alpha_word) >= 5 and alpha_word not in DOMAIN_VOCABULARY:
                matches = difflib.get_close_matches(alpha_word, DOMAIN_VOCABULARY, n=1, cutoff=0.72)
                if matches:
                    corrected_tokens.append(matches[0])
                    continue
            corrected_tokens.append(word)

        return " ".join(corrected_tokens)

    def _init_knowledge_base(self):
        """Comprehensive dictionary of core engineering concepts, formulas, and parameters."""
        self.knowledge_dict = {
            # --- VOLTAGE CONCEPTS ---
            "receiving_end_voltage": {
                "keywords": ["receiving end voltage", "receiving voltage", "what is vr", "what is v_r"],
                "is_concept_query": lambda clean: any(k in clean for k in ["what is", "define", "explain", "meaning", "formula"]),
                "concept_answer": (
                    "Receiving-End Voltage (V_R):\n"
                    "• The voltage available at the load or substation terminal at the end of the transmission line.\n"
                    "• In three-phase systems, it is related to sending-end voltage (V_S) by: V_S = A·V_R + B·I_R.\n"
                    "• Under load, V_R typically drops below V_S due to line series impedance (I·Z drop).\n"
                    "• Under no-load or light load on long lines, V_R can exceed V_S (Ferranti Effect)."
                ),
            },
            "sending_end_voltage": {
                "keywords": ["sending end voltage", "sending voltage", "what is vs", "what is v_s"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Sending-End Voltage (V_S):\n"
                    "• The operating voltage supplied at the generating station or sending substation bus.\n"
                    "• Governed by the two-port equation: V_S = A·V_R + B·I_R.\n"
                    "• It must be maintained high enough to ensure the receiving-end voltage stays within statutory limits (±5%)."
                ),
            },
            "voltage_regulation": {
                "keywords": ["voltage regulation", "regulation percentage", "what is regulation"],
                "is_concept_query": lambda clean: any(k in clean for k in ["what is", "define", "explain", "meaning", "formula"]),
                "concept_answer": (
                    "Voltage Regulation (%):\n"
                    "• The percentage change in receiving-end voltage magnitude when full load is dropped to no-load:\n"
                    "  VR (%) = (|V_S / A| - |V_R|) / |V_R| × 100%\n"
                    "• Standard utility limit: Typically kept within 5.0% for grid stability."
                ),
            },
            "line_losses": {
                "keywords": ["line loss", "line losses", "power loss", "losses in transmission"],
                "is_concept_query": lambda clean: any(k in clean for k in ["what is", "define", "explain", "meaning", "formula"]),
                "concept_answer": (
                    "Line Losses (P_loss):\n"
                    "• The real power dissipated as heat in the conductors due to Joule heating: P_loss = 3 × |I_R|² × Re(B) kW.\n"
                    "• Reduced by raising transmission voltage (which lowers current I for the same MW load)."
                ),
            },
            "transmission_efficiency": {
                "keywords": ["transmission efficiency", "efficiency of line", "efficiency formula"],
                "is_concept_query": lambda clean: any(k in clean for k in ["what is", "define", "explain", "meaning", "formula"]),
                "concept_answer": (
                    "Transmission Efficiency (η):\n"
                    "• Ratio of real power delivered at receiving end to power supplied at sending end:\n"
                    "  η (%) = P_load / (P_load + P_loss) × 100%\n"
                    "• High-voltage overhead lines typically operate at 95% to 98% efficiency."
                ),
            },

            # --- REACTANCE, IMPEDANCE, ADMITTANCE ---
            "inductance": {
                "keywords": ["inductance"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Inductance (L):\n"
                    "• The property of a conductor or circuit that stores energy in its magnetic field when current flows.\n"
                    "• A changing current produces an induced voltage that opposes the change: v = L·di/dt.\n"
                    "• Measured in henry (H). In a transmission line, inductance depends mainly on phase spacing and conductor GMR.\n"
                    "• Larger phase spacing increases line inductance; a larger conductor radius increases GMR and slightly reduces it."
                ),
            },
            "capacitance": {
                "keywords": ["capacitance"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Capacitance (C):\n"
                    "• The ability of conductors separated by insulation or air to store electric charge and energy in an electric field.\n"
                    "• C = Q/V and is measured in farad (F).\n"
                    "• For an overhead line, capacitance increases with conductor radius and decreases as phase spacing increases."
                ),
            },
            "resistance": {
                "keywords": ["resistance"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Resistance (R):\n"
                    "• The opposition a material offers to electric current, causing real-power loss as heat.\n"
                    "• R = ρl/A, measured in ohms (Ω): it rises with length and falls with conductor cross-sectional area.\n"
                    "• In AC transmission lines, skin effect makes AC resistance slightly higher than DC resistance."
                ),
            },
            "current": {
                "keywords": ["current"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Electric Current (I):\n"
                    "• The rate of flow of electric charge, measured in amperes (A).\n"
                    "• In a balanced three-phase system, apparent power is S = √3·V_LL·I.\n"
                    "• Higher current increases conductor heating and I²R losses."
                ),
            },
            "voltage": {
                "keywords": ["voltage"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Voltage (V):\n"
                    "• Electric potential difference: energy available per unit charge between two points.\n"
                    "• Measured in volts (V). Transmission systems use high voltage to transfer the same power with lower current and lower I²R loss."
                ),
            },
            "topology": {
                "keywords": ["topology", "line configuration", "phase configuration"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Transmission-Line Topology:\n"
                    "• The physical arrangement of phase conductors in a line, such as equilateral/triangular, horizontal, or vertical.\n"
                    "• It determines the distances between phases (GMD), which affect inductance, capacitance, impedance, and voltage performance.\n"
                    "• In this simulator, Equilateral/Triangular has equal phase spacing; Horizontal and Vertical use equal adjacent spacing with the outer phases farther apart."
                ),
            },
            "inductive_reactance": {
                "keywords": ["inductive reactance", "formula for inductive reactance", "x_l", "xl"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Inductive Reactance (X_L = 2πfL = ωL):\n"
                    "• The opposition offered by conductor magnetic flux linkage to alternating current.\n"
                    "• Measured in Ohms (Ω).\n"
                    "• Proportional to frequency (f) and inductance (L). Higher frequency or longer line directly increases X_L."
                ),
            },
            "capacitive_reactance": {
                "keywords": ["capacitive reactance", "x_c", "xc"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Capacitive Reactance (X_C = 1 / (2πfC)):\n"
                    "• The opposition offered by electric field capacitance to alternating current.\n"
                    "• Measured in Ohms (Ω).\n"
                    "• Inversely proportional to frequency and capacitance. Higher frequency lowers X_C."
                ),
            },
            "reactance": {
                "keywords": ["what is reactance", "electrical reactance"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Reactance (X = X_L - X_C):\n"
                    "• Non-resistive opposition of electrical elements to AC current.\n"
                    "• Caused by energy storage in magnetic fields (Inductive, X_L) and electric fields (Capacitive, X_C)."
                ),
            },
            "impedance": {
                "keywords": ["what is impedance", "line impedance"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Impedance (Z = R + jX):\n"
                    "• Total opposition an AC circuit presents to current, combining AC resistance (R) and reactance (X).\n"
                    "• Measured in Ohms (Ω)."
                ),
            },
            "admittance": {
                "keywords": ["what is admittance", "line admittance"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Admittance (Y = G + jB = 1 / Z):\n"
                    "• Measure of how easily an AC circuit allows current to flow.\n"
                    "• Conductance (G) is real part; Susceptance (B) is imaginary part. Measured in Siemens (S)."
                ),
            },

            # --- PHENOMENA & HARDWARE ---
            "ferranti_effect": {
                "keywords": ["ferranti", "voltage rise"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Ferranti Effect:\n"
                    "• Phenomenon where receiving-end voltage exceeds sending-end voltage under no-load or light load on medium/long lines.\n"
                    "• Caused by line charging current flowing through series line inductance."
                ),
            },
            "skin_effect": {
                "keywords": ["skin effect", "skin depth"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Skin Effect:\n"
                    "• Tendency of AC current to concentrate near conductor surface, increasing effective AC resistance.\n"
                    "• Skin depth δ = √(2ρ / (ω·μ)). Decreases with higher frequency."
                ),
            },
            "abcd_parameters": {
                "keywords": ["abcd", "two port parameter"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "ABCD Parameters:\n"
                    "• Two-port matrix relating sending & receiving ends: V_S = A·V_R + B·I_R, I_S = C·V_R + D·I_R.\n"
                    "• For symmetrical lines: A = D. Reciprocity: A·D - B·C = 1."
                ),
            },
            "acsr": {
                "keywords": ["acsr"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "ACSR (Aluminum Conductor Steel Reinforced):\n"
                    "• Outer aluminum strands provide high conductivity; central steel core provides high tensile strength.\n"
                    "• Standard sizes: Weasel, Rabbit, Dog, Panther, Zebra."
                ),
            },
            "gmd_gmr": {
                "keywords": ["gmd", "gmr", "geometric mean distance"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "GMD & GMR:\n"
                    "• GMD (Geometric Mean Distance): Equivalent geometric distance between conductor phases.\n"
                    "• GMR (Geometric Mean Radius): Effective radius of conductor accounting for internal flux (r' = 0.7788·r)."
                ),
            },
            "surge_impedance": {
                "keywords": ["surge impedance", "sil", "characteristic impedance"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Surge Impedance (Zc) & SIL:\n"
                    "• Zc = √(L / C) ≈ 250–400 Ω for overhead lines.\n"
                    "• Surge Impedance Loading (SIL) = V_rated² / Zc: The load where line reactive power generated equals reactive power consumed."
                ),
            },
            "corona": {
                "keywords": ["corona"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Corona Effect:\n"
                    "• Ionization of air around high-voltage conductors when surface electric field exceeds air dielectric breakdown (~30 kV/cm peak).\n"
                    "• Causes power loss, ozone, and audible hiss. Reduced by increasing conductor diameter or using bundles."
                ),
            },
            "sag": {
                "keywords": ["sag", "tension"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Conductor Sag:\n"
                    "• S = (w · L²) / (8 · T), where w is weight per unit length, L is span length, T is tension.\n"
                    "• Increases with conductor temperature due to thermal expansion."
                ),
            },
            "power_factor": {
                "keywords": ["power factor", "lagging", "leading"],
                "is_concept_query": lambda clean: True,
                "concept_answer": (
                    "Power Factor (cos φ):\n"
                    "• Ratio of Real Power (P) to Apparent Power (S).\n"
                    "• Low lagging PF increases current and line losses; leading PF can cause voltage rise."
                ),
            }
        }

    def _build_system_context(self, system_data):
        """Provide active inputs/results to the local model without claiming unknown values."""
        if not system_data:
            return "No active simulation values."
        fields = ("voltage", "frequency", "length", "spacing", "radius", "conductor",
                  "load", "load_unit", "power_factor", "vr", "regulation", "losses",
                  "efficiency", "model")
        return "\n".join(f"{field}: {system_data[field]}" for field in fields
                         if system_data.get(field) not in (None, "", "—"))

    def _handle_conductor_radius_questions(self, clean):
        """Answer physical trends caused by a larger phase-conductor radius."""
        radius_terms = ("radius", "diameter", "conductor size", "conductor thickness")
        if not any(term in clean for term in radius_terms):
            return None
        if not any(term in clean for term in ("increase", "larger", "bigger", "change", "effect", "happen")):
            return None
        return (
            "When conductor radius increases (with line length and phase spacing fixed):\n"
            "• DC/AC resistance decreases because cross-sectional area increases; skin effect can moderate this at AC.\n"
            "• Inductance decreases slightly because GMR = 0.7788r increases.\n"
            "• Capacitance increases because ln(GMD/r) becomes smaller.\n"
            "• Surface electric field decreases, so corona performance improves.\n"
            "• Weight, cost, and usually sag loading increase, so mechanical design must also be checked."
        )

    def _handle_conductor_height_questions(self, clean):
        """Answer clearance/height changes using the conductor-to-ground model."""
        height_terms = ("height", "clearance", "above ground", "from ground", "ground distance")
        change_terms = ("increase", "higher", "raise", "raised", "change", "effect", "happen")
        if not any(term in clean for term in height_terms) or not any(term in clean for term in change_terms):
            return None
        return (
            "When conductor height above ground increases (with phase spacing and conductor size fixed):\n"
            "• Line-to-ground capacitance decreases because the electric-field path to ground is longer.\n"
            "• Charging current and capacitive reactive power decrease slightly.\n"
            "• Earth-return/self inductance increases slightly; phase-to-phase inductance is nearly unchanged when phase spacing is unchanged.\n"
            "• Ground-level electric field decreases, improving clearance and reducing induced effects near the ground.\n"
            "• Taller supports and greater mechanical loading increase cost; actual clearance must still be checked at maximum sag."
        )

    def _handle_conductor_spacing_questions(self, clean):
        """Answer conductor spacing questions concisely."""
        is_spacing = any(k in clean for k in ["distance", "spacing", "separation", "space"])
        is_conductor = any(k in clean for k in ["conductor", "conductors", "phase", "line"])

        if is_spacing and (is_conductor or "between" in clean):
            has_r = "resistance" in clean or "ac resistance" in clean
            has_l = "inductance" in clean or "inductive" in clean
            has_c = "capacitance" in clean or "capacitive" in clean

            if has_r and not has_l and not has_c:
                return (
                    "When conductor spacing/distance increases:\n"
                    "• Total Resistance: Remains approximately unchanged (constant), not significantly affected.\n"
                    "Reason: Resistance depends on conductor material, length, and cross-section, not spacing."
                )
            elif has_l and not has_r and not has_c:
                return (
                    "When conductor spacing/distance increases:\n"
                    "• Total Inductance: Increases (↑).\n"
                    "Reason: L = (μ₀/2π)·ln(GMD/GMR). Higher GMD increases magnetic flux linkage."
                )
            elif has_c and not has_r and not has_l:
                return (
                    "When conductor spacing/distance increases:\n"
                    "• Total Capacitance: Decreases (↓).\n"
                    "Reason: C = 2πε₀/ln(GMD/r). Larger separation reduces electric-field coupling."
                )
            else:
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
                    "Reason: R = r_per_km × Length."
                )
            elif has_l and not has_r and not has_c:
                return (
                    "When transmission line length increases:\n"
                    "• Total Inductance: Increases (↑).\n"
                    "Reason: L_total = L_per_km × Length."
                )
            elif has_c and not has_r and not has_l:
                return (
                    "When transmission line length increases:\n"
                    "• Total Capacitance: Increases (↑).\n"
                    "Reason: C_total = C_per_km × Length."
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
        has_change_trigger = any(k in clean for k in [
            "what if", "if i change", "change", "increase", "decrease", "set", "at", "what would", "calculate for"
        ])
        if not has_change_trigger:
            return None

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

        m = re.search(r"(?:frequency|freq|hz)\s*(?:to|is|=|of)?\s*(\d+(?:\.\d+)?)\s*(?:hz)?", clean)
        if not m:
            m = re.search(r"(\d+(?:\.\d+)?)\s*hz", clean)
        if m:
            val = float(m.group(1))
            if 10 <= val <= 500:
                target_f = val
                detected = True
                desc = f"Frequency: {cur_f} Hz → {target_f} Hz"

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

        if not detected:
            m = re.search(r"(?:load|power)\s*(?:to|is|=|of)?\s*(\d+(?:\.\d+)?)\s*(?:mw)?", clean)
            if m:
                val = float(m.group(1))
                if val > 0:
                    target_load = val
                    detected = True
                    desc = f"Load: {cur_load} MW → {target_load} MW"

        if not detected:
            m = re.search(r"spacing\s*(?:d)?\s*(?:to|is|=|of)?\s*(\d+(?:\.\d+)?)\s*(?:m|meters)?", clean)
            if m:
                val = float(m.group(1))
                if val > 0:
                    target_spacing = val
                    detected = True
                    desc = f"Spacing: {cur_spacing} m → {target_spacing} m"

        if not detected:
            m = re.search(r"(?:radius|diameter)\s*(?:to|is|=|of)?\s*(\d+(?:\.\d+)?)\s*(?:mm)?", clean)
            if m:
                val = float(m.group(1))
                if val > 0:
                    target_radius = val
                    detected = True
                    desc = f"Conductor radius: {cur_radius} mm → {target_radius} mm"

        if detected:
            base_res = calculate_full_system(cur_v, cur_f, cur_len, cur_spacing, cur_radius, cur_rdc, cur_top, cur_load, cur_pf)
            new_res = calculate_full_system(target_v, target_f, target_len, target_spacing, target_radius, target_rdc, target_top, target_load, target_pf)

            return (
                f"🔬 Calculation Result ({desc}):\n"
                f"• Receiving Voltage (Vr): {base_res['vr_kv']:.2f} kV → {new_res['vr_kv']:.2f} kV\n"
                f"• Voltage Regulation: {base_res['regulation_pct']:.2f}% → {new_res['regulation_pct']:.2f}%\n"
                f"• Line Losses: {base_res['losses_kw']:.1f} kW → {new_res['losses_kw']:.1f} kW\n"
                f"• Total Inductance: {base_res['inductance_mh']:.2f} mH → {new_res['inductance_mh']:.2f} mH\n"
                f"• Total Capacitance: {base_res['capacitance_uf']:.4f} µF → {new_res['capacitance_uf']:.4f} µF\n"
                f"• Efficiency: {base_res['efficiency_pct']:.2f}% → {new_res['efficiency_pct']:.2f}%\n"
                f"• Model: {new_res['model']}"
            )
        return None

    def _handle_system_state_or_concept(self, clean, system_data):
        """Unified resolver that can answer both Concept Definitions and Live Telemetry."""
        has_calc = system_data and system_data.get("vr") not in (None, "", "—")
        is_concept_prompt = any(k in clean for k in ["what is", "define", "explain", "meaning", "concept", "formula", "theory"])

        # 1. Receiving End Voltage
        if any(k in clean for k in ["receiving end voltage", "receiving voltage", "reciving end voltage", "vr", "v_r"]):
            concept = (
                "Receiving-End Voltage (V_R):\n"
                "• The voltage measured at the load end of the transmission line.\n"
                "• In ABCD parameter modeling: V_S = A·V_R + B·I_R."
            )
            if has_calc:
                val = system_data["vr"]
                return f"{concept}\n\n⚡ Active System Value: V_R = {val} kV (Line-to-Line)."
            elif is_concept_prompt:
                return f"{concept}\n\n(Tip: Click 'CALCULATE SYSTEM PARAMETERS' to compute the active system V_R)."
            else:
                return "The receiving-end voltage has not been computed yet. Click 'CALCULATE SYSTEM PARAMETERS' to evaluate."

        # 2. Sending End Voltage
        if any(k in clean for k in ["sending end voltage", "sending voltage", "vs", "v_s"]):
            concept = (
                "Sending-End Voltage (V_S):\n"
                "• The voltage supplied by the generator or substation at the transmission line inlet.\n"
                "• Relates to receiving end by: V_S = A·V_R + B·I_R."
            )
            val = system_data.get("voltage", "132 kV") if system_data else "132 kV"
            return f"{concept}\n\n⚡ Active System Value: V_S = {val}."

        # 3. Voltage Regulation
        if any(k in clean for k in ["voltage regulation", "regulation", "reg %"]):
            concept = (
                "Voltage Regulation (%):\n"
                "• VR (%) = (|V_S / A| - |V_R|) / |V_R| × 100%.\n"
                "• Indicates percentage change in voltage at receiving end from full-load to no-load."
            )
            if has_calc:
                val = system_data["regulation"]
                status = "Within 5% IEEE limit." if float(val) <= 5.0 else "Exceeds 5% statutory limit!"
                return f"{concept}\n\n⚡ Active System Value: {val}% ({status})."
            elif is_concept_prompt:
                return f"{concept}\n\n(Tip: Click 'CALCULATE SYSTEM PARAMETERS' to compute regulation for current inputs)."
            else:
                return "Voltage regulation has not been computed yet. Click 'CALCULATE SYSTEM PARAMETERS'."

        # 4. Line Losses
        if any(k in clean for k in ["losses", "loss", "line loss", "power loss"]):
            concept = (
                "Line Losses (P_loss):\n"
                "• Power dissipated as heat due to line resistance: P_loss = 3 × |I_R|² × Re(B) kW."
            )
            if has_calc:
                val = system_data["losses"]
                return f"{concept}\n\n⚡ Active System Value: Line Losses = {val} kW."
            elif is_concept_prompt:
                return f"{concept}\n\n(Tip: Click 'CALCULATE SYSTEM PARAMETERS' to evaluate losses)."
            else:
                return "Line losses are not calculated yet. Click 'CALCULATE SYSTEM PARAMETERS'."

        # 5. Efficiency
        if any(k in clean for k in ["efficiency"]):
            concept = (
                "Transmission Efficiency (η):\n"
                "• η = P_load / (P_load + P_loss) × 100%."
            )
            if has_calc:
                val = system_data["efficiency"]
                return f"{concept}\n\n⚡ Active System Value: Transmission Efficiency = {val}%."
            elif is_concept_prompt:
                return f"{concept}\n\n(Tip: Click 'CALCULATE SYSTEM PARAMETERS' to evaluate efficiency)."
            else:
                return "Efficiency has not been computed yet. Click 'CALCULATE SYSTEM PARAMETERS'."

        # 6. Current Resistance (telemetry)
        if any(k in clean for k in ["current resistance", "calculated resistance", "what is rac", "what is total resistance"]):
            if has_calc and "rac" in system_data:
                return f"Total AC Resistance: {system_data['rac']} Ω for {system_data.get('length')} km."
            return "Total AC resistance has not been computed yet."

        # 7. Current Inductance (telemetry)
        if any(k in clean for k in ["current inductance", "calculated inductance", "what is total inductance"]):
            if has_calc and "inductance" in system_data:
                return f"Total Inductance: {system_data['inductance']} mH for {system_data.get('length')} km."
            return "Total inductance has not been computed yet."

        # 8. Summary / Status
        if any(k in clean for k in ["summary", "status", "telemetry", "report"]):
            if has_calc:
                return (
                    f"⚡ Live System Telemetry:\n"
                    f"• V_S: {system_data.get('voltage')} | V_R: {system_data['vr']} kV\n"
                    f"• Regulation: {system_data['regulation']}% | Losses: {system_data['losses']} kW\n"
                    f"• Efficiency: {system_data['efficiency']}% | Model: {system_data['model']}\n"
                    f"• Line Length: {system_data.get('length')} km | Conductor: {system_data.get('conductor')}"
                )
            return (
                f"⚡ Current System Setup:\n"
                f"• Voltage: {system_data.get('voltage', '132 kV')} | Length: {system_data.get('length', '150')} km\n"
                f"• Conductor: {system_data.get('conductor', 'ACSR Zebra')} | Load: {system_data.get('load', '50')} {system_data.get('load_unit', 'MW')}\n"
                f"(Click 'CALCULATE SYSTEM PARAMETERS' to generate performance outputs)."
            )

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
        """Generate concise, accurate responses using offline calculations and a local LLM."""
        if not message:
            return "Please enter a question or calculation."

        # 1. Fuzzy spell-check & text normalization
        clean = self._normalize_and_spellcheck(message)

        # 2. Greetings
        if clean in ("hi", "hello", "hey", "help", "start"):
            resp = (
                "Hello! Power System Assistant ready.\n"
                "Ask any question about transmission lines, calculations, formulas, or active results."
            )
            self.record_turn(message, resp)
            return resp

        # 3. Direct geometry questions take priority over general language answers.
        radius_resp = self._handle_conductor_radius_questions(clean)
        if radius_resp:
            self.record_turn(message, radius_resp)
            return radius_resp

        height_resp = self._handle_conductor_height_questions(clean)
        if height_resp:
            self.record_turn(message, height_resp)
            return height_resp

        # 4. Conductor spacing questions (typo-tolerant)
        spacing_resp = self._handle_conductor_spacing_questions(clean)
        if spacing_resp:
            self.record_turn(message, spacing_resp)
            return spacing_resp

        # 5. Line length questions
        length_resp = self._handle_line_length_questions(clean)
        if length_resp:
            self.record_turn(message, length_resp)
            return length_resp

        # 6. Parametric what-if comparative simulation
        what_if_resp = self._handle_what_if_comparative_sim(clean, system_data)
        if what_if_resp:
            self.record_turn(message, what_if_resp)
            return what_if_resp

        # 7. Combined Concept & Telemetry Handler (Sending Voltage, Receiving Voltage, Regulation, Losses, etc.)
        state_or_concept = self._handle_system_state_or_concept(clean, system_data)
        if state_or_concept:
            self.record_turn(message, state_or_concept)
            return state_or_concept

        # 8. Local Knowledge Dictionary lookup (e.g. inductive reactance, skin effect, Ferranti)
        for item in self.knowledge_dict.values():
            if any(k in clean for k in item["keywords"]):
                resp = item["concept_answer"]
                self.record_turn(message, resp)
                return resp

        # 9. Math expressions
        math_resp = self._handle_math_expression(message)
        if math_resp:
            self.record_turn(message, math_resp)
            return math_resp

        # 10. Open-ended questions go to an optional, locally hosted LLM only.
        local_response = self.local_llm.answer(message, self._build_system_context(system_data))
        if local_response:
            self.record_turn(message, local_response)
            return local_response

        # 11. Clean offline fallback
        default_resp = (
            "I can answer this with a local language model once one is installed. "
            "For the offline engine now, ask about:\n"
            "• Receiving or sending-end voltages (definitions or live values)\n"
            "• Inductive or capacitive reactance formulas\n"
            "• Effects of line length or conductor spacing\n"
            "• System simulations (e.g. 'what if frequency is 60 Hz')"
        )
        self.record_turn(message, default_resp)
        return default_resp
