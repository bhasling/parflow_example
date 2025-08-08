"""
Unit tests for pf_util module.
"""

import sys
import os
import parflow
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
import pf_util


def test_huc8():
    """
    Test generating a parflow directory and execute model and assert start/end pressure values for a HUC8
    """

    try:
        runname = "pf_util"
        directory_path = f"./{runname}"

        start_time = "2005-10-01"
        end_time = "2005-10-03"
        options = {
            "grid_bounds": [4020, 1964, 4022, 1967],
            "hucs": ["02080203"],
            "grid": "conus2",
            "start_time": start_time,
            "end_time": end_time,
        }

        # Create the parflow model and generated input files
        runscript_path = pf_util.create_model(runname, options, directory_path)
        model = parflow.Run.from_definition(runscript_path)
        model.write(file_format="yaml")

        # Check if the model has been initialized with default settings
        assert hasattr(model, "FileVersion")
        assert model.FileVersion == 4
        assert model.ComputationalGrid.DX == 1000.0
        model.write(file_format="yaml")

        # Run the parflow model
        model.run()

        # Verify the pressure start and end values for center cell of the period run
        verify_pressure(runscript_path, 0.057855, 0.057169)

    except Exception as e:
        raise e

def xxtest_compare():
    runscript_path = "pf_util/pf_util.yaml"
    verify_pressure(runscript_path, 0.057855, 0.057169)

def verify_pressure(runscript_path, start_pressure, end_pressure):
    directory_path = os.path.dirname(runscript_path)
    model = parflow.Run.from_definition(runscript_path)
    stopTime = model.TimingInfo.StopTime
    nx = model.ComputationalGrid.NX
    ny = model.ComputationalGrid.NY
    nz = model.ComputationalGrid.NZ
    print("Num Time Steps", stopTime)
    initial_press_np = parflow.read_pfb(f"{directory_path}/ss_pressure_head.pfb")
    print("INI PRESS_SHAPE", initial_press_np.shape)
    y = int(nx/2)
    x = int(ny/2)
    z = nz - 1
    print(f"INI PRESS ({z},{y},{x})", initial_press_np[z, y, x])
    print(initial_press_np[z, y, x])
    print()
    for i in range(0, stopTime):
        out_path = f"{directory_path}/pf_util.out.press.{i:05d}.pfb"
        out_press_np = parflow.read_pfb(out_path)
        print(f"OUT PRESS ({z},{y},{x}) {out_press_np[z, y, x]} [{i}]")
        top_layer_pressure = out_press_np
    assert initial_press_np[z, y, x] == pytest.approx(start_pressure, 0.00001)
    assert top_layer_pressure[z, y, x] == pytest.approx(end_pressure, 0.00001)
