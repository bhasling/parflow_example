"""
Unit tests for pf_util module.
"""

# pylint: disable=C0301,R0914,C0413,E0401
import sys
import os
import parflow
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
import pf_util


def test_huc8():
    """
    Test generating a parflow directory and execute model and assert start/end pressure values for a HUC8.
    Uses HUC 02080203 and runs for 10 timesteps.
    """

    try:
        runname = "huc8"
        directory_path = f"./{runname}"

        start_time = "2005-10-01"
        end_time = "2005-10-02"
        options = {
            "hucs": ["02080203"],
            "grid": "conus2",
            "start_time": start_time,
            "end_time": end_time,
            "time_steps": 10,
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
        verify_pressure(runscript_path, 0.003443, 0.003190)

    except Exception as e:
        raise e


def test_box():
    """
    Test generating a parflow directory and execute model and assert start/end pressure values for a box
    Use a box with radius 5 around the same target point that is the center of HUC 02080203
    This should get the same answer as the HUC test, but with a smaller parflow domain.
    """

    try:
        runname = "box"
        directory_path = f"./{runname}"

        start_time = "2005-10-01"
        end_time = "2005-10-02"
        target_x = 3754
        target_y = 1588
        target_radius = 5
        grid_bounds = [
            target_x - target_radius,
            target_y - target_radius,
            target_x + target_radius,
            target_y + target_radius,
        ]
        print("GRID BOUNDS", grid_bounds)
        options = {
            "grid_bounds": grid_bounds,
            "grid": "conus2",
            "start_time": start_time,
            "end_time": end_time,
            "time_steps": 10,
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
        verify_pressure(runscript_path, 0.003443, 0.003190)

    except Exception as e:
        raise e


def verify_pressure(runscript_path, start_pressure, end_pressure):
    """Print the start and end pressure of the parflow run and assert expected values."""

    directory_path = os.path.dirname(runscript_path)
    runname = os.path.basename(directory_path)
    model = parflow.Run.from_definition(runscript_path)
    stop_time = model.TimingInfo.StopTime
    nx = model.ComputationalGrid.NX
    ny = model.ComputationalGrid.NY
    nz = model.ComputationalGrid.NZ
    domain_x = model.ComputationalGrid.Lower.X
    domain_y = model.ComputationalGrid.Lower.Y
    print(f"DOMAIN XY = ({domain_x}, {domain_y})")
    print("Num Time Steps", stop_time)
    initial_press_np = parflow.read_pfb(f"{directory_path}/ss_pressure_head.pfb")
    print("INI PRESS_SHAPE", initial_press_np.shape)
    x = int(nx / 2)
    y = int(ny / 2)
    z = nz - 1
    print(f"TARGET XY = ({domain_x + x}, {domain_y + y})")
    print("Num Time Steps", stop_time)
    print(f"INI PRESS ({z},{y},{x})", initial_press_np[z, y, x])
    print(initial_press_np[z, y, x])
    print()
    for i in range(0, stop_time):
        out_path = f"{directory_path}/{runname}.out.press.{i:05d}.pfb"
        out_press_np = parflow.read_pfb(out_path)
        print(f"OUT PRESS ({z},{y},{x}) {out_press_np[z, y, x]} [{i}]")
        top_layer_pressure = out_press_np
    assert initial_press_np[z, y, x] == pytest.approx(start_pressure, abs=0.00001)
    assert top_layer_pressure[z, y, x] == pytest.approx(end_pressure, abs=0.00001)
