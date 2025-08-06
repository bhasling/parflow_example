"""
Unit tests for pf_util module.
"""

import sys
import os
import parflow

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
import pf_util


def test_create():
    """
    Test that the initialize_model function initializes the model correctly.
    """

    try:
        runname = "pf_util"
        directory_path = f"./{runname}"

        start_time = "2001-01-01"
        end_time = "2001-01-02"
        options = {
            "grid_bounds": [4020, 1964, 4022, 1967],
            "grid": "conus2",
            "start_time": start_time,
            "end_time": end_time,
        }

        runscript_path = pf_util.create_model(runname, options, directory_path)
        model = parflow.Run.from_definition(runscript_path)

        # Check if the model has been initialized with default settings
        assert hasattr(model, "FileVersion")
        assert model.FileVersion == 4
        assert model.ComputationalGrid.DX == 1000.0

        model.TimingInfo.StopTime = 1
        model.write(file_format="yaml")
        model.run()

    except Exception as e:
        raise e


def test_compare():
    runscript_path = "./pf_util/pf_util.yaml"
    directory_path = os.path.dirname(runscript_path)
    initial_press_np = parflow.read_pfb(f"{directory_path}/ss_pressure_head.pfb")
    print("IN PRESS_SHAPE", initial_press_np.shape)
    print("IN PRESS", initial_press_np[9])
    out_press_np = parflow.read_pfb(f"{directory_path}/pf_util.out.press.00000.pfb")
    print("OUT PRESS SHAPE", out_press_np.shape)
    print("OUT PRESS", out_press_np[23])
