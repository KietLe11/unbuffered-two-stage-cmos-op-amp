"""
Test Suite for Two-Stage CMOS Operational Amplifier Designer
"""

import pytest
import yaml
from opamp_designer import OpAmpDesigner

@pytest.fixture
def baseline_yaml_file(tmp_path):
    """
    Creates a temporary YAML file with known baseline inputs.
    This acts as our 'Golden Reference' to ensure math logic never silently breaks.
    """
    test_data = {
        "process_params": {
            "tox_n_nm": 3.981,
            "tox_p_nm": 4.06,
            "mu0_n": 0.0305,
            "mu0_p": 0.0139,
            "vth0_n": 0.4395,
            "vth0_p": 0.459,
            "lambda_n": 0.719,
            "lambda_p": 0.491,
            "epsilon_ox_F_m": 3.4515e-11
        },
        "design_specs": {
            "VDD": 1.8,
            "VSS": 0.0,
            "CL_max_pF": 2.0,
            "GBW_min_MHz": 10.0,
            "SR_min_V_us": 10.0,
            "ICMR_min": 0.8,
            "ICMR_max": 1.4,
            "Vout_min": 0.4,
            "Vout_max": 1.5,
            "Pdiss_max_mW": 9.0
        },
        "design_choices": {
            "Cc_multiplier": 0.22,
            "L_default_um": 0.18,
            "CL_target_pF": 2.0,
            "GBW_target_MHz": 10.0,
            "SR_target_V_us": 10.0
        }
    }

    # tmp_path is a built-in pytest fixture that provides a temporary directory unique to the test invocation
    file_path = tmp_path / "test_design_params.yaml"
    with open(file_path, 'w') as f:
        yaml.dump(test_data, f)

    return str(file_path)

def test_baseline_math_calculations(baseline_yaml_file):
    """
    Verifies that the core physics equations produce the expected historical outputs.
    Using pytest.approx to handle floating-point precision differences.
    """
    designer = OpAmpDesigner(baseline_yaml_file)
    designer.run_all_stages()
    res = designer.results

    # Assert Stage 1 & 2 (Capacitor and Tail Current)
    assert res['Cc (pF)'] == pytest.approx(0.4400, abs=1e-4)
    assert res['I5 (uA)'] == pytest.approx(4.4000, abs=1e-4)

    # Assert Stage 3, 4, 5 (First Stage Sizing)
    assert res['S3, S4 (W/L)'] == pytest.approx(0.2572, abs=1e-4)
    assert res['S1, S2 (W/L)'] == pytest.approx(0.6569, abs=1e-4)
    assert res['S5 (W/L)'] == pytest.approx(0.8209, abs=1e-4)

    # Assert Stage 6 & 7 (Second Stage Sizing and Current)
    assert res['S6 (W/L)'] == pytest.approx(9.8912, abs=1e-4)
    assert res['I6 (uA)'] == pytest.approx(32.6957, abs=1e-4)
    assert res['S7 (W/L)'] == pytest.approx(6.0999, abs=1e-4)

    # Assert Final Verification Metrics
    assert res['Calculated Gain (dB)'] == pytest.approx(37.2156, abs=1e-4)
    assert res['Power Diss (mW)'] == pytest.approx(0.0668, abs=1e-4)
