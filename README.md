# Unbuffered Two-Stage CMOS Op-Amp Designer

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
