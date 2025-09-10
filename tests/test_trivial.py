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


def test_fixed_forcing_box():
    """
    Test generating a parflow directory and execute model and assert start/end pressure values for a box
    Use a box with radius 5 around the same target point that is the center of HUC 02080203
    This should get the same answer as the HUC test, but with a smaller parflow domain.
    """

    try:
        runname = "box_fixed_forcing"
        directory_path = f"./{runname}"

        start_time = "2005-10-01"
        end_time = "2005-10-02"
        target_x = 3754
        target_y = 1588
        target_radius = 5
        time_steps = 10
        grid_bounds = [
            target_x - target_radius,
            target_y - target_radius,
            target_x + target_radius,
            target_y + target_radius,
        ]
        parflow_options = {
            "grid_bounds": grid_bounds,
            "grid": "conus2",
            "start_time": start_time,
            "end_time": end_time,
            "time_steps": time_steps,
            "forcing_day": start_time,
        }

        # Create the parflow model and generated input files
        runscript_path = pf_util.create_project_dir(directory_path, parflow_options)
        model = parflow.Run.from_definition(runscript_path)
        model.write(file_format="yaml")

        # Run the parflow model
        model.run()

        # Verify the result
        time_step = time_steps - 1
        nx = model.ComputationalGrid.NX
        ny = model.ComputationalGrid.NY
        nz = model.ComputationalGrid.NZ
        x = int(nx / 2)
        y = int(ny / 2)
        z = nz - 1
        out_path = f"{directory_path}/{runname}.out.press.{time_step:05d}.pfb"
        out_press_np = parflow.read_pfb(out_path)
        print(f"OUT PRESS ({z},{y},{x}) {out_press_np[z, y, x]} [{time_step}]")
        top_layer_pressure = out_press_np
        assert top_layer_pressure[z, y, x] == pytest.approx(0.003247, abs=0.00001)


    except Exception as e:
        raise e