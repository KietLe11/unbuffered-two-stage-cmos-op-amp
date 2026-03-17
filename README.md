# Unbuffered Two-Stage CMOS Op-Amp Designer

![Analog Electronics](https://img.shields.io/badge/Domain-Analog_Electronics-8A2BE2?style=flat-square)
![CMOS Op-Amp](https://img.shields.io/badge/Device-CMOS_Op--Amp-007EC6?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![YAML](https://img.shields.io/badge/Config-YAML-CB171E?style=flat-square)
![GitHub Actions](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=flat-square&logo=github-actions&logoColor=white)
![Black](https://img.shields.io/badge/Code_Style-Black-000000?style=flat-square)
![Ruff](https://img.shields.io/badge/Linter-Ruff-FCC21B?style=flat-square)

## Overview
This repository contains an automated, analytical design flow for sizing an unbuffered, two-stage CMOS operational amplifier. Developed for the EECS3611 Analog Electronics course at the Lassonde School of Engineering, this tool bridges the gap between theoretical hand-calculations and physical silicon constraints in a nanometer CMOS process.

Instead of manually recalculating W/L aspect ratios every time a target specification changes, this project utilizes a parameter-driven Python engine to instantly compute bias currents, compensation capacitance, and transistor dimensions while actively verifying output swing limits and power dissipation.

## Repository Structure
```text
📦 unbuffered-two-stage-cmos-op-amp
 ┣ 📂 .github/workflows
 ┃ ┗ 📜 ci.yml                 # GitHub Actions pipeline for linting, formatting, and testing
 ┣ 📂 scripts
 ┃ ┣ 📜 opamp_designer.py      # Core object-oriented sizing engine
 ┃ ┗ 📜 test_opamp.py          # Pytest golden reference suite
 ┣ 📜 design_params.yaml       # Master configuration file (Process constraints & Design knobs)
 ┣ 📜 requirements.txt         # Python dependencies
 ┗ 📜 README.md
```

## Features
* **Separation of Concerns:** Physical silicon constraints (unalterable) are strictly separated from design specifications (grading rubric) and user choices (control knobs) via a clean YAML interface.
* **Physical Reality Checks:** The script goes beyond textbook square-law formulas by actively verifying that required bias currents do not force transistors out of saturation during maximum/minimum voltage swings.
* **Dynamic Lambda Scaling:** Channel length modulation parameters are scaled dynamically based on the chosen transistor length ($L$) to provide accurate intrinsic gain estimations.
* **Continuous Integration:** A rigorous GitHub Actions pipeline ensures code quality using `Ruff`, formatting using `Black` (via Reviewdog for inline PR comments), and mathematical regression testing using `pytest`.

## Usage

### 1. Configure your targets
Modify the `design_choices` block inside `design_params.yaml` to set your target Slew Rate, Gain-Bandwidth Product, and default transistor length. 

```yaml
design_choices:
  Cc_multiplier: 0.22
  L_default_um: 0.54
  CL_target_pF: 2.0
  GBW_target_MHz: 10.0
  SR_target_V_us: 100.0
```

### 2. Run the Designer
Execute the Python script from the root directory to generate the calculated $W/L$ ratios and physical dimensions ($W$ in $\mu m$) required for your schematic testbench:

```bash
python scripts/opamp_designer.py
```

### 3. Run the Test Suite
To ensure that future modifications to the analytical equations do not silently break the core physics math, run the golden reference test suite:

```bash
pytest -v
```
