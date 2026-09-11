# ⚡ TransLine-Sim

### Retro Transmission Line Analysis & Power System Simulator

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python\&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Build](https://img.shields.io/badge/Build-Passing-brightgreen.svg)](#)
[![Issues](https://img.shields.io/github/issues/YOUR_USERNAME/TransLine-Sim)](https://github.com/YOUR_USERNAME/TransLine-Sim/issues)
[![Stars](https://img.shields.io/github/stars/YOUR_USERNAME/TransLine-Sim?style=social)](https://github.com/YOUR_USERNAME/TransLine-Sim/stargazers)

> **A retro-inspired engineering workstation for analyzing, visualizing, and understanding electrical transmission lines.**

**TransLine-Sim** is an open-source desktop engineering simulator built with **Python and Tkinter** for electrical engineering students, power-system engineers, and grid planners. It combines transmission-line parameter calculations, ABCD network modeling, performance analysis, and an interactive **Single Line Diagram (SLD)** into one lightweight desktop application.

---

## 📑 Table of Contents

* [✨ Key Features](#-key-features)
* [⚡ Built-In Conductor Database](#-built-in-conductor-database)
* [📐 Mathematical Foundations](#-mathematical-foundations)
* [🖥️ Interface & Schematic Engine](#️-interface--schematic-engine)
* [🔄 Analysis Modes](#-analysis-modes)
* [🏗️ Application Architecture](#️-application-architecture)
* [🚀 Installation](#-installation)
* [⚡ Quick Start](#-quick-start)
* [📊 Analysis Workflow](#-analysis-workflow)
* [🗺️ Roadmap](#️-roadmap)
* [🤝 Contributing](#-contributing)
* [📜 License](#-license)
* [🙏 Acknowledgments](#-acknowledgments)

---

## ✨ Key Features

### 🧮 Dynamic Physical Parameter Engine

Automatically calculates the electrical and physical parameters required for transmission-line analysis:

* **GMD — Geometric Mean Distance**
* **GMR — Geometric Mean Radius**
* **DC Resistance**
* **AC Resistance ($R_{ac}$)**
* **Skin-effect correction**
* **Inductance ($L$)**
* **Capacitance ($C$)**
* Conductor-dependent electrical characteristics
* Custom conductor configuration

> 💡 **Engineering-first design:** Instead of treating transmission-line parameters as fixed values, TransLine-Sim derives them from conductor geometry and operating conditions.

---

### 🔢 ABCD Matrix Solver

The simulator automatically selects the appropriate mathematical model according to transmission-line length.

| Line Model      | Typical Application      | Mathematical Model                        |
| --------------- | ------------------------ | ----------------------------------------- |
| **Short Line**  | Short transmission lines | Series impedance                          |
| **Medium Line** | Medium-distance lines    | Nominal-$\pi$                             |
| **Long Line**   | Long EHV/UHV lines       | Distributed parameters / Hyperbolic model |

The ABCD engine evaluates:

$$
\begin{bmatrix}
V_S \
I_S
\end{bmatrix}
=============

\begin{bmatrix}
A & B \
C & D
\end{bmatrix}
\begin{bmatrix}
V_R \
I_R
\end{bmatrix}
$$

This allows the same analysis framework to determine sending-end and receiving-end operating conditions.

---

### 📈 Performance & Stability Metrics

TransLine-Sim provides real-time engineering results including:

* 📉 Voltage drop
* 📊 Voltage regulation (%)
* 🔥 $I^2R$ transmission losses
* ⚡ Sending-end power
* ⚡ Receiving-end power
* 🎯 Transmission efficiency (%)
* 🔋 Reactive power behavior
* 📈 No-load voltage rise
* ⚠️ Ferranti-effect detection
* 🔌 Sending-end current and voltage
* 🔌 Receiving-end current and voltage

---

### 🖥️ Interactive Retro CAD Schematic Canvas

A built-in **Tkinter Canvas-based vector graphics engine** provides a visual representation of the transmission system.

The schematic can represent:

* 🏭 Generating stations
* ⚡ Transmission buses
* 🗼 Lattice transmission towers
  -〰️ Catenary phase conductors
* 🔌 Receiving substations
* 📏 Transmission-line spans
* 📡 Phase conductors
* 📊 Dynamic engineering parameter callouts

The schematic redraws dynamically as simulation parameters change.

> 🛠️ **No external CAD software required.** The SLD is generated directly inside the application using Tkinter vector primitives.

---

### 🔄 Dual Analysis Modes

#### Forward Mode

Start with known operating conditions and determine transmission performance.

**Input → Simulation → Performance**

Typical inputs include:

* Sending voltage
* Receiving-end load
* Power factor
* Line length
* Conductor selection
* Frequency
* Conductor geometry

---

#### Reverse Mode

Work backward from system constraints to determine the **maximum permissible loadability**.

**System Limit → Iterative Analysis → Maximum Load**

This mode can be useful for exploring:

* Maximum transferable power
* Voltage constraints
* Thermal limitations
* Regulation limits
* Operating margins

---

# ⚡ Built-In Conductor Database

TransLine-Sim includes a pre-configured conductor database containing commonly used **ACSR (Aluminium Conductor Steel Reinforced)** transmission conductors.

### Included Conductors

| Conductor   | Type | Typical Use                     |
| ----------- | ---- | ------------------------------- |
| **Weasel**  | ACSR | Distribution / transmission     |
| **Rabbit**  | ACSR | Distribution / transmission     |
| **Dog**     | ACSR | Transmission                    |
| **Panther** | ACSR | High-voltage transmission       |
| **Zebra**   | ACSR | High-voltage / EHV transmission |

The database can be extended with **custom conductor parameters**, allowing users to model conductors outside the built-in library.

### Custom Conductor Support

Users can define parameters such as:

* Conductor diameter
* Resistance
* GMR
* Number of subconductors
* Bundle spacing
* Conductor geometry
* Frequency-dependent parameters

This makes the simulator suitable for both **educational experiments and custom engineering studies**.

---

# 📐 Mathematical Foundations

TransLine-Sim is based on classical transmission-line theory and distributed-parameter power-system models.

## Geometric Mean Distance

For a simplified two-conductor arrangement:

$$
GMD = \sqrt{D_{12}D_{23}\cdots D_{n1}}
$$

For symmetrical arrangements, GMD represents the effective geometric spacing between conductors.

---

## Geometric Mean Radius

For a conductor:

$$
GMR \approx 0.7788r
$$

where:

* $r$ = physical conductor radius
* $GMR$ = geometric mean radius

For bundled conductors, the equivalent GMR is calculated from the bundle geometry.

---

## Inductance

A simplified transmission-line inductance relationship is:

$$
L = 2\times10^{-7}
\ln\left(\frac{GMD}{GMR}\right)
\quad H/m
$$

The inductive reactance is then:

$$
X_L = 2\pi fL
$$

---

## Capacitance

The capacitance per unit length can be represented by:

$$
C =
\frac{2\pi\varepsilon}
{\ln(GMD/r)}
$$

where $\varepsilon$ represents the permittivity of the surrounding medium.

---

## AC Resistance & Skin Effect

At higher frequencies, current distribution becomes non-uniform across the conductor cross-section.

TransLine-Sim applies a skin-effect correction to obtain:

$$
R_{ac}=R_{dc}\times K_{skin}
$$

where:

* $R_{dc}$ = DC resistance
* $K_{skin}$ = skin-effect correction factor

The exact correction depends on conductor and operating-frequency parameters.

---

## Long-Line Hyperbolic Model

For a distributed transmission line:

$$
A=D=\cosh(\gamma l)
$$

$$
B=Z_c\sinh(\gamma l)
$$

$$
C=\frac{1}{Z_c}\sinh(\gamma l)
$$

where:

$$
\gamma=\sqrt{ZY}
$$

and

$$
Z_c=\sqrt{\frac{Z}{Y}}
$$

Here:

* $Z$ = series impedance per unit length
* $Y$ = shunt admittance per unit length
* $\gamma$ = propagation constant
* $Z_c$ = characteristic impedance
* $l$ = line length

These equations allow the simulator to model the behavior of long transmission lines using distributed parameters.

---

# 🖥️ Interface & Schematic Engine

TransLine-Sim intentionally uses a **retro engineering-workstation aesthetic** rather than a modern web-dashboard design.

The interface combines:

* 🖱️ Tkinter desktop controls
* 📐 CAD-style schematic graphics
* 🧮 Engineering calculation panels
* 📊 Numerical result tables
* 🗼 Transmission tower visualization
* 📋 Parameter callouts
* 🟦 Classic retro GUI styling

The goal is not simply visual nostalgia—the interface is designed to make the simulator feel like a compact **engineering analysis workstation**.

---

# 🔄 Analysis Modes

## Forward Analysis

```text
Conductor + Line + Load
          │
          ▼
 Physical Parameter Engine
          │
          ▼
   ABCD Line Model
          │
          ▼
 Sending-End Conditions
          │
          ▼
 Performance Metrics
```

### Outputs

* Sending-end voltage
* Sending-end current
* Receiving-end voltage
* Receiving-end current
* Voltage regulation
* Power losses
* Efficiency
* Reactive power
* Ferranti-effect behavior

---

## Reverse Analysis

```text
System Constraints
        │
        ▼
 Candidate Load
        │
        ▼
 ABCD Network Calculation
        │
        ▼
 Constraint Check
        │
   ┌────┴────┐
   │         │
 Valid     Invalid
   │         │
   ▼         ▼
Increase   Reduce
Load       Load
   │         │
   └────┬────┘
        ▼
 Maximum Loadability
```

---

# 🏗️ Application Architecture

The application follows a modular engineering workflow where the GUI collects system information, the calculation engine processes electrical parameters, and the visualization layer presents the resulting system state.

```text
┌──────────────────────────────┐
│        Tkinter GUI           │
│                              │
│  Line Data / Load / Voltage  │
│  Conductor / Frequency       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ Physical Parameter Engine    │
│                              │
│ GMD / GMR / R / L / C        │
│ Skin Effect / Geometry       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│      ABCD Matrix Engine      │
│                              │
│ Short / Medium / Long Line   │
│ Nominal-π / Hyperbolic       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│   Power System Calculations  │
│                              │
│ Regulation / Loss /          │
│ Efficiency / Ferranti Effect │
└──────────────┬───────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐  ┌────────────────┐
│ Results Table│  │ Dynamic SLD    │
│              │  │ Canvas Redraw  │
└──────────────┘  └────────────────┘
```

---

# 📁 Suggested Project Structure

```text
TransLine-Sim/
│
├── main.py
├── README.md
├── LICENSE
├── requirements.txt
│
├── assets/
│   └── ...
│
├── data/
│   └── conductors.json
│
├── core/
│   ├── parameters.py
│   ├── abcd.py
│   ├── conductor.py
│   └── analysis.py
│
├── gui/
│   ├── main_window.py
│   ├── canvas.py
│   └── widgets.py
│
└── tests/
    └── ...
```

> 📌 The exact structure may evolve as the simulator grows. The objective is to keep **engineering calculations, conductor data, GUI components, and visualization logic** independently maintainable.

---

# 🚀 Installation

## Prerequisites

Make sure your system has:

* **Python 3.8 or newer**
* Git
* Tkinter
* A desktop environment capable of running Tkinter applications

Check your Python installation:

```bash
python3 --version
```

Expected:

```text
Python 3.8+
```

---

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/TransLine-Sim.git
cd TransLine-Sim
```

---

## 2. Create a Virtual Environment

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If Tkinter is not installed on a Debian/Ubuntu-based Linux system:

```bash
sudo apt install python3-tk
```

---

# ⚡ Quick Start

After installation, launch the simulator with:

```bash
python main.py
```

or:

```bash
python3 main.py
```

### Typical workflow

1. Select a conductor.
2. Enter transmission-line length.
3. Configure conductor geometry.
4. Set system voltage and frequency.
5. Enter receiving-end load.
6. Select operating mode.
7. Run the analysis.
8. Inspect the ABCD parameters.
9. Review voltage regulation, losses, and efficiency.
10. Observe the dynamically updated transmission-line schematic.

---

# 📊 Analysis Workflow

The complete engineering workflow can be summarized as:

```text
          USER INPUT
              │
              ▼
    ┌───────────────────┐
    │ Conductor Database│
    │ or Custom Input   │
    └─────────┬─────────┘
              │
              ▼
     ┌─────────────────┐
     │ Geometry Engine │
     │                 │
     │ GMD / GMR       │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │ Parameter Engine│
     │                 │
     │ R / L / C       │
     │ Skin Effect     │
     └────────┬────────┘
              │
              ▼
       ┌─────────────┐
       │ ABCD Solver │
       └──────┬──────┘
              │
       ┌──────┴───────┐
       ▼              ▼
 Forward Mode    Reverse Mode
       │              │
       └──────┬───────┘
              ▼
     ┌─────────────────┐
     │ Power Analysis  │
     │                 │
     │ ΔV / Loss / η   │
     │ Ferranti Effect │
     └────────┬────────┘
              │
       ┌──────┴───────┐
       ▼              ▼
 Results Table    SLD Canvas
```

---

# 📈 Engineering Metrics

The simulator is designed around the key performance indicators engineers commonly use when evaluating transmission lines.

| Metric                  | Description                                                  |
| ----------------------- | ------------------------------------------------------------ |
| **$R_{ac}$**            | Effective AC conductor resistance                            |
| **$L$**                 | Line inductance                                              |
| **$C$**                 | Line capacitance                                             |
| **$A,B,C,D$**           | ABCD transmission parameters                                 |
| **Voltage Drop**        | Difference between sending and receiving voltage             |
| **Voltage Regulation**  | Change in receiving voltage with loading                     |
| **$I^2R$ Loss**         | Resistive transmission-line losses                           |
| **Efficiency**          | Ratio of receiving-end to sending-end power                  |
| **Ferranti Effect**     | Receiving-end voltage rise under light/no load               |
| **Maximum Loadability** | Maximum permissible operating load under defined constraints |

---

# 🗺️ Roadmap

TransLine-Sim is intended to evolve into a broader **power-system engineering workstation**.

### Planned Features

* [ ] 🔌 Three-phase short-circuit analysis
* [ ] ⚡ Fault-current calculation
* [ ] 🔋 Reactive-power compensation analysis
* [ ] 🌀 Shunt-reactor sizing
* [ ] 📊 Advanced voltage-stability analysis
* [ ] 📈 P–V and Q–V curves
* [ ] 🌐 Multi-bus power-system modeling
* [ ] 🗼 More transmission-tower geometries
* [ ] 🔗 Bundled-conductor optimization
* [ ] 📄 PDF export of engineering test reports
* [ ] 📋 CSV/Excel result export
* [ ] 💾 Save/load simulation projects
* [ ] 🧪 Automated engineering test cases
* [ ] 🖥️ Cross-platform packaging

> 🚧 **Roadmap items are subject to change.** Contributions that improve the mathematical accuracy, usability, documentation, or visualization system are welcome.

---

# 🤝 Contributing

Contributions are welcome!

Whether you want to improve the calculation engine, add a conductor, redesign part of the GUI, fix a bug, or improve documentation, feel free to contribute.

## Contribution Workflow

### 1. Fork the Repository

Create your own fork of **TransLine-Sim**.

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/TransLine-Sim.git
cd TransLine-Sim
```

### 3. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 4. Make Your Changes

Keep changes focused and maintainable.

For engineering calculations:

* Document important equations.
* Use meaningful variable names.
* Avoid unexplained constants.
* Validate new calculations against known results.
* Add tests where practical.

### 5. Commit Your Changes

```bash
git add .
git commit -m "Add: your feature description"
```

### 6. Push Your Branch

```bash
git push origin feature/your-feature-name
```

### 7. Open a Pull Request

Create a Pull Request describing:

* What you changed
* Why you changed it
* How you tested it
* Any limitations or assumptions

---

## 🧪 Engineering Contributions

For contributors modifying mathematical models, please include enough information for another engineer to reproduce or verify the result.

A good engineering contribution should ideally provide:

```text
Input Parameters
       ↓
Mathematical Model
       ↓
Calculated Result
       ↓
Expected / Reference Result
       ↓
Validation
```

Accuracy is more important than adding complexity.

---

# 📜 License

TransLine-Sim is released under the **MIT License**.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

This means you are free to:

* Use the software
* Modify the software
* Distribute the software
* Use it commercially
* Create derivative works

subject to the conditions described in the MIT License.

See [`LICENSE`](LICENSE) for the complete license text.

---

# 🙏 Acknowledgments

TransLine-Sim is built on the foundational concepts of classical **electrical power-system and transmission-line engineering**, including:

* Transmission-line distributed parameter theory
* ABCD two-port network analysis
* Electromagnetic conductor modeling
* Ferranti-effect analysis
* Power-system voltage and efficiency calculations
* ACSR conductor engineering
* Single Line Diagram representation

Special thanks to the open-source Python ecosystem and the engineers, educators, and students who continue to make electrical-engineering computation more accessible.

---

# ⚡ Why TransLine-Sim?

Traditional transmission-line calculations often require switching between equations, spreadsheets, simulation software, and hand-drawn schematics.

**TransLine-Sim brings those pieces together.**

```text
┌────────────────────────────────────────────┐
│              TRANSMISSION LINE             │
│                                            │
│  PHYSICAL PARAMETERS                       │
│       ↓                                    │
│  GMD → GMR → R → L → C                    │
│       ↓                                    │
│  ABCD NETWORK MODEL                        │
│       ↓                                    │
│  VOLTAGE / CURRENT / POWER                 │
│       ↓                                    │
│  REGULATION / LOSS / EFFICIENCY            │
│       ↓                                    │
│  FERRANTI EFFECT / LOADABILITY             │
│       ↓                                    │
│  INTERACTIVE SINGLE LINE DIAGRAM           │
│                                            │
└────────────────────────────────────────────┘
```

> **From conductor geometry to grid-level performance — visualize the entire transmission line.**

---

## ⭐ If You Find This Project Useful

Give the repository a ⭐ **Star**, report issues, suggest improvements, or contribute new engineering models.

Every contribution helps make power-system engineering tools more accessible to students, researchers, and practicing engineers.

---

**TransLine-Sim**
*Retro interface. Classical equations. Practical power-system engineering.*
