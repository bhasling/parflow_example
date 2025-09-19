"""
    Create scenarios of .csv files that can be used to plot examples of parflow results.
"""
import os
import parflow
import project

def generate_scenarios():
    start_pressure_options = ["small", "large"]
    forcing_input = ["zero", "real" "large"]
    for sp in start_pressure_options:
        for forcing in forcing_input:
            generate_scenario(sp, forcing)
            return

def generate_scenario(start_pressure_option, forcing_input_option):
    scenario_options = {}
    scenario_options["start_date"] = "2005-10-01"
    scenario_options["end_date"] = "2005-10-02"
    scenario_options["timesteps"] = 10
    if start_pressure_option == "small":
        scenario_options["target_x"] = 3754
        scenario_options["target_y"] = 1588
        # 4037, 1949, 4038, 1951   -- Robinsville NJ WTD < 3 meters *oewaayew is negative
        scenario_options["target_x"] = (4037 + 4038)/2
        scenario_options["target_y"] = (1949 + 1951)/2
        print(scenario_options)
    elif start_pressure_option == "large":
        scenario_options["target_x"] = 3750
        scenario_options["target_y"] = 1500
    else:
        raise ValueError(f"Unsupport start pressure option '{start_pressure_option}")
    
    if forcing_input_option == "real":
        scenario_options["forcing_day"] = None
        scenario_options["preip"] = None
    elif forcing_input_option == "zero":
        scenario_options["forcing_day"] = "2005-10-01"
        scenario_options["preip"] = 0.0
    elif forcing_input_option == "large":
        scenario_options["forcing_day"] = "2000-01-01"
        scenario_options["preip"] = 10.0
    runname = f"{start_pressure_option}_{forcing_input_option}"
    directory_path = f"./scenarios/{runname}"
    execute_run(runname, scenario_options)
    #generate_csv(directory_path, scenario_options)

def execute_run(runname, scenario_options):
    print(runname, scenario_options)
    directory_path = f"./scenarios/{runname}"
    os.makedirs(directory_path, exist_ok=True)


    start_date = scenario_options.get("start_date")
    end_date = scenario_options.get("end_date")
    target_x = scenario_options.get("target_x")
    target_y = scenario_options.get("target_y")
    time_steps = scenario_options.get("time_steps")
    forcing_day = scenario_options.get("forcing_day")
    precip = scenario_options.get("precip")
    target_radius = 5
    grid_bounds = [
        target_x - target_radius,
        target_y - target_radius,
        target_x + target_radius,
        target_y + target_radius,
    ]
    options = {
        "grid_bounds": grid_bounds,
        "grid": "conus2",
        "start_date": start_date,
        "end_date": end_date,
        "forcing_day": forcing_day,
        "precip" : precip
    }
    if time_steps:
        options["time_steps"] = time_steps

    # Create the parflow model and generated input files
    runscript_path = project.create_project(options, directory_path)
    model = parflow.Run.from_definition(runscript_path)
    model.write(file_format="yaml")

    # Run the parflow model
    # 
    # 
    # model.run()

    generate_csv(directory_path, scenario_options)

def generate_csv(directory_path, scenario_options):
    print(directory_path)
    target_x = scenario_options.get("target_x")
    target_y = scenario_options.get("target_y")
    target_radius = 5

    initial_press_np = parflow.read_pfb(f"{directory_path}/ss_pressure_head.pfb")
    print("Initial Pressure")
    print(initial_press_np.shape)
    for r in range(-target_radius+1, target_radius):
        x = target_radius - r
        y = target_radius
        print(f"({x},{y}) {initial_press_np[9, y, x]}")


generate_scenarios()
    


