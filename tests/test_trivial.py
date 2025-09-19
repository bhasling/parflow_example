"""
Unit tests for pf_util module.
"""

# pylint: disable=C0301,R0914,C0413,E0401
import sys
import os
import parflow
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
import project


def test_trivial():
    """
    Test generating a parflow directory and execute model and assert start/end pressure values for a box
    Use a box with radius 5 around the same target point that is the center of HUC 02080203
    This should get the same answer as the HUC test, but with a smaller parflow domain.
    """

    try:
        project_options = {
            "run_type": "transient",
            "grid_bounds": [3749, 1583, 3759, 1593],
            "grid": "conus2",
            "start_date": "2005-10-01",
            "end_date": "2005-10-02",
            "time_steps": 10,
            "forcing_day": "2005-10-01",
            "topology": (2, 2, 1)
        }
        directory_path = "./trivial"

        # Create the parflow model and generated input files
        runscript_path = project.create_project(project_options, directory_path)

        # Run the parflow model
        model = parflow.Run.from_definition(runscript_path)
        model.run()

        # Verify the result
        time_step = 9
        nx = model.ComputationalGrid.NX
        ny = model.ComputationalGrid.NY
        nz = model.ComputationalGrid.NZ
        x = int(nx / 2)
        y = int(ny / 2)
        z = nz - 1
        runname = os.path.basename(directory_path)
        out_path = f"{directory_path}/{runname}.out.press.{time_step:05d}.pfb"
        out_press_np = parflow.read_pfb(out_path)
        print(f"OUT PRESS ({z},{y},{x}) {out_press_np[z, y, x]} [{time_step}]")
        top_layer_pressure = out_press_np
        assert top_layer_pressure[z, y, x] == pytest.approx(0.003247, abs=0.00001)


    except Exception as e:
        raise e