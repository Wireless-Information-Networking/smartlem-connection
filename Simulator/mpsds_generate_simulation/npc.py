
import time
from datetime import datetime, timedelta, timezone
import random
import matplotlib.pyplot as plt
import json
import os


# Personal modules
from climateEnviroment import temperature_humidty_airquality as getTempHomemade



# Constant for energy used to heat one liter of water (kWh per liter)
ENERGY_PER_LITER_HOT_WATER = 0.035  # Assuming a temperature difference of about 30°C
BASELINE_ELECTRICITY_KWH_PER_5MIN = 0.0125  # 12.5 Wh per 5 minutes, e.g., a 150W refrigerator

#Print the messages of actions being made or so, this does not account for actions, which are run in the background
update_each_seconds = 300 #(5 minutes = 300s)

# Account in minutes or in seconds (seconds (FALSE) is more for development, not for the final version (TRUE), which will be every 5m )
actions_in_minutes = True


def create_json_reg(house_name: str, FILEPATH, typeOfSimulation, start_date=None, end_date=None):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(FILEPATH), exist_ok=True)
    
    if not os.path.exists(FILEPATH):
        data = {
            "house_name": house_name,
            "total_energy_used": 0,
            "total_water_used": 0,
            "total_time": 0,
            "type_of_simulation": typeOfSimulation,
            "start_date": start_date,
            "end_date": end_date,
            "actions": []
        }
        with open(FILEPATH, "w") as file:
            json.dump(data, file, indent=4)
        print("File created with initial structure. House name: ", house_name)
    else:
        print("File already exists.")    
        
def add_action_to_json(NPCtime, action="NAN", device_used="NAN", energy_used=0, water_used=0, duration=0, npc_name="Unknown", FILEPATH="results/user_data.json", print_message=True):
    with open(FILEPATH, "r") as file:
        data = json.load(file)
    
    
    formatted_time = NPCtime.isoformat()# e.g., "2021-01-01T00:05:00+01:00"
    
    new_action = {
        "timestamp": formatted_time,  # e.g., "2021-01-01 00:05:00"
        "npc": npc_name,
        "action": action,
        "device_used": device_used,
        "energy_used": energy_used,
        "water_used": water_used,
        "duration": duration
    }
    
    data["actions"].append(new_action)
    data["total_energy_used"] += energy_used
    data["total_water_used"] += water_used
    data["total_time"] += duration
    
    with open(FILEPATH, "w") as file:
        json.dump(data, file, indent=4)
    
    
    timestamp = datetime.now(timezone.utc).strftime('%H:%M:%S')
    if print_message:
        print(f"[{timestamp}] \033[93mAdded action to JSON\033[0m")


# Data for plotting


class House:
    def __init__(self, config_data, temperature=20, humidity=50, month=1, year=2025):
        # Basic parameters
        self.name = config_data["basic_parameters"]["name"]
        self.number_of_people = config_data["basic_parameters"]["number_of_people"]
        self.rooms = {
            "rooms": config_data["basic_parameters"]["rooms"],
            "bathrooms": config_data["basic_parameters"]["bathrooms"],
            "kitchen": config_data["basic_parameters"]["kitchen"],
            "living_room": config_data["basic_parameters"]["living_room"],
            "dining_room": config_data["basic_parameters"]["dining_room"],
            "garage": config_data["basic_parameters"]["garage"],
            "garden": config_data["basic_parameters"]["garden"]
        }
        
        # Environmental conditions
        self.temperature = temperature
        self.humidity = humidity
        self.month = month
        self.year = year
        
        # House specifications
        self.volume = config_data["house"]["volume_cubic_meters"]
        
        # Solar system
        self.solar_system = {
            "panel_efficiency": config_data["solar_panels"]["panel_eff"],
            "number_of_panels": config_data["solar_panels"]["number_of_panels"],
            "panel_size": config_data["solar_panels"]["size_of_panels_m2"]
        }
        
        # Battery system
        self.battery = {
            "capacity": config_data["battery"]["capacity_ah"],
            "voltage": config_data["battery"]["voltage"],
            "state_of_charge": config_data["battery"]["initial_state_of_charge_percent"],
            "charging_efficiency": config_data["battery"]["charging_efficiency"],
            "discharging_efficiency": config_data["battery"]["discharging_efficiency"],
            "energy_loss": config_data["battery"]["energy_loss_conversion"],
            "degrading_ratio": config_data["battery"]["degrading_ratio"]
        }
        
        # Water heating
        self.water_heating = {
            "method": config_data["water_heating"]["selected_method"],
            "available_options": config_data["water_heating"]["options"]
        }
        
        # Emission factors
        self.emission_factors = {
            "solar_panel": {
                "min": config_data["emission_factors"]["solar_panel_emission_factor_kgCO2_per_kWh"]["min"],
                "max": config_data["emission_factors"]["solar_panel_emission_factor_kgCO2_per_kWh"]["max"]
            },
            "cold_water": config_data["emission_factors"]["cold_water_emission_factor_kgCO2_per_L"],
            "hot_water": config_data["emission_factors"]["hot_water_emission_factor_kgCO2_per_L"]
        }
        
        # Devices
        self.water_devices = config_data["water_devices"]
        self.electricity_devices = config_data["electricity_devices"]
        
        self.device_electricity_usage = {}
        for device in self.electricity_devices:
            key = f"{device['room']}_{device['device']}"
            self.device_electricity_usage[key] = 0
        
        self.total_electricity_used_kwh = 0
        self.total_water_used_liters = 0
        
        # Add device state tracking
        self.device_states = {}
        for device in self.water_devices + self.electricity_devices:
            key = f"{device['room']}_{device['device']}"
            self.device_states[key] = {
                "type": "water" if device in self.water_devices else "electricity",
                "info": device,
                "in_use": False,
                "used_by": None
            }
            
    def is_device_available(self, device_name, room_name):
        key = f"{room_name}_{device_name}"
        if key in self.device_states:
            return not self.device_states[key]["in_use"]
        return False
        
    def get_total_rooms(self):
        """Return the total number of rooms in the house"""
        return sum(self.rooms.values())
    
    def get_solar_capacity(self):
        """Calculate total solar panel capacity in square meters"""
        return self.solar_system["number_of_panels"] * self.solar_system["panel_size"]
    
    def get_battery_capacity_kwh(self):
        """Calculate battery capacity in kWh"""
        return (self.battery["capacity"] * self.battery["voltage"]) / 1000
    
    def get_device_by_name(self, device_name):
        """Find a device by its name in either water or electricity devices"""
        for device in self.water_devices:
            if device["device"].lower() == device_name.lower():
                return {"type": "water", "device": device}
        
        for device in self.electricity_devices:
            if device["device"].lower() == device_name.lower():
                return {"type": "electricity", "device": device}
        
        return None

    
    def has_device_in_room(self, device_name, room_name):
        """Check if a device exists in a specific room"""
        for device in self.water_devices + self.electricity_devices:
            if (device["device"].lower() == device_name.lower() and 
                device.get("room", "").lower() == room_name.lower()):
                return True
        return False
    
    
    
class Action:
    def __init__(self, name, duration, location, required_device=None, need_changes=None, next_action=None, allowed_age_groups=None):
        self.name = name
        self.location = location
        self.required_device = required_device
        self.need_changes = need_changes or {}
        self.next_action = next_action
        
        # Default to all age groups if not specified
        self.allowed_age_groups = allowed_age_groups or ["child", "teenager", "adult", "elderly"]
        
        if actions_in_minutes:  # Assuming this is a global flag for time units
            self.duration = duration * 60
        else:
            self.duration = duration
        

class NPC:
    def __init__(self, name, out_of_home_periods, house, age_group, simulation_type="fast_forward"):
        self.name = name
        self.age_group = age_group
        self.out_of_home_periods = out_of_home_periods
        self.house = house
        self.current_room = "Living Room"
        self.state = "Idle"
        self.action_start_time = None
        self.current_action = None
        self.action_end_time = None
        self.action_chain = []
        self.needs = {
            "hunger": random.randint(0, 100),
            "energy": random.randint(0, 100),
            "hygiene": random.randint(0, 100),
            "fun": random.randint(0, 100),
            "temperature": 22
        }
        # Initialize datetimes based on simulation type
        if simulation_type == "realtime":
            self.time = datetime.now(timezone.utc)
        else:  # Default to naive for "fast_forward" to match original behavior
            self.time = datetime.now()
        self.last_toilet_time = self.time
        self.actions = {}
        self._setup_actions()

    def _setup_actions(self):
        """Setup actions with their proper chains as per diagram"""
        # Create actions first
        self.actions = {
            "cook": Action(
                name="cook",
                duration=30,
                location="Kitchen",
                required_device="stove",
                need_changes={"hunger": 0, "energy": -20, "hygiene": -25, "fun": 15},
                allowed_age_groups=["adult", "elderly"]
            ),
            "eat": Action(
                name="eat",
                duration=20,
                location="Dining Room",
                need_changes={"hunger": -70, "energy": 20, "hygiene": -20, "fun": 20},
                allowed_age_groups=["child", "teenager", "adult", "elderly"]
            ),
            "use_dishwasher": Action(
                name="use_dishwasher",
                duration=5,
                location="Kitchen",
                required_device="dishwasher",
                need_changes={"hunger": 0, "energy": -5, "hygiene": 7, "fun": -10},
                allowed_age_groups=["adult", "elderly"]
            ),
            "wash_hands": Action(
                name="wash_hands",
                duration=2,
                location="Bathroom",
                required_device="sink",
                need_changes={"hunger": 0, "energy": -2, "hygiene": 30, "fun": 0},
                allowed_age_groups=["child", "teenager", "adult", "elderly"]
            ),
            "brush_teeth": Action(
                name="brush_teeth",
                duration=5,
                location="Bathroom",
                required_device="sink",
                need_changes={"hunger": 0, "energy": -5, "hygiene": 35, "fun": 0},
                allowed_age_groups=["child", "teenager", "adult", "elderly"]
            ),
            "nap_sleep": Action(
                name="nap_sleep",
                duration=30,
                location="Bedroom",
                need_changes={"hunger": 20, "energy": 80, "hygiene": -15, "fun": 5},
                allowed_age_groups=["child", "teenager", "adult", "elderly"]
            ),
            "shower": Action(
                name="shower",
                duration=10,
                location="Bathroom",
                required_device="shower",
                need_changes={"hunger": 0, "energy": 5, "hygiene": 55, "fun": 0},
                allowed_age_groups=["child", "teenager", "adult", "elderly"]
            ),
            "watch_tv": Action(
                name="watch_tv",
                duration=60,
                location="Living Room",
                required_device="tv",
                need_changes={"hunger": 15, "energy": 5, "hygiene": -5, "fun": 35},
                allowed_age_groups=["child", "teenager", "adult", "elderly"]
            ),
            "play_games": Action(
                name="play_games",
                duration=15,
                location="Living Room",
                required_device="gaming_console",
                need_changes={"hunger": 20, "energy": -20, "hygiene": -15, "fun": 30},
                allowed_age_groups=["child", "teenager", "adult", "elderly"]
            ),
            "go_for_walk": Action(
                name="go_for_walk",
                duration=20,
                location="Outside",
                need_changes={"hunger": 35, "energy": -30, "hygiene": -15, "fun": 25},
                allowed_age_groups=["child", "teenager", "adult", "elderly"]
            ),
            "use_toilet": Action(
                name="use_toilet",
                duration=3,
                location="Bathroom",
                required_device="toilet",
                need_changes={"hunger": 0, "energy": -1, "hygiene": 5, "fun": 0},
                allowed_age_groups=["child", "teenager", "adult", "elderly"]
            ),
            "call_friend": Action(
                name="call_friend",
                duration=5,
                location="Living Room",
                need_changes={"hunger": 5, "energy": -5, "hygiene": 0, "fun": 10},
                allowed_age_groups=["child", "teenager", "adult", "elderly"]
            ),
            "read_book": Action(
                name="read_book",
                duration=15,
                location="Bedroom",
                need_changes={"hunger": 10, "energy": -5, "hygiene": 0, "fun": 20},
                allowed_age_groups=["child", "teenager", "adult", "elderly"]
            ),
            "go_shopping": Action(
                name="go_shopping",
                duration=25,
                location="Outside",
                need_changes={"hunger": 5, "energy": -5, "hygiene": 0, "fun": 10},
                allowed_age_groups=["adult", "elderly", "teenager"]
            ),
            "go_for_jog": Action(
                name="go_for_jog",
                duration=20,
                location="Outside",
                need_changes={"hunger": 25, "energy": -20, "hygiene": -15, "fun": 25},
                allowed_age_groups=["adult", "teenager"]
            ),
            "go_to_gym": Action(
                name="go_to_gym",
                duration=30,
                location="Outside",
                need_changes={"hunger": 30, "energy": -35, "hygiene": -20, "fun": 30},
                allowed_age_groups=["adult", "teenager"]
            ),
            "clean_house": Action(
                name="clean_house",
                duration=30,
                location="Living Room",
                required_device="vacuum_cleaner",
                need_changes={"hunger": 20, "energy": -20, "hygiene": 20, "fun": -20},
                allowed_age_groups=["adult", "elderly"]
            ),
            "study": Action(
                name="study",
                duration=25,
                location="Bedroom",
                required_device="computer",
                need_changes={"hunger": 15, "energy": -25, "hygiene": -10, "fun": -15},
                allowed_age_groups=[ "teenager", "adult", "elderly"]
            ),
            "overthink": Action(
                name="overthink",
                duration=10,
                location="Bedroom",
                need_changes={"hunger": 5, "energy": -10, "hygiene": 0, "fun": -10},
                allowed_age_groups=["adult", "elderly", "t"]
            ),
        }
        
        # Setup action chains as per diagram
        self.actions["cook"].next_action = "eat"
        self.actions["eat"].next_action = "use_dishwasher"
        self.actions["use_dishwasher"].next_action = "wash_hands"
        self.actions["wash_hands"].next_action = "brush_teeth"
        self.actions["go_for_jog"].next_action = "shower"
        self.actions["go_to_gym"].next_action = "shower"

    def update_needs(self):
        """Update needs based on time and house conditions"""
        self.needs["hunger"] = min(100, self.needs["hunger"] + 0.5)
        self.needs["energy"] = max(0, self.needs["energy"] - 0.3)
        self.needs["hygiene"] = max(0, self.needs["hygiene"] - 0.7)
        self.needs["fun"] = max(0, self.needs["fun"] - 0.4)
        
        # Adjust needs based on house temperature
        temp_diff = abs(int(self.house.temperature) - int(self.needs["temperature"]))
        if temp_diff > 5:
            self.needs["energy"] = max(0, self.needs["energy"] - int(temp_diff / 5))
            self.needs["fun"] = max(0, self.needs["fun"] - int(temp_diff / 5))
        
        # Toilet need every 2 hours
        if (self.time - self.last_toilet_time).seconds >= 7200 and self.actions["use_toilet"] not in self.action_chain:
            self.action_chain.append(self.actions["use_toilet"])
            self.last_toilet_time = self.time
            
    
    def is_out_of_home(self):
        for period in self.out_of_home_periods:
            start_dt = datetime.strptime(f"{self.time.date()} {period['start']}", "%Y-%m-%d %H:%M").replace(tzinfo=self.time.tzinfo)
            end_dt = datetime.strptime(f"{self.time.date()} {period['end']}", "%Y-%m-%d %H:%M").replace(tzinfo=self.time.tzinfo)
            if end_dt < start_dt:  # Crosses midnight
                end_dt += timedelta(days=1)
            if start_dt <= self.time <= end_dt:
                return True, period["reason"]
        return False, None


    def decide_next_action(self):
        """Decide next action based on needs and chains"""
        
        # If out of home, do nothing
        if self.is_out_of_home()[0]:
            reason = self.is_out_of_home()[1]
            return "out_of_home", reason
        
        
        # If there's an action chain in progress, continue it
        if self.action_chain:
            return self.action_chain.pop(0)
            
        # Critical needs first
        if self.needs["energy"] < 20:
            return self.actions["nap_sleep"]
        
        if self.needs["hunger"] > 85:
            # Start the cooking -> eating -> cleaning chain
            self.action_chain = []
            current = self.actions["cook"]
            while current:
                self.action_chain.append(current)
                current = self.actions[current.next_action] if current.next_action else None
            return self.action_chain.pop(0)
            
        if self.needs["hygiene"] < 30:
            return self.actions["shower"]
            
        if self.needs["fun"] < 30:
            return random.choice([self.actions["watch_tv"], self.actions["play_games"]])
        
        # If too much energy
        if self.needs["energy"] > 80:
            return random.choice([self.actions["go_for_jog"], self.actions["go_to_gym"]])
        
        # If too much fun
        if self.needs["fun"] > 70:
            return random.choice([self.actions["clean_house"], self.actions["study"], self.actions["overthink"]])
        

            
        #return None

        #If non of the if's work: its idle, choose a random action
        return random.choice([self.actions["call_friend"], self.actions["read_book"], self.actions["go_shopping"]])




            
    def perform_action(self, action):
        if self.age_group not in action.allowed_age_groups:
            self.activity = f"{self.name} cannot perform {action.name} because it is not allowed for their age group."
            return
        
        if action.required_device and not self.house.is_device_available(action.required_device, action.location):
            self.activity = f"{self.name} cannot perform {action.name} because {action.required_device} in {action.location} is in use."
            return
        
        if action.required_device and not self.house.has_device_in_room(action.required_device, action.location):
            self.activity = f"{self.name} cannot perform {action.name} because {action.required_device} is not in {action.location}."
            return
        
        self.current_room = action.location
        self.state = "Performing Action"
        self.current_action = action
        self.action_start_time = self.time  # Set start time
        self.action_end_time = self.time + timedelta(seconds=action.duration)
        self.activity = f"{self.name} started {action.name} in {self.current_room} (will take {(action.duration)/60} minutes ({action.duration} seconds))."
                
        # Mark the device as in use
        if action.required_device:
            key = f"{action.location}_{action.required_device}"
            self.house.device_states[key]["in_use"] = True
            self.house.device_states[key]["used_by"] = self.name
        
     


    def finish_action(self):
        if self.current_action and self.state == "Performing Action":
            # Update needs
            for need, change in self.current_action.need_changes.items():
                new_value = self.needs[need] + change
                self.needs[need] = max(0, min(100, new_value))
            
            # Calculate resource usage
            energy_kwh = 0
            water_used_liters = 0
            
            if self.current_action.required_device:
                device_info = self.house.get_device_by_name(self.current_action.required_device)
                if device_info:
                    device_type = device_info["type"]
                    device = device_info["device"]
                    
                    if device_type == "electricity":
                        power_watts = device.get("power_watts", 0)
                        energy_kwh = (power_watts * (self.current_action.duration / 3600)) / 1000
                        self.house.total_electricity_used_kwh += energy_kwh
                        device_key = f"{self.current_room}_{self.current_action.required_device}"
                        if device_key in self.house.device_electricity_usage:
                            self.house.device_electricity_usage[device_key] += energy_kwh
                            
                    elif device_type == "water":
                        flow_rate_lpm = device.get("flow_rate_liters_per_minute", 0)
                        water_used_liters = flow_rate_lpm * (self.current_action.duration / 60)
                        self.house.total_water_used_liters += water_used_liters
                        if device["device"] in ["shower", "sink"] and self.house.water_heating["method"] == "electricity":
                            heating_energy = water_used_liters * ENERGY_PER_LITER_HOT_WATER
                            energy_kwh = heating_energy
                            self.house.total_electricity_used_kwh += heating_energy
                    
                    # Release device
                    key = f"{self.current_room}_{self.current_action.required_device}"
                    self.house.device_states[key]["in_use"] = False
                    self.house.device_states[key]["used_by"] = None
            
            # Log action with full timestamp
            add_action_to_json(
                NPCtime=self.time,  # Pass datetime object
                action=self.current_action.name,
                device_used=self.current_action.required_device or "NAN",
                energy_used=energy_kwh,
                water_used=water_used_liters,
                duration=self.current_action.duration,
                npc_name=self.name,
                FILEPATH="results/user_data.json",
                print_message=False
            )
            
            # Reset state and immediately decide next action
            self.current_action = None
            self.action_end_time = None
            self.state = "Idle"
            self.activity = f"{self.name} finished the action in {self.current_room}."
            next_action = self.decide_next_action()
            if next_action and not isinstance(next_action, tuple):
                self.perform_action(next_action)
            
            
                
            


    def decide_and_act(self):
        self.update_needs()
        
        if self.state == "Performing Action":
            if self.time >= self.action_end_time:
                self.finish_action()
            else:
                self.activity = f"{self.name} is still performing {self.current_action.name}."
        elif self.state == "Idle":
            next_action = self.decide_next_action()
            if next_action:
                if isinstance(next_action, tuple) and next_action[0] == "out_of_home":
                    self.activity = f"{self.name} is out of home because of {next_action[1]}."
                    add_action_to_json(
                        NPCtime=self.time,  # Pass datetime object
                        action=next_action[1],
                        device_used="NAN",
                        energy_used=0,
                        water_used=0,
                        duration=0,
                        npc_name=self.name,
                        FILEPATH="results/user_data.json",
                        print_message=False
                    )
                else:
                    self.perform_action(next_action)
            else:
                self.activity = f"{self.name} is idle."
                
                
                

    def display_stats(self):
        """Display the NPC's current stats."""
        hunger_status = "Very Hungry" if self.needs["hunger"] > 70 else "Hungry" if self.needs["hunger"] > 50 else "Not Hungry"
        energy_status = "Exhausted" if self.needs["energy"] < 20 else "Tired" if self.needs["energy"] < 50 else "Energetic"
        hygiene_status = "Dirty" if self.needs["hygiene"] < 30 else "Clean"
        fun_status = "Bored" if self.needs["fun"] < 30 else "Having Fun"

        
        return (f"\033[94mStats: Hunger={self.needs['hunger']} ({hunger_status}) | "
                f"Energy={self.needs['energy']} ({energy_status}) | "
                f"Hygiene={self.needs['hygiene']} ({hygiene_status}) | "
                f"Fun={self.needs['fun']} ({fun_status})\033[0m")


#################################################################### NPC CONFIG ####################################################################

def run_simulation(config_data, output_path="results/user_data.json", update_interval=300, actions_in_minutes_flag=True, start_date=None, end_date=None):
    global update_each_seconds, actions_in_minutes
    update_each_seconds = update_interval
    actions_in_minutes = actions_in_minutes_flag
    
    # Simulation setup
    type_of_simulation = config_data['basic_parameters']['type_of_simulation']["type"]
    config_start_date = config_data['basic_parameters']['type_of_simulation'].get("start_date")
    config_end_date = config_data['basic_parameters']['type_of_simulation'].get("end_date")
    
    sim_start_date = start_date if start_date else config_start_date
    sim_end_date = end_date if end_date else config_end_date

    # Initialize house
    temp, humidi = getTempHomemade.get_temp_hum()
    now = datetime.now()
    house = House(config_data, temperature=temp, humidity=humidi, month=now.month, year=now.year)

    create_json_reg(house_name=config_data["basic_parameters"]["name"], FILEPATH=output_path, typeOfSimulation=type_of_simulation,
                    start_date=sim_start_date if type_of_simulation == "fast_forward" else None,
                    end_date=sim_end_date if type_of_simulation == "fast_forward" else None)



    # Initialize NPCs
    npcs = [NPC(name=npc["name"], out_of_home_periods=npc.get("out_of_home_periods", []), house=house, age_group=npc["age_group"], simulation_type="fast_forward") 
        for npc in config_data['basic_parameters']['npc']]


    # Initial output (unchanged)
    print("-" * 50)
    print(f"Simulation started for {config_data['basic_parameters']['name']}. Press Ctrl+C to stop.")
    print(f"Type of simulation: {type_of_simulation}")
    print(f"Initial temperature: {house.temperature}°C, Humidity: {house.humidity}%")
    print(f"Updates every {update_interval} seconds.")
    print(f"Actions in minutes: {actions_in_minutes_flag}")
    print("-" * 50)
    for npc in npcs:
        print(f"\033[94mName of NPC: {npc.name}\033[0m")
        print(f"\033[94mAge group: {npc.age_group}\033[0m")
    print("-" * 50)

    # Simulation loop
    try:
        
        simulation_time = datetime.strptime(sim_start_date + " 00:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(timedelta(hours=1)))
        end_time = datetime.strptime(sim_end_date + " 00:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(timedelta(hours=1)))
        print(f"Simulating from {simulation_time.isoformat()} to {end_time.isoformat()}")

        electricity_consumption = {}
        water_consumption = {}
        device_usage = {}

        npcs = [NPC(name=npc["name"], out_of_home_periods=npc.get("out_of_home_periods", []), house=house, age_group=npc["age_group"]) 
                for npc in config_data['basic_parameters']['npc']]
        for npc in npcs:
            npc.time = simulation_time
            npc.last_toilet_time = simulation_time

        iteration_count = 0
        while simulation_time < end_time:
            interval_start = simulation_time
            timestamp = simulation_time.isoformat()
            #print(f"Iteration {iteration_count}: Simulating at {timestamp}")
            
            interval_electricity = 0
            interval_water = 0
            interval_devices = {"electricity": {}, "water": {}}
            try:
                for npc in npcs:
                    npc.time = interval_start
                    npc.decide_and_act()
                    #print(f"[{npc.time.isoformat()}] {npc.name} state: {npc.state}, action: {npc.current_action.name if npc.current_action else 'None'}")
                    if npc.state == "Performing Action":
                        start_time = max(npc.action_start_time, interval_start)
                        action_end_in_interval = min(simulation_time + timedelta(minutes=5), npc.action_end_time)
                        active_time_seconds = (action_end_in_interval - start_time).total_seconds() if action_end_in_interval > start_time else 0
                        #print(f"  Action {npc.current_action.name}: {start_time.isoformat()} to {action_end_in_interval.isoformat()}, active for {active_time_seconds}s")

                        if active_time_seconds > 0 and npc.current_action.required_device:
                            device_info = house.get_device_by_name(npc.current_action.required_device)
                            if device_info:
                                device_type = device_info["type"]
                                device = device_info["device"]
                                device_key = f"{npc.current_room}_{npc.current_action.required_device}"

                                if device_type == "electricity":
                                    power_watts = device.get("power_watts", 0)
                                    energy_kwh = (power_watts * active_time_seconds / 3600) / 1000
                                    interval_electricity += energy_kwh
                                    interval_devices["electricity"][device_key] = interval_devices["electricity"].get(device_key, 0) + energy_kwh
                                    house.total_electricity_used_kwh += energy_kwh
                                    #print(f"  Electricity: {energy_kwh} kWh")

                                elif device_type == "water":
                                    flow_rate_lpm = device.get("flow_rate_liters_per_minute", 0)
                                    water_used_liters = flow_rate_lpm * (active_time_seconds / 60)
                                    interval_water += water_used_liters
                                    interval_devices["water"][device_key] = interval_devices["water"].get(device_key, 0) + water_used_liters
                                    house.total_water_used_liters += water_used_liters
                                    #print(f"  Water: {water_used_liters} L")
                                    if device["device"] in ["shower", "sink"] and house.water_heating["method"] == "electricity":
                                        heating_energy = water_used_liters * ENERGY_PER_LITER_HOT_WATER
                                        interval_electricity += heating_energy
                                        house.total_electricity_used_kwh += heating_energy
                                        #print(f"  Heating: {heating_energy} kWh")

                electricity_consumption[timestamp] = interval_electricity
                water_consumption[timestamp] = interval_water
                device_usage[timestamp] = interval_devices
            except Exception as e:
                print(f"Error in iteration {iteration_count}: {e}")
                raise
            
            simulation_time += timedelta(minutes=5)
            #print(f"Next simulation_time: {simulation_time.isoformat()} < {end_time.isoformat()} = {simulation_time < end_time}")
            iteration_count += 1

        print("-" * 50)
        print("Simulation completed.")
        print(f"Total electricity used: {house.total_electricity_used_kwh:.2f} kWh")
        print(f"Total water used: {house.total_water_used_liters:.2f} liters")

        """
        with open("results/electricity_consumption.json", "w") as file:
            json.dump(electricity_consumption, file, indent=4)
        with open("results/water_consumption.json", "w") as file:
            json.dump(water_consumption, file, indent=4)
        with open("results/device_usage.json", "w") as file:
            json.dump(device_usage, file, indent=4)
        """
        

        return electricity_consumption, water_consumption, device_usage

    except KeyboardInterrupt:
        print("Simulation stopped by user.")
        print(f"Total electricity used: {house.total_electricity_used_kwh:.2f} kWh")
        print(f"Total water used: {house.total_water_used_liters:.2f} liters")


def run_simulation_realtime(config_data, output_path="results/user_data.json"):
    # Initialize house with current temperature, humidity, and time
    temp, humidi = getTempHomemade.get_temp_hum()
    now = datetime.now()
    house = House(config_data, temperature=temp, humidity=humidi, month=now.month, year=now.year)

    # Save initial results to JSON
    create_json_reg(house_name=config_data["basic_parameters"]["name"], 
                    FILEPATH=output_path, 
                    typeOfSimulation="realtime", 
                    start_date=None, 
                    end_date=None)
    
    # Initialize NPCs
    npcs = [NPC(name=npc["name"], 
                out_of_home_periods=npc.get("out_of_home_periods", []), 
                house=house, 
                age_group=npc["age_group"], 
                simulation_type="realtime") 
            for npc in config_data['basic_parameters']['npc']]

    # Define baseline electricity consumption per 5-minute interval
    BASELINE_ELECTRICITY_KWH_PER_5MIN = 0.0125  # e.g., 12.5 Wh (150W fridge over 5 min)

    # Initialize resource tracking
    house.total_electricity_used_kwh = BASELINE_ELECTRICITY_KWH_PER_5MIN  # Start with baseline
    house.total_water_used_liters = 0.0
    device_usage = {"electricity": {"always_on": BASELINE_ELECTRICITY_KWH_PER_5MIN}, "water": {}}

    # Update NPCs and calculate additional consumption
    for npc in npcs:
        npc.time = datetime.now(timezone.utc)
        npc.decide_and_act()
        print(f"[{npc.time.isoformat()}] {npc.name}: {npc.activity}")
        print(npc.display_stats())

        # Track device usage if an action occurs
        if npc.state == "Performing Action" and npc.current_action and npc.current_action.required_device:
            device_info = house.get_device_by_name(npc.current_action.required_device)
            if device_info:
                device_type = device_info["type"]
                device_key = f"{npc.current_room}_{npc.current_action.required_device}"

                if device_type == "electricity":
                    power_watts = device_info["device"].get("power_watts", 0)
                    energy_kwh = (power_watts * (npc.current_action.duration / 3600)) / 1000
                    device_usage["electricity"][device_key] = device_usage["electricity"].get(device_key, 0) + energy_kwh
                    house.total_electricity_used_kwh += energy_kwh

                elif device_type == "water":
                    flow_rate_lpm = device_info["device"].get("flow_rate_liters_per_minute", 0)
                    water_used_liters = flow_rate_lpm * (npc.current_action.duration / 60)
                    device_usage["water"][device_key] = device_usage["water"].get(device_key, 0) + water_used_liters
                    house.total_water_used_liters += water_used_liters

    # Output results
    print(f"Total electricity used: {house.total_electricity_used_kwh:.2f} kWh")
    print(f"Total water used: {house.total_water_used_liters:.2f} liters")
    return house.total_electricity_used_kwh, house.total_water_used_liters, device_usage

        

if __name__ == "__main__":
    
    #If the type is fast forward, run the simulation with run_simulation, if the type is realtime, run the simulation with run_simulation_realtime
    pass    
    """
    with open('config_default.json', 'r') as file:
        config_data = json.load(file)
    run_simulation(config_data)
    """
    """
    with open('config_default.json', 'r') as file:
        config_data = json.load(file)

    try:
        print("Real-time simulation started. Press Ctrl+C to stop.")
        while True:
            run_simulation_realtime(config_data)
            time.sleep(300)  # Wait for 5 minutes (300 seconds)
    except KeyboardInterrupt:
        print("Simulation stopped by user.")
    """
