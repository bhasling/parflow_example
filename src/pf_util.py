"""
Utility to configure a parflow directory with files and runscript to be used to run parflow.
"""
#pylint: disable = C0301,R0914,W0632
import os
import shutil
import datetime
import parflow
import hf_hydrodata as hf
import subsettools as st


def create_model(
    runname: str,
    options: dict,
    directory_path: str,
    template_path: str = "conus2_transient_solid.yaml",
) -> str:
    """
    Create a parflow directory populated with files needed to run parflow.
    Returns:
        the path to the yaml runscript of the parflow model
    """
    runscript_path = create_runscript(runname, directory_path, template_path)

    create_topology(runscript_path, options)
    create_static_and_forcing(runscript_path, options, runname)
    create_dist_files(runscript_path, options)

    return runscript_path


def create_runscript(
    runname: str,
    directory_path: str,
    template_path="conus2_transient_solid.yaml",
):
    """
        Create a parflow model using the template.
        Returns:
            the path to the runscript of the model
    """

    directory_path = os.path.abspath(directory_path)

    os.makedirs(directory_path, exist_ok=True)
    template_dir = os.path.dirname(os.path.abspath(__file__))
    if not template_path.startswith("/"):
        template_path = os.path.join(template_dir, template_path)
    parflow.tools.settings.set_working_directory(directory_path)
    runscript_path = os.path.abspath(f"{directory_path}/{runname}.yaml")

    # Create Parfow runscript_path using the template if it does not exist yet
    if not os.path.exists(runscript_path):
        shutil.copy(template_path, runscript_path)
        model = parflow.Run.from_definition(runscript_path)
        model.write(file_format="yaml")

    return runscript_path


def create_topology(runscript_path: str, options: dict):
    """
    Create the topology files and add the references to the model and runscript.yaml file
    """
    model = parflow.Run.from_definition(runscript_path)
    _, grid, ij_bounds, latlon_bounds, _, _ = get_time_space_options(
        options
    )

    p = int(options.get("p", "1"))
    q = int(options.get("q", "1"))
    r = int(options.get("r", "1"))
    model.Process.Topology.P = p
    model.Process.Topology.Q = q
    model.Process.Topology.R = r
    model.FileVersion = 4

    ij_bounds, _ = st.define_latlon_domain(latlon_bounds, grid)

    model.ComputationalGrid.Lower.X = ij_bounds[0]
    model.ComputationalGrid.Lower.Y = ij_bounds[1]
    model.ComputationalGrid.Lower.Z = 0.0

    # Define the size of each grid cell. The length units are the same as those on hydraulic conductivity, here that is meters.
    model.ComputationalGrid.DX = 1000.0
    model.ComputationalGrid.DY = 1000.0
    model.ComputationalGrid.DZ = 200.0

    # Define the number of grid blocks in the domain.
    model.ComputationalGrid.NX = ij_bounds[2] - ij_bounds[0]
    model.ComputationalGrid.NY = ij_bounds[3] - ij_bounds[1]
    if grid == "conus1":
        model.ComputationalGrid.NZ = 5
    elif grid == "conus2":
        model.ComputationalGrid.NZ = 10

    model.write(file_format="yaml")


def create_static_and_forcing(runscript_path: str, options: dict, runname: str):
    """
    Create the static input and forcing files and add the references to the model and runscript.yaml file
    """
    model = parflow.Run.from_definition(runscript_path)
    directory_path = os.path.dirname(runscript_path)

    mask, grid, ij_bounds, _, start_time, end_time = get_time_space_options(
        options
    )

    st.write_mask_solid(
        mask=mask, grid=grid, write_dir=directory_path
    )

    var_ds = "conus2_domain"
    static_paths = st.subset_static(ij_bounds, dataset=var_ds, write_dir=directory_path)
    st.config_clm(
        ij_bounds,
        start=start_time,
        end=end_time,
        dataset=var_ds,
        write_dir=directory_path,
    )

    forcing_dir_path = directory_path
    os.makedirs(forcing_dir_path, exist_ok=True)
    forcing_ds = "CW3E"
    st.subset_forcing(
        ij_bounds,
        grid=grid,
        start=start_time,
        end=end_time,
        dataset=forcing_ds,
        write_dir=forcing_dir_path,
    )

    st.edit_runscript_for_subset(
        ij_bounds,
        runscript_path=runscript_path,
        runname=runname,
        forcing_dir=forcing_dir_path,
    )

    init_press_path = os.path.basename(static_paths["ss_pressure_head"])
    depth_to_bedrock_path = os.path.basename(static_paths["pf_flowbarrier"])

    st.change_filename_values(
        runscript_path=runscript_path,
        init_press=init_press_path,
        depth_to_bedrock=depth_to_bedrock_path,
    )
    model = parflow.Run.from_definition(runscript_path)
    model.Solver.CLM.MetFileName = "CW3E"
    model.write(file_format="yaml")


def create_dist_files(runscript_path: str, options: dict):
    """
    Create the parflow .dist files for the generated pfb files in the parflow directory.
    """
    p = int(options.get("p", "1"))
    q = int(options.get("q", "1"))

    st.dist_run(
        topo_p=p,
        topo_q=q,
        runscript_path=runscript_path,
        dist_clim_forcing=True,
    )
    model = parflow.Run.from_definition(runscript_path)

    # Set the timesteps to use in the parflow run
    time_steps = options.get("time_steps", None)
    if time_steps is None:
        # If time_steps is not set in the options use the hours between start and end time
        _, _, _, _, start_time, end_time = get_time_space_options(options)
        start_time_dt = datetime.datetime.strptime(start_time, "%Y-%m-%d")
        end_time_dt = datetime.datetime.strptime(end_time, "%Y-%m-%d")
        days_between = (end_time_dt - start_time_dt).days
        model.TimingInfo.StopTime = 24 * int(days_between)
    else:
        # If time_steps is set in the options then use that number of steps
        model.TimingInfo.StopTime = int(time_steps)

    # Reset the NZ that can be incorrectly set by st.dist_run
    model.ComputationalGrid.NZ = 10
    model.write(file_format="yaml")


def get_time_space_options(options):
    """
    Get the time and space options from the input options.
    Returns:
        (grid, ij_bounds, latlon_bounds, start_time, end_time)
    """

    grid_bounds = options.get("grid_bounds", None)
    latlon_bounds = options.get("latlon_bounds", None)
    hucs = options.get("hucs", None)
    grid = options.get("grid", "conus2")
    start_time = options.get("start_time", "2001-01-01")
    end_time = options.get("end_time", "2001-01-02")
    if hucs:
        ij_bounds, mask = st.define_huc_domain(hucs=hucs, grid=grid)
        lat_min, lon_min = hf.to_latlon(grid, ij_bounds[0], ij_bounds[1])
        lat_max, lon_max = hf.to_latlon(grid, ij_bounds[2] - 1, ij_bounds[3] - 1)
        latlon_bounds = [[lat_min, lon_min], [lat_max, lon_max]]
    elif grid_bounds:
        lat_min, lon_min = hf.to_latlon(grid, grid_bounds[0], grid_bounds[1])
        lat_max, lon_max = hf.to_latlon(grid, grid_bounds[2] - 1, grid_bounds[3] - 1)
        latlon_bounds = [[lat_min, lon_min], [lat_max, lon_max]]
        ij_bounds, mask = st.define_latlon_domain(latlon_bounds, grid)
    elif latlon_bounds:
        if len(latlon_bounds) != 2:
            raise ValueError("The latlon_bounds must be an array of 2 lat/lon pairs")
        if len(latlon_bounds[0]) != 2:
            raise ValueError("The latlon_bounds must be an array of 2 lat/lon pairs")
        ij_bounds, mask = st.define_latlon_domain(latlon_bounds, grid)
    else:
        raise ValueError("Must specify in options hucs, grid_bounds, or latlon_bounds")
    return (mask, grid, ij_bounds, latlon_bounds, start_time, end_time)
