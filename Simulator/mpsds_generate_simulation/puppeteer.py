


"""
#########################################################################################################################################################

Puppeteer.py is the main file. This file will be the responsible for the main logic of the program. It will join all the pices together and generate the 
final output.

Fix the timestamp, is the last thing to do but it needs to be done.

#########################################################################################################################################################
"""


# Importing the necessary libraries
import json
from datetime import datetime
import numpy as np
import os
import time


#Import custom modules
import solar_module.solar_irradiance as solar_module #Import the solar_production module from the solar_block folder
from climateEnviroment import temperature_humidty_airquality as getTempHomemade #Import the homemade sensor module
from npc import run_simulation #Import the run_simulation function from the npc module
from battery_module.battery_sim import battery_status #Import the battery_status function from the battery_sim module

#Import custom solar modules for real time. Batery and climateEnviroment are the same
from solar_module.solar_irradiance import get_real_time_solar_irradiance
from npc import run_simulation_realtime




#if the directory results does not exist, create it
if not os.path.exists("results"):
    os.makedirs("results")




def get_solar_production(solar_irr_data_json: dict, pannel_eff: float, num_pannels: int, panel_area_m2: float):
    """
    This function will be responsible for generating the solar production data. It will use the solar_block.solar_production module to calculate the
    solar production of the given solar panels. This module uses solcast api to return the irradiance data.
    
    Args:
        solar_irr_data_json (dict): The solar irradiance data in JSON format, every 5 minutes. With this format "{"2024-01-01 00:00:00+01:00": 0.0, "2024-01-01 00:05:00+01:00": 0.0, ....}"
        pannel_eff (float): The efficiency of the solar panels.
        num_pannels (int): The number of solar panels.
        panel_area_m2 (float): The area of the solar panels in m².
        
    Returns:
        dict: Dictionary containing the solar production data. With timestamp as key (like in the solar_irr dict) and the production in kW as value.
    """
    
    
    production_data = {
        timestamp: (irradiance * panel_area_m2 * pannel_eff * num_pannels) / 1000
        for timestamp, irradiance in solar_irr_data_json.items()
    }
    
    return production_data
    


def get_total_consumption(config_file_data: dict, output_file: str = "results/user_data.json", interval: int = 300, minutes: bool = True, start_date: datetime = None, end_date: datetime = None):
    """
    Run the house simulation with custom parameters.

    Args:
        config_file (str): Path to the configuration JSON file.
        output_file (str): Path to save the simulation output (default: "my_results.json").
        interval (int): Update interval in seconds (default: 300).
        minutes (bool): Whether actions are in minutes (default: True).

    Returns:
         tuple: (total_electricity_used_kwh, total_water_used_liters, device_electricity_usage) for fast-forward mode,
           where device_electricity_usage is a dictionary with device keys (e.g., "Kitchen_stove") and their electricity usage in kWh.
           Returns None for real-time mode.
    """
    
    #Get type of simulation
    type_of_simulation = config_file_data["basic_parameters"]["type_of_simulation"]["type"]
    
    if type_of_simulation == "fast_forward":
        print("Running fast foward simulation...")
        result = run_simulation(config_data=config_file_data,
                                output_path=output_file,
                                update_interval=interval,
                                actions_in_minutes_flag=minutes,
                                start_date=start_date,
                                end_date=end_date)
        
        if result:
            electricity_used, water_used, device_conumption_dict = result
            print("\033[92mFast foward simulation completed correctly\033[0m")
            return electricity_used, water_used, device_conumption_dict   
        else:
            print("\033[91mSimulation failed with result None\033[0m")
            exit(1)
            
            
    elif type_of_simulation == "real_time":
        print("Running real time simulation...")

        # Run the simulation in real-time mode
        result = run_simulation_realtime(config_data=config_file_data, output_path=output_file)

        if result:
            print(f"Result: {result}")
            electricity_used, water_used, device_consumption_dict = result

            # Check if electricity consumption is 0 or None
            if electricity_used == 0 or electricity_used is None:
                print("\033[93mElectricity consumption is 0 or None. Setting grid consumption to 0.\033[0m")
                grid_consumption = 0
            else:
                # Calculate grid consumption normally if electricity is used
                grid_consumption = electricity_used  # Replace with actual calculation if needed

            print(f"Grid Consumption: {grid_consumption}")
            print("\033[92mReal time simulation completed correctly\033[0m")
            return electricity_used, water_used, device_consumption_dict
        else:
            print("\033[91mSimulation failed with result None\033[0m")
            exit(1)
    else:
        print("\033[91mInvalid simulation type. Please use 'fast_foward' or 'real_time'.\033[0m")
        exit(1)
        

    

from datetime import datetime

from datetime import datetime

def get_battery_data(battery_capacity_ah: float, voltage: float, solar_prod, total_consumpt, charge_eff: float, discharge_eff: float, energy_loss_convrt: float, degrading_ratio: float, initial_state_charge: float = 100.0, type_of_simulation: str = "fast_forward"):
    """
    Compute battery status based on solar production and total consumption data.

    Args:
        battery_capacity_ah (float): Battery capacity in ampere-hours.
        voltage (float): Battery voltage.
        solar_prod: Solar production data (dict for both modes: single timestamp in real-time, multiple in fast-forward).
        total_consumpt: Total consumption data (float in real-time, dict in fast-forward).
        charge_eff (float): Charging efficiency.
        discharge_eff (float): Discharging efficiency.
        energy_loss_convrt (float): Energy loss during conversion.
        degrading_ratio (float): Battery degradation ratio.
        initial_state_charge (float): Initial state of charge percentage (default: 100.0).
        type_of_simulation (str): Simulation type ("real_time" or "fast_forward").

    Returns:
        dict: Battery status with timestamps as keys.
    """
    if type_of_simulation == "real_time":
        # Validate inputs for real-time mode
        if not isinstance(solar_prod, dict) or len(solar_prod) != 1:
            raise ValueError("In real-time mode, solar_prod should be a dict with exactly one timestamp.")
        if not isinstance(total_consumpt, (float, int)):
            raise TypeError("In real-time mode, total_consumpt should be a float or int.")

        # Extract the single timestamp and value from solar_prod
        timestamp = list(solar_prod.keys())[0]
        solar_energy_kwh = solar_prod[timestamp]  # kW value for the current time step
        consumpt_energy_kwh = total_consumpt      # Float value in kWh

        # Convert timestamp to datetime
        curr_ts_dt = datetime.fromisoformat(timestamp)

        # Compute battery status for this single time step
        status = battery_status(
            battery_capacity_ah=battery_capacity_ah,
            voltage=voltage,
            solar_prod=solar_energy_kwh,
            total_consumpt=consumpt_energy_kwh,
            charge_eff=charge_eff,
            discharge_eff=discharge_eff,
            energy_loss_convrt=energy_loss_convrt,
            degrading_ratio=degrading_ratio,
            initial_state_charge=initial_state_charge,
            current_time=curr_ts_dt
        )
        # Return a dict with the timestamp as key for consistency
        return {timestamp: status}

    elif type_of_simulation == "fast_forward":
        # Validate inputs for fast-forward mode
        if not isinstance(solar_prod, dict):
            raise TypeError("In fast-forward mode, solar_prod should be a dict.")
        if not isinstance(total_consumpt, dict):
            raise TypeError("In fast-forward mode, total_consumpt should be a dict.")

        # Standardize timestamps for both dictionaries
        solar_prod_standardized = {standardize_timestamp_format(ts): value for ts, value in solar_prod.items()}
        total_consumpt_standardized = {standardize_timestamp_format(ts): value for ts, value in total_consumpt.items()}

        # Find common timestamps between solar_prod and total_consumpt
        common_timestamps = sorted(set(solar_prod_standardized.keys()) & set(total_consumpt_standardized.keys()), key=lambda x: datetime.fromisoformat(x))
        if not common_timestamps:
            raise ValueError("No common timestamps found between solar production and total consumption data.")

        # Debugging: Print the number of common timestamps
        print(f"Number of common timestamps in get_battery_data: {len(common_timestamps)}")

        # Convert to datetime objects for time differences
        timestamps_dt = [datetime.fromisoformat(ts) for ts in common_timestamps]

        # Optional: Check for consecutive 5-minute intervals
        for i in range(1, len(timestamps_dt)):
            delta_t_minutes = (timestamps_dt[i] - timestamps_dt[i-1]).total_seconds() / 60
            if delta_t_minutes != 5:
                print(f"Warning: Timestamp gap between {timestamps_dt[i-1]} and {timestamps_dt[i]} is {delta_t_minutes} minutes, expected 5 minutes.")

        # Initialize result dictionary
        result = {}

        # Initialize battery status at the first common timestamp
        first_ts_dt = timestamps_dt[0]
        first_ts_str = common_timestamps[0]
        initial_status = battery_status(
            battery_capacity_ah=battery_capacity_ah,
            voltage=voltage,
            solar_prod=0.0,  # No energy transfer for initialization
            total_consumpt=0.0,
            charge_eff=charge_eff,
            discharge_eff=discharge_eff,
            energy_loss_convrt=energy_loss_convrt,
            degrading_ratio=degrading_ratio,
            initial_state_charge=initial_state_charge,
            current_time=first_ts_dt
        )
        result[first_ts_str] = initial_status

        # Iterate over consecutive common timestamps
        for i in range(1, len(timestamps_dt)):
            prev_ts_dt = timestamps_dt[i - 1]
            curr_ts_dt = timestamps_dt[i]
            prev_ts_str = common_timestamps[i - 1]
            curr_ts_str = common_timestamps[i]

            # Compute time difference in hours
            delta_t_hours = (curr_ts_dt - prev_ts_dt).total_seconds() / 3600.0

            # Compute energy (kWh) for the interval [prev_ts, curr_ts] using power at prev_ts
            solar_energy_kwh = solar_prod_standardized[prev_ts_str] * delta_t_hours
            consumpt_energy_kwh = total_consumpt_standardized[prev_ts_str] * delta_t_hours

            # Update battery status for current timestamp
            status = battery_status(
                battery_capacity_ah=battery_capacity_ah,
                voltage=voltage,
                solar_prod=solar_energy_kwh,
                total_consumpt=consumpt_energy_kwh,
                charge_eff=charge_eff,
                discharge_eff=discharge_eff,
                energy_loss_convrt=energy_loss_convrt,
                degrading_ratio=degrading_ratio,
                initial_state_charge=initial_state_charge,  # Ignored after first call due to history
                current_time=curr_ts_dt
            )
            result[curr_ts_str] = status

        return result

    else:
        raise ValueError("Invalid type_of_simulation. Must be 'real_time' or 'fast_forward'.")
    

def standardize_timestamp_format(timestamp):
    """Convert a timestamp to a standardized ISO format without 'T' separator."""
    dt = datetime.fromisoformat(timestamp.replace("T", " "))
    return dt.strftime("%Y-%m-%d %H:%M:%S%z")

def get_solar_grid_consumption(solar_production, total_electr_consumption):
    """
    Calculate the electrical grid consumption based on the solar production and total electricity consumption.
    
    If the value is negative, it means there is an excess of solar production.
    If the value is positive, it means the house is consuming more electricity than the solar panels are producing.
    
    Args:
        solar_production (dict): Solar production data in kW. With timestamp as key and production in kW as value.
        total_electr_consumption (dict): Total electricity consumption in kW. With timestamp as key and consumption in kW as value.
        
    Returns:
        dict: Dictionary containing the electrical grid consumption data. With timestamp as key and consumption in kW as value.
    """
    
    # If both dictionaries are empty, raise an error
    if not solar_production and not total_electr_consumption:
        raise ValueError("Both solar production and total electricity consumption are empty.")
    
    # If one of the dictionaries is empty, raise an error
    if not solar_production:
        raise ValueError("Solar production data is empty.")
    if not total_electr_consumption:
        raise ValueError("Total electricity consumption data is empty.")
    
    #print size of both dictionaries
    #print(f"Size of solar_production: {len(solar_production)}")
    #print(f"Size of total_electr_consumption: {len(total_electr_consumption)}")
    
    
    
    # Standardize timestamps in both dictionaries
    standardized_solar_production = {standardize_timestamp_format(ts): value for ts, value in solar_production.items()}
    standardized_total_electr_consumption = {standardize_timestamp_format(ts): value for ts, value in total_electr_consumption.items()}

    # Find common timestamps
    common_timestamps = set(standardized_solar_production.keys()) & set(standardized_total_electr_consumption.keys())
    
    # If no common timestamps are found, raise an error
    if not common_timestamps:
        raise ValueError("No common timestamps found between solar production and total electricity consumption data in solar_grid_consumption.")
    else:
        print(f"Number of common timestamps: {len(common_timestamps)} found in get_solar_grid_consumption.")
    
    
    
        
    # Filter both datasets to only include common timestamps
    filtered_solar_production = {ts: standardized_solar_production[ts] for ts in common_timestamps}
    filtered_total_electr_consumption = {ts: standardized_total_electr_consumption[ts] for ts in common_timestamps}

    # Calculate the grid consumption
    grid_consumption = {
        timestamp: filtered_total_electr_consumption[timestamp] - filtered_solar_production[timestamp]
        for timestamp in common_timestamps
    }
    
    return grid_consumption


def get_device_satistical_data(dev_dict: dict) -> dict:
    """
    Calculate statistical measures and anomalies from a dictionary of device energy consumption.
    
    Args:
        dev_dict (dict): Dictionary with device names as keys and energy consumption as values. 
                         Format: {"2024-01-01 00:05:00+01:00": {"electricity": {"Kitchen_stove": 0.5}, 
                                                        "water": {"Bathroom_shower": 10.0}}, ...}
        
    Returns:
        dict: Dictionary containing statistical measures and anomaly information. Use timestamp as key 
              and the statistical data as value.
    """
    
    def _compute_category_stats(category_dict):
        """Compute statistical measures and anomalies for a dictionary of device consumptions."""
        values = list(category_dict.values())
        n = len(values)
        
        # Handle case with no devices
        if n == 0:
            return {
                "number_of_devices": 0,
                "total_consumption": 0,
                "mean_consumption": None,
                "std_deviation": None,
                "median_consumption": None,
                "min_consumption": None,
                "max_consumption": None,
                "first_quartile": None,
                "third_quartile": None,
                "iqr": None,
                "gini_coefficient": None,
                "num_low_anomalies": 0,
                "num_high_anomalies": 0,
                "low_anomalies": [],
                "high_anomalies": []
            }
        
        # Basic statistics
        total = sum(values)
        mean = total / n
        std = np.std(values, ddof=1) if n > 1 else 0  # Sample std dev; 0 if n=1
        median = np.median(values)
        min_val = min(values)
        max_val = max(values)
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        # Gini coefficient
        sorted_values = sorted(values)
        sum_i_x = sum((i + 1) * x for i, x in enumerate(sorted_values))
        gini = (2 * sum_i_x) / (n * total) - (n + 1) / n if total > 0 else 0
        
        # Anomaly detection using IQR method
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        low_anomalies = [device for device, consumption in category_dict.items() 
                         if consumption < lower_bound]
        high_anomalies = [device for device, consumption in category_dict.items() 
                          if consumption > upper_bound]
        num_low_anomalies = len(low_anomalies)
        num_high_anomalies = len(high_anomalies)
        
        return {
            "number_of_devices": n,
            "total_consumption": total,
            "mean_consumption": mean,
            "std_deviation": std,
            "median_consumption": median,
            "min_consumption": min_val,
            "max_consumption": max_val,
            "first_quartile": q1,
            "third_quartile": q3,
            "iqr": iqr,
            "gini_coefficient": gini,
            "num_low_anomalies": num_low_anomalies,
            "num_high_anomalies": num_high_anomalies,
            "low_anomalies": sorted(low_anomalies),
            "high_anomalies": sorted(high_anomalies)
        }
    
    # Process each timestamp in the input dictionary
    result = {}
    for timestamp, data in dev_dict.items():
        stats = {}
        for category in ["electricity", "water"]:
            # Use empty dict if category is missing
            category_dict = data.get(category, {})
            stats[category] = _compute_category_stats(category_dict)
        result[timestamp] = stats
    
    return result

# Helper function to map battery health percentage to a description
def health_status_description(percentage):
    """Map battery health percentage to a descriptive status."""
    if percentage > 80:
        return "good"
    elif percentage > 50:
        return "fair"
    else:
        return "poor"

def generate_output(houseID, solar_production, electricity_consumption, water_consumption, device_consumption, solar_grid_consumption, battery_data, device_statistical_data, temperature, humidity, air_quality, air_quality_description):
    """
    Generate a single JSON file with sensor data for all timestamps, including all device statistics.

    Args:
        houseID (str): House ID.
        solar_production (dict): Solar production in kW, with timestamps as keys.
        electricity_consumption (dict): Total electricity consumption in kW, with timestamps as keys.
        water_consumption (dict): Water consumption in liters, with timestamps as keys.
        device_consumption (dict): Device consumption data, with timestamps as keys and nested electricity/water dicts.
        solar_grid_consumption (dict): Grid consumption in kW, with timestamps as keys.
        battery_data (dict): Battery data, with timestamps as keys and nested battery stats.
        device_statistical_data (dict): Statistical data for devices, with timestamps as keys.
        temperature (float): Temperature in Celsius (constant for now).
        humidity (float): Humidity in percentage (constant for now).
        air_quality (int): Air quality index (constant for now).
        air_quality_description (str): Air quality description (constant for now).
    """
    
    
    
    
    # Standardize all input dictionaries' timestamps
    def safe_standardize_timestamps(data):
        """Standardize timestamps, skipping invalid keys."""
        return {
            standardize_timestamp_format(ts): value
            for ts, value in data.items()
            if isinstance(ts, str) and is_valid_isoformat(ts)
        }

    def is_valid_isoformat(timestamp):
        """Check if a string is a valid ISO 8601 timestamp."""
        try:
            datetime.fromisoformat(timestamp.replace("T", " "))
            return True
        except ValueError:
            return False

    # Standardize all input dictionaries' timestamps
    solar_production_std = safe_standardize_timestamps(solar_production)
    electricity_consumption_std = safe_standardize_timestamps(electricity_consumption)
    water_consumption_std = safe_standardize_timestamps(water_consumption)
    device_consumption_std = safe_standardize_timestamps(device_consumption)
    solar_grid_consumption_std = safe_standardize_timestamps(solar_grid_consumption)
    battery_data_std = safe_standardize_timestamps(battery_data)
    device_statistical_data_std = safe_standardize_timestamps(device_statistical_data)

    if not solar_production_std:
        print("Warning: Solar production data is empty. Filling with None.")
        solar_production_std = {ts: None for ts in electricity_consumption_std.keys()}

    if not electricity_consumption_std:
        print("Warning: Electricity consumption data is empty. Filling with None.")
        electricity_consumption_std = {ts: None for ts in solar_production_std.keys()}

    if not water_consumption_std:
        print("Warning: Water consumption data is empty. Filling with None.")
        water_consumption_std = {ts: None for ts in solar_production_std.keys()}

    if not device_consumption_std:
        print("Warning: Device consumption data is empty. Filling with empty dictionaries.")
        device_consumption_std = {ts: {"electricity": {}, "water": {}} for ts in solar_production_std.keys()}

    if not solar_grid_consumption_std:
        print("Warning: Solar grid consumption data is empty. Filling with None.")
        solar_grid_consumption_std = {ts: None for ts in solar_production_std.keys()}

    if not battery_data_std:
        print("Warning: Battery data is empty. Filling with default battery status.")
        battery_data_std = {ts: {"battery": {"charge_level_kwh": None, "discharging_rate": None, "health_status": None}} for ts in solar_production_std.keys()}

    if not device_statistical_data_std:
        print("Warning: Device statistical data is empty. Filling with empty statistics.")
        device_statistical_data_std = {ts: {"electricity": {}, "water": {}} for ts in solar_production_std.keys()}










    # Debugging: Print the keys of each dictionary
    print(f"Solar Production Keys: {list(solar_production_std.keys())}")
    print(f"Electricity Consumption Keys: {list(electricity_consumption_std.keys())}")
    print(f"Water Consumption Keys: {list(water_consumption_std.keys())}")
    print(f"Device Consumption Keys: {list(device_consumption_std.keys())}")
    print(f"Solar Grid Consumption Keys: {list(solar_grid_consumption_std.keys())}")
    print(f"Battery Data Keys: {list(battery_data_std.keys())}")
    print(f"Device Statistical Data Keys: {list(device_statistical_data_std.keys())}")

    # Check for empty dictionaries
    if not solar_production_std or not electricity_consumption_std or not water_consumption_std or not device_consumption_std or not solar_grid_consumption_std or not battery_data_std or not device_statistical_data_std:
        raise ValueError("One or more input datasets are empty. Cannot generate output.")

    # Find common timestamps across all datasets
    all_keys = [solar_production_std.keys(), electricity_consumption_std.keys(), water_consumption_std.keys(),
                device_consumption_std.keys(), solar_grid_consumption_std.keys(), battery_data_std.keys(),
                device_statistical_data_std.keys()]
    common_timestamps = sorted(set.intersection(*map(set, all_keys)), key=lambda x: datetime.fromisoformat(x))

    if not common_timestamps:
        raise ValueError("No common timestamps found across all input datasets.")

    print(f"Generating output with {len(common_timestamps)} common timestamps.")

    # List to hold data for all timestamps
    output_data = []

    for ts in common_timestamps:
        # Build the output dictionary for this timestamp
        ts_data = {
            "house_id": houseID,
            "timestamp": ts,
            "energy_management_sensors": {
                "solar_power": {
                    "production": solar_production_std[ts],
                    "grid_consumption": solar_grid_consumption_std[ts]
                },
                "battery": {
                    "charge_level": battery_data_std[ts]["battery"]["charge_level_kwh"],
                    "discharging_rate": battery_data_std[ts]["battery"]["discharging_rate"],
                    "health_status": health_status_description(battery_data_std[ts]["battery"]["health_status"])
                },
                "energy_efficiency": {
                    "device_consumption": device_consumption_std[ts].get("electricity", {}),
                    "load_balancing": device_statistical_data_std[ts]["electricity"].get("gini_coefficient", 0.0),  # Default to 0.0
                    "statistics": device_statistical_data_std[ts].get("electricity", {})
                }
            },
            "water_management_sensors": {
                "usage_tracking": water_consumption_std[ts],
                "device_consumption": device_consumption_std[ts].get("water", {}),
                "statistics": device_statistical_data_std[ts].get("water", {})
            },
            "climate_and_environment_sensors": {
                "temperature": temperature,
                "humidity": humidity,
                "air_quality": air_quality,
                "air_quality_description": air_quality_description
            }
        }
        output_data.append(ts_data)

    # Generate new folder to save the outputs file
    if not os.path.exists("sim_result"):
        os.makedirs("sim_result")

    # Save the output to a single file
    output_file = f"./sim_result/{houseID}_output.json"
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=4)

    print(f"Generated output file: {output_file}")






def complete_simulation_generate(name_of_config_file: str = "mpsds_generate_simulation/config_default.json"):
    
    #Import the configuration file
    with open(name_of_config_file) as f:
        config = json.load(f)
        
    
    type_of_simulation = config["basic_parameters"]["type_of_simulation"]["type"] #Just fast_foward for now
    
    latitud_barcelona, longitud_barcelona = 41.38879, 2.15899  # Barcelona, España
    tz = 'Europe/Madrid'
        
    if type_of_simulation == "fast_forward":
        
        print("*"*100)
        print("\033[92mStarting fast foward simulation...\033[0m")
        print("*"*100)
        
        start_date = config["basic_parameters"]["type_of_simulation"]["start_date"] #Start date of the simulation
        end_date = config["basic_parameters"]["type_of_simulation"]["end_date"] #End date of the simulation
        
        
        
        ################################## 1. Get solar production simulation ##################################
        print("Getting solar production data...") 
        solar_prod = get_solar_production(solar_irr_data_json=solar_module.get_solar_irradiance(latitud_barcelona, longitud_barcelona, tz, start_date, end_date),
                                        pannel_eff=config["solar_panels"]["panel_eff"],
                                        num_pannels=config["solar_panels"]["number_of_panels"],
                                        panel_area_m2=config["solar_panels"]["size_of_panels_m2"])
        print("\033[92mSolar production data obtained correctly\033[0m")
        
        ####################################### 2. Get grid consumption ######################################## 
        
        print("Getting total consumption data...")
        #run the simulation to get total consuption
        total_consumption = get_total_consumption(config_file_data=config,
                                                output_file="results/user_data.json",
                                                interval=300,
                                                minutes=True,
                                                start_date=start_date,
                                                end_date=end_date)
        print("\033[92mTotal consumption data obtained correctly\033[0m")
        
        #total_consumption[0] is the total electricity consumption (a dict with timestamps as keys and consumption in kW as values)
        #total_consumption[1] is the total water consumption in liters (a dict with timestamps as keys and consumption in liters as values)
        #total_consumption[2] is the device consumption (a dict with device names as keys and consumption in kW as values)
        
        print(f"Getting solar grid consumption data...")
        grid_consumption = get_solar_grid_consumption(solar_production=solar_prod,
                                                    total_electr_consumption=total_consumption[0])
        print("\033[92mSolar grid consumption data obtained correctly\033[0m")
        
        
        
        ######################################## 3. Get battery data ###########################################
        
        #Get the battery data
        print("Getting battery data...")
        battery_data = get_battery_data(battery_capacity_ah=config["battery"]["capacity_ah"],
                                        voltage=config["battery"]["voltage"],
                                        solar_prod=solar_prod,
                                        total_consumpt=total_consumption[0],
                                        charge_eff=config["battery"]["charging_efficiency"],
                                        discharge_eff=config["battery"]["discharging_efficiency"],
                                        energy_loss_convrt=config["battery"]["energy_loss_conversion"],
                                        degrading_ratio=config["battery"]["degrading_ratio"],
                                        initial_state_charge=config["battery"]["initial_state_of_charge_percent"],
                                        type_of_simulation=type_of_simulation)
        print("\033[92mBattery data obtained correctly\033[0m")
        
        
        ###################################### 4. Get device consumption #######################################
        
        device_consumption = total_consumption[2]
        
        print(f"Getting device statistical data...")
        device_statistical_data = get_device_satistical_data(dev_dict=device_consumption)
        print("\033[92mDevice statistical data obtained correctly\033[0m")
        
        
        ###################################### 5. Get water consumption #######################################
        
        water_consumption = total_consumption[1]
        
        ###################################### 5. Get climate and environment sensors #########################
        
        print("Getting climate and environment sensors data...")
        temperature = getTempHomemade.get_temp_hum()[0]
        humidity = getTempHomemade.get_temp_hum()[1]
        air_quality = getTempHomemade.get_aq()[0]
        air_quality_description = getTempHomemade.get_aq()[1]
        print("\033[92mClimate and environment sensors data obtained correctly\033[0m")
        
            
        ###################################### 6. Generate output file ########################################
        print("Generating output file...")
        generate_output(
            houseID=config["basic_parameters"]["name"].lower().replace(" ", "_"),
            solar_production=solar_prod,
            electricity_consumption=total_consumption[0],  # Pass total electricity consumption
            water_consumption=water_consumption,        # Pass total water consumption
            device_consumption=device_consumption,
            solar_grid_consumption=grid_consumption,
            battery_data=battery_data,
            device_statistical_data=device_statistical_data,
            temperature=temperature,
            humidity=humidity,
            air_quality=air_quality,
            air_quality_description=air_quality_description
        )
        print("\033[92mOutput file generated correctly\033[0m")
        
        print("\033[92mSimulation completed successfully!\033[0m")
    
    elif type_of_simulation == "real_time":
         
        print("*"*100)
        print("\033[92mStarting real time simulation...\033[0m")
        print("*"*100)
        
        #Update every 5m 
        interval = 300
        
        while True:
            ################################## 1. Get solar production simulation ##################################
            print("Getting solar production data...") 
            solar_prod = get_solar_production(solar_irr_data_json=get_real_time_solar_irradiance(latitud_barcelona, longitud_barcelona, tz),
                                            pannel_eff=config["solar_panels"]["panel_eff"],
                                            num_pannels=config["solar_panels"]["number_of_panels"],
                                            panel_area_m2=config["solar_panels"]["size_of_panels_m2"])
            print("\033[92mSolar production data obtained correctly\033[0m")
            
            
            ####################################### 2. Get total consumption ########################################
            
            print("Getting total consumption data...")
            total_consumption = get_total_consumption(config_file_data=config, output_file="results/user_data.json")
            print("\033[92mTotal consumption data obtained correctly\033[0m")

            # Check if total electricity consumption is empty or None
            if not isinstance(total_consumption[0], dict) or not total_consumption[0] or all(value == 0 for value in total_consumption[0].values()):
                print("\033[93mElectricity consumption is 0 or None. Setting grid consumption to 0.\033[0m")
                grid_consumption = {timestamp: 0 for timestamp in solar_prod.keys()}
            else:
                print(f"Getting solar grid consumption data...")
                grid_consumption = get_solar_grid_consumption(
                    solar_production=solar_prod,
                    total_electr_consumption=total_consumption[0]
                )
            print("\033[92mSolar grid consumption data obtained correctly\033[0m")

            
            
            
            ######################################## 3. Get battery data ###########################################
        
            #Get the battery data
            print("Getting battery data...")
            battery_data = get_battery_data(battery_capacity_ah=config["battery"]["capacity_ah"],
                                            voltage=config["battery"]["voltage"],
                                            solar_prod=solar_prod,
                                            total_consumpt=total_consumption[0],
                                            charge_eff=config["battery"]["charging_efficiency"],
                                            discharge_eff=config["battery"]["discharging_efficiency"],
                                            energy_loss_convrt=config["battery"]["energy_loss_conversion"],
                                            degrading_ratio=config["battery"]["degrading_ratio"],
                                            initial_state_charge=config["battery"]["initial_state_of_charge_percent"],
                                            type_of_simulation=type_of_simulation)
            print("\033[92mBattery data obtained correctly\033[0m")
            
            ###################################### 4. Get device consumption #######################################
        
            device_consumption = total_consumption[2]
            
            print(f"Getting device statistical data...")
            device_statistical_data = get_device_satistical_data(dev_dict=device_consumption)
            print("\033[92mDevice statistical data obtained correctly\033[0m")
            
            
            ###################################### 5. Get water consumption #######################################
            
            water_consumption = total_consumption[1]
            
            ###################################### 5. Get climate and environment sensors #########################
            
            print("Getting climate and environment sensors data...")
            temperature = getTempHomemade.get_temp_hum()[0]
            humidity = getTempHomemade.get_temp_hum()[1]
            air_quality = getTempHomemade.get_aq()[0]
            air_quality_description = getTempHomemade.get_aq()[1]
            print("\033[92mClimate and environment sensors data obtained correctly\033[0m")
            
            ###################################### 6. Generate output file ########################################
            print("Generating output file...")
            generate_output(
                houseID=config["basic_parameters"]["name"].lower().replace(" ", "_"),
                solar_production=solar_prod,
                electricity_consumption={ts: total_consumption[0] for ts in solar_prod.keys()},  # Convert float to dict
                water_consumption={ts: total_consumption[1] for ts in solar_prod.keys()},  # Convert float to dict
                device_consumption=device_consumption,
                solar_grid_consumption=grid_consumption,
                battery_data=battery_data,
                device_statistical_data=device_statistical_data,
                temperature=temperature,
                humidity=humidity,
                air_quality=air_quality,
                air_quality_description=air_quality_description
            )
            print("\033[92mOutput file generated correctly\033[0m")
            
            print("\033[92mSimulation completed successfully!\033[0m")
            
            time.sleep(interval)
        
        
        
        






if __name__ == "__main__":
    
    import sys
    
    # Check command-line arguments
    if len(sys.argv) == 1:
        # No arguments provided, use default config
        print("No configuration file provided. Using default configuration.")
        complete_simulation_generate()
    elif len(sys.argv) == 2:
        # Configuration file provided as an argument
        print(f"Using configuration file: {sys.argv[1]}")
        config_file = sys.argv[1]
        complete_simulation_generate(config_file)
    else:
        print("Usage: python puppeteer.py [config_file]")
        exit(1)

        
    
    
    
    
    
    




