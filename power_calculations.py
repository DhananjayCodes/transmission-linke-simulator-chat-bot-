"""Power Engineering Calculation Engine for Transmission Line Analysis.
This module provides standard IEEE / IEC transmission line parameter calculations,
enabling offline, analytical answering and verification.
"""

import math
import cmath

EPS0 = 8.8541878128e-12
MU0 = 4 * math.pi * 1e-7
ALUMINUM_RHO = 2.82e-8

CONDUCTOR_DATABASE = {
    "ACSR Weasel": {"radius_mm": 3.25, "rdc": 0.272, "stranding": "6/1"},
    "ACSR Rabbit": {"radius_mm": 4.12, "rdc": 0.184, "stranding": "6/1"},
    "ACSR Dog": {"radius_mm": 4.72, "rdc": 0.139, "stranding": "6/7"},
    "ACSR Panther": {"radius_mm": 6.00, "rdc": 0.070, "stranding": "30/7"},
    "ACSR Zebra": {"radius_mm": 7.50, "rdc": 0.046, "stranding": "54/7"},
    "Custom": {"radius_mm": 5.00, "rdc": 0.100, "stranding": "Generic"},
}

def calculate_gmd(spacing_m, topology="Equilateral/Triangular"):
    """Calculate Geometric Mean Distance (GMD) in meters."""
    if topology == "Equilateral/Triangular":
        return spacing_m
    elif topology in ("Horizontal", "Vertical"):
        # For horizontal or vertical 3-phase line with equal spacing D between adjacent conductors:
        # D12 = D, D23 = D, D31 = 2D -> GMD = (D * D * 2D)^(1/3) = D * 2^(1/3)
        return spacing_m * (2 ** (1 / 3))
    return spacing_m

def calculate_skin_depth(frequency_hz=50.0, rho=ALUMINUM_RHO, mu=MU0):
    """Skin depth delta in meters."""
    omega = 2 * math.pi * max(1e-3, frequency_hz)
    return math.sqrt(2 * rho / (omega * mu))

def calculate_rac(rdc_per_km, radius_m, frequency_hz=50.0):
    """Calculate AC resistance per km accounting for skin effect."""
    delta = calculate_skin_depth(frequency_hz)
    skin_factor = 1.0 + ((radius_m / delta) ** 4) / 48.0
    return rdc_per_km * skin_factor

def calculate_inductance(gmd_m, radius_m):
    """Calculate inductance in Henry per meter (H/m) and per km (mH/km).
    GMR = 0.7788 * radius for solid round conductor approximation.
    """
    gmr_m = 0.7788 * radius_m
    l_h_per_m = 2e-7 * math.log(gmd_m / gmr_m)
    l_mh_per_km = l_h_per_m * 1000 * 1000  # H/m -> mH/km
    return l_h_per_m, l_mh_per_km

def calculate_capacitance(gmd_m, radius_m):
    """Calculate capacitance in Farad per meter (F/m) and microfarad per km (uF/km)."""
    c_f_per_m = 2 * math.pi * EPS0 / math.log(gmd_m / radius_m)
    c_uf_per_km = c_f_per_m * 1e6 * 1000  # F/m -> uF/km
    return c_f_per_m, c_uf_per_km

def determine_line_model(length_km):
    """Classify transmission line model based on length."""
    if length_km < 80:
        return "SHORT LINE"
    elif length_km <= 240:
        return "MEDIUM LINE (NOMINAL-π)"
    else:
        return "LONG LINE (DISTRIBUTED)"

def calculate_full_system(vk_kv, f_hz, length_km, spacing_m, radius_mm, rdc_ohm_per_km,
                          topology="Equilateral/Triangular", load_mw=50.0, pf=0.85):
    """Perform complete analytical power flow & ABCD evaluation."""
    radius_m = radius_mm / 1000.0
    vk = vk_kv * 1000.0  # Line-to-line V
    gmd = calculate_gmd(spacing_m, topology)
    omega = 2 * math.pi * f_hz

    # Parameters per km
    rac_km = calculate_rac(rdc_ohm_per_km, radius_m, f_hz)
    _, l_mh_km = calculate_inductance(gmd, radius_m)
    l_h_km = l_mh_km / 1000.0  # H/km
    _, c_uf_km = calculate_capacitance(gmd, radius_m)
    c_f_km = c_uf_km / 1e6  # F/km

    # Total parameters
    total_rac = rac_km * length_km
    total_inductance_mh = l_mh_km * length_km
    total_capacitance_uf = c_uf_km * length_km

    # Impedance & Admittance
    z_per_km = complex(rac_km, omega * l_h_km)
    y_per_km = complex(0, omega * c_f_km)
    Z = z_per_km * length_km
    Y = y_per_km * length_km

    model = determine_line_model(length_km)

    if length_km < 80:
        A = 1.0 + 0j
        B = Z
        C = 0j
        D = 1.0 + 0j
    elif length_km <= 240:
        A = 1.0 + (Y * Z) / 2.0
        B = Z
        C = Y * (1.0 + (Y * Z) / 4.0)
        D = 1.0 + (Y * Z) / 2.0
    else:
        gamma = cmath.sqrt(z_per_km * y_per_km)
        zc = cmath.sqrt(z_per_km / y_per_km)
        A = cmath.cosh(gamma * length_km)
        D = A
        B = zc * cmath.sinh(gamma * length_km)
        C = cmath.sinh(gamma * length_km) / zc

    # Voltages & Currents
    vs = vk / math.sqrt(3.0)  # Sending phase voltage
    noload_phase = abs(vs / A)
    noload_line_kv = noload_phase * math.sqrt(3.0) / 1000.0
    ferranti_rise_pct = ((noload_line_kv - vk_kv) / vk_kv) * 100.0

    # Iterative receiving-end voltage under load
    load_watts = load_mw * 1e6
    angle = math.acos(max(0.01, min(1.0, pf)))
    S_3ph = (load_watts / pf) * complex(math.cos(angle), math.sin(angle))
    
    vr = vs / A
    for _ in range(100):
        ir = (S_3ph / (3.0 * vr)).conjugate()
        new_vr = (vs - B * ir) / A
        if abs(new_vr - vr) < 1e-5:
            break
        vr = new_vr

    vr_line_kv = abs(vr) * math.sqrt(3.0) / 1000.0
    ir_mag = abs(S_3ph / (3.0 * vr))
    losses_watts = max(0.0, 3.0 * (ir_mag ** 2) * (B.real if B else 0.0))
    losses_kw = losses_watts / 1000.0
    reg_pct = ((vk_kv - vr_line_kv) / vr_line_kv) * 100.0
    efficiency_pct = (load_watts / (load_watts + losses_watts)) * 100.0 if load_watts > 0 else 0.0

    return {
        "model": model,
        "rac_ohm": total_rac,
        "inductance_mh": total_inductance_mh,
        "capacitance_uf": total_capacitance_uf,
        "vr_kv": vr_line_kv,
        "regulation_pct": reg_pct,
        "losses_kw": losses_kw,
        "efficiency_pct": efficiency_pct,
        "noload_kv": noload_line_kv,
        "ferranti_rise_pct": ferranti_rise_pct,
        "A": A,
        "B": B,
        "C": C,
        "D": D,
    }
