"""
Two-Stage CMOS Operational Amplifier Design Automation

This module automates the analytical sizing and verification calculations
for an unbuffered, two-stage CMOS operational amplifier. It parses process
parameters and design specifications from an external YAML configuration
file and sequentially calculates the required W/L (aspect) ratios, bias
currents, and compensation capacitance to meet target performance metrics
such as Gain, Phase Margin, and Slew Rate.

Author: Kiet
Date: 2026-03-17

Dependencies:
    - pyyaml (Install via: pip install pyyaml)
    - math (Standard Library)

Usage:
    Ensure 'design_params.yaml' is present in the working directory
    before executing the script.

    $ python opamp_designer.py
"""

import yaml
import math

class OpAmpDesigner:
    def __init__(self, yaml_file):
        with open(yaml_file, 'r') as f:
            # safe_load is recommended for security when parsing YAML
            data = yaml.safe_load(f)

        self.proc = data['process_params']
        self.spec = data['design_specs']
        self.choice = data['design_choices']
        self.results = {}

    def run_all_stages(self):
        self.validate_choices()
        self.calc_base_parameters()
        self.stage_1_compensation_cap()
        self.stage_2_tail_current()
        self.stage_3_active_load()
        self.stage_4_input_pair()
        self.stage_5_tail_source()
        self.stage_6_second_stage_amp()
        self.stage_7_second_stage_bias()
        self.stage_8_verify_specs()
        self.print_results()

    def validate_choices(self):
        """Validate user design choices against project specifications."""
        print("\n=== Validating Design Choices ===")

        if self.choice['CL_target_pF'] > self.spec['CL_max_pF']:
            print(f"WARNING: Target CL ({self.choice['CL_target_pF']} pF) exceeds max spec ({self.spec['CL_max_pF']} pF). Defaulting to {self.spec['CL_max_pF']} pF.")
            self.choice['CL_target_pF'] = self.spec['CL_max_pF']

        if self.choice['GBW_target_MHz'] < self.spec['GBW_min_MHz']:
            print(f"WARNING: Target GBW ({self.choice['GBW_target_MHz']} MHz) is below min spec ({self.spec['GBW_min_MHz']} MHz). Defaulting to {self.spec['GBW_min_MHz']} MHz.")
            self.choice['GBW_target_MHz'] = self.spec['GBW_min_MHz']

        if self.choice['SR_target_V_us'] < self.spec['SR_min_V_us']:
            print(f"WARNING: Target SR ({self.choice['SR_target_V_us']} V/us) is below min spec ({self.spec['SR_min_V_us']} V/us). Defaulting to {self.spec['SR_min_V_us']} V/us.")
            self.choice['SR_target_V_us'] = self.spec['SR_min_V_us']

        print("Validation complete.")

    def calc_base_parameters(self):
        """Calculate fundamental process constants."""
        eps_ox = self.proc['epsilon_ox_F_m']

        # Oxide capacitance (F/m^2)
        self.Cox_n = eps_ox / (self.proc['tox_n_nm'] * 1e-9)
        self.Cox_p = eps_ox / (self.proc['tox_p_nm'] * 1e-9)

        # Process transconductance parameters (A/V^2)
        self.Kn_prime = self.proc['mu0_n'] * self.Cox_n
        self.Kp_prime = self.proc['mu0_p'] * self.Cox_p

    def stage_1_compensation_cap(self):
        """Step 1: Determine minimum compensation capacitor (Cc) for 60 deg phase margin."""
        CL_F = self.choice['CL_target_pF'] * 1e-12
        self.Cc = self.choice['Cc_multiplier'] * CL_F
        self.results['Cc (pF)'] = self.Cc * 1e12

    def stage_2_tail_current(self):
        """Step 2: Determine minimum tail current (I5) based on Slew Rate."""
        SR_V_s = self.choice['SR_target_V_us'] * 1e6
        self.I5 = SR_V_s * self.Cc
        self.results['I5 (uA)'] = self.I5 * 1e6

    def stage_3_active_load(self):
        """Step 3: Size M3 and M4 based on Max ICMR, and Step 4: Verify Mirror Pole."""
        # S3 = I5 / (Kp * [VDD - Vin_max - |Vthp| + Vthn]^2)
        v_diff = self.spec['VDD'] - self.spec['ICMR_max'] - abs(self.proc['vth0_p']) + self.proc['vth0_n']
        self.S3 = self.I5 / (self.Kp_prime * (v_diff ** 2))
        self.S4 = self.S3 # Mirror pair
        self.results['S3, S4 (W/L)'] = self.S3

        # --- STEP 4: VERIFY MIRROR POLE IS NOT DOMINANT ---
        # 1. Calculate gm3. Current through M3 is half the tail current (I5 / 2).
        gm3 = math.sqrt(2 * self.Kp_prime * self.S3 * (self.I5 / 2))

        # 2. Calculate Cgs3 = 0.67 * W3 * L3 * Cox
        # Note: Since S3 = W3/L3, then W3 * L3 = S3 * L^2
        L_meters = self.choice['L_default_um'] * 1e-6
        Cgs3 = 0.67 * self.S3 * (L_meters ** 2) * self.Cox_p

        # 3. Calculate the mirror pole location in rad/s
        mirror_pole_rad = gm3 / (2 * Cgs3)

        # 4. Compare against 10 * GBW (converted to rad/s)
        GBW_rad = self.choice['GBW_target_MHz'] * 1e6 * 2 * math.pi

        self.results['Mirror Pole > 10GBW?'] = mirror_pole_rad > (10 * GBW_rad)

    def stage_4_input_pair(self):
        """Step 5: Size M1 and M2 based on Gain-Bandwidth."""
        GBW_rad = self.choice['GBW_target_MHz'] * 1e6 * 2 * math.pi
        self.gm1 = GBW_rad * self.Cc

        # S1 = S2 = gm1^2 / (Kn' * I5)
        self.S1 = (self.gm1 ** 2) / (self.Kn_prime * self.I5)
        self.S2 = self.S1
        self.results['S1, S2 (W/L)'] = self.S1

    def stage_5_tail_source(self):
        """Step 6: Size M5 based on Min ICMR."""
        # VDS5(sat) = Vin(min) - VSS - sqrt(I5 / (Kn'*S1)) - Vthn
        beta_1 = self.Kn_prime * self.S1
        VDS5_sat = self.spec['ICMR_min'] - self.spec['VSS'] - math.sqrt(self.I5 / beta_1) - self.proc['vth0_n']

        if VDS5_sat < 0.1: # Fallback to a minimum 100mV saturation margin if negative
            VDS5_sat = 0.1

        self.S5 = (2 * self.I5) / (self.Kn_prime * (VDS5_sat ** 2))
        self.results['S5 (W/L)'] = self.S5

    def stage_6_second_stage_amp(self):
        """Step 7: Size M6 for Phase Margin."""
        # gm6 = 2.2 * gm2 * (CL / Cc)
        self.gm2 = self.gm1 # Symmetric pair
        self.gm6 = 2.2 * self.gm2 * ((self.choice['CL_target_pF'] * 1e-12) / self.Cc)

        # Need gm4 to find S6. gm4 = sqrt(2 * Kp' * S4 * I4), where I4 = I5/2
        self.gm4 = math.sqrt(2 * self.Kp_prime * self.S4 * (self.I5 / 2))

        # S6 = S4 * (gm6 / gm4)
        self.S6 = self.S4 * (self.gm6 / self.gm4)
        self.results['S6 (W/L)'] = self.S6

    def stage_7_second_stage_bias(self):
        """Step 8 & 9: Calculate I6, verify output swing limits, and size M7."""
        # I6 = gm6^2 / (2 * Kp' * S6)
        self.I6 = (self.gm6 ** 2) / (2 * self.Kp_prime * self.S6)

        # Check against Vout_max requirement
        vsd6_sat_max = self.spec['VDD'] - self.spec['Vout_max']
        S6_min_swing = (2 * self.I6) / (self.Kp_prime * (vsd6_sat_max ** 2))
        if self.S6 < S6_min_swing:
            self.S6 = S6_min_swing
            # Recalculate I6 to maintain gm6 phase margin requirement with new S6
            self.I6 = (self.gm6 ** 2) / (2 * self.Kp_prime * self.S6)
            self.results['S6 (W/L)'] = self.S6

        self.results['I6 (uA)'] = self.I6 * 1e6

        # S7 = S5 * (I6 / I5)
        self.S7 = self.S5 * (self.I6 / self.I5)

        # Check against Vout_min requirement
        vds7_sat_max = self.spec['Vout_min'] - self.spec['VSS']
        S7_min_swing = (2 * self.I6) / (self.Kn_prime * (vds7_sat_max ** 2))
        if self.S7 < S7_min_swing:
            self.S7 = S7_min_swing

        self.results['S7 (W/L)'] = self.S7

    def stage_8_verify_specs(self):
        """Step 10: Verify Gain, Power Specs, and finalize physical dimensions."""

        # Scale lambda based on chosen L_default_um relative to the 0.18um minimum length
        L_ratio = 0.18 / self.choice['L_default_um']
        lambda_n_actual = self.proc['lambda_n'] * L_ratio
        lambda_p_actual = self.proc['lambda_p'] * L_ratio

        # Av = (2 * gm2 * gm6) / (I5*(lambda2 + lambda3) * I6*(lambda6 + lambda7))
        lambda_sum_1 = lambda_n_actual + lambda_p_actual
        lambda_sum_2 = lambda_p_actual + lambda_n_actual

        gain_linear = (2 * self.gm2 * self.gm6) / (self.I5 * lambda_sum_1 * self.I6 * lambda_sum_2)
        gain_dB = 20 * math.log10(gain_linear)
        self.results['Calculated Gain (dB)'] = gain_dB

        # Power Dissipation Verification
        pdiss_W = (self.I5 + self.I6) * (self.spec['VDD'] - self.spec['VSS'])
        self.results['Power Diss (mW)'] = pdiss_W * 1000
        self.results['Meets Power Spec?'] = (pdiss_W * 1000) <= self.spec['Pdiss_max_mW']

        # Calculate physical transistor Widths (W = S * L)
        L = self.choice['L_default_um']
        self.results['W1, W2 (um)'] = self.S1 * L
        self.results['W3, W4 (um)'] = self.S3 * L
        self.results['W5 (um)'] = self.S5 * L
        self.results['W6 (um)'] = self.S6 * L
        self.results['W7 (um)'] = self.S7 * L

    def print_results(self):
        print("\n=== Op-Amp Sizing Results ===")
        for key, value in self.results.items():
            if isinstance(value, bool):
                print(f"{key:25}: {'Yes' if value else 'No'}")
            else:
                print(f"{key:25}: {value:.4f}")
        print("=============================\n")

if __name__ == "__main__":
    designer = OpAmpDesigner('design_params.yaml')
    designer.run_all_stages()
