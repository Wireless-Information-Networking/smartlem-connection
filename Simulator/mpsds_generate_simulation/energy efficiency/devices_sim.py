import random
from datetime import datetime, timedelta

class SmartHomeSimulator:
    def __init__(self, devices):
        self.devices = devices
        
    def get_usage_probability(self, device, hour):
        """
        Returns probability of device being active based on time of day
        """
        usage_patterns = {
            "Smart Light Bulb": {
                "high": [(6, 9), (17, 23)],  # Morning and evening
                "low": [(9, 17), (23, 6)]    # Day and night
            },
            "Smart Thermostat": {
                "high": [(0, 24)],  # Always running, varies with temperature
            },
            "Smart Refrigerator": {
                "high": [(0, 24)],  # Always running, varies with door opens
            },
            "Smart TV": {
                "high": [(19, 23)],  # Evening prime time
                "medium": [(9, 19)], # Day time
                "low": [(23, 9)]     # Night time
            },
            "Smart Speaker": {
                "high": [(7, 9), (17, 22)],  # Morning and evening
                "low": [(9, 17), (22, 7)]    # Work hours and night
            },
            "Smart Plug": {
                "medium": [(9, 23)],  # Active hours
                "low": [(23, 9)]      # Night time
            },
            "Smart Security Camera": {
                "high": [(0, 24)],    # Always running
            },
            "Smart Door Lock": {
                "high": [(7, 9), (17, 19)],  # Coming and going times
                "low": [(0, 7), (9, 17), (19, 24)]
            },
            "Smart Washing Machine": {
                "high": [(10, 14), (18, 21)],  # Common laundry times
                "low": [(0, 10), (14, 18), (21, 24)]
            },
            "Smart Dishwasher": {
                "high": [(19, 22)],    # After dinner
                "medium": [(13, 14)],  # After lunch
                "low": [(0, 13), (14, 19), (22, 24)]
            }
        }
        
        device_pattern = usage_patterns[device["device"]]
        
        # Check which probability band the current hour falls into
        for time_range, ranges in device_pattern.items():
            for start, end in ranges:
                if start <= hour < end:
                    if time_range == "high":
                        return 0.8
                    elif time_range == "medium":
                        return 0.5
                    else:
                        return 0.2
        return 0.1  # Default probability
    
    def calculate_consumption(self, hour):
        """
        Calculate power consumption for all devices at given hour
        """
        total_consumption = 0
        device_states = {}
        
        for device in self.devices:
            probability = self.get_usage_probability(device, hour)
            is_active = random.random() < probability
            
            if is_active:
                # Get random consumption within device's range
                min_consumption, max_consumption = device["consumption_range"]
                consumption = random.uniform(min_consumption, max_consumption)
                
                # Some devices like refrigerators have baseline consumption even when not actively used
                if device["device"] in ["Smart Refrigerator", "Smart Thermostat"]:
                    consumption = max(consumption * 0.3, min_consumption)  # Minimum baseline
            else:
                # Minimal standby power for inactive devices
                consumption = 0.5  # 0.5W standby power
                
                # Some devices maintain higher baseline even when "inactive"
                if device["device"] in ["Smart Refrigerator", "Smart Thermostat"]:
                    min_consumption, _ = device["consumption_range"]
                    consumption = min_consumption * 0.3  # 30% of minimum power
            
            total_consumption += consumption
            device_states[device["device"]] = {
                "active": is_active,
                "consumption": round(consumption, 2)
            }
            
        return round(total_consumption, 2), device_states

def simulate_day(devices, start_hour=0, hours=24):
    """
    Simulate power consumption over specified period
    """
    simulator = SmartHomeSimulator(devices)
    hourly_data = []
    
    for hour in range(start_hour, start_hour + hours):
        hour = hour % 24  # Wrap around to 0-23
        consumption, states = simulator.calculate_consumption(hour)
        hourly_data.append({
            "hour": hour,
            "total_consumption": consumption,
            "device_states": states
        })
    
    return hourly_data

# Example usage:
smart_home_devices = [
    {"device": "Smart Light Bulb", "consumption_range": (5, 20)},
    {"device": "Smart Thermostat", "consumption_range": (3, 10)},
    {"device": "Smart Refrigerator", "consumption_range": (100, 250)},
    {"device": "Smart TV", "consumption_range": (50, 150)},
    {"device": "Smart Speaker", "consumption_range": (5, 20)},
    {"device": "Smart Plug", "consumption_range": (1, 10)},
    {"device": "Smart Security Camera", "consumption_range": (5, 15)},
    {"device": "Smart Door Lock", "consumption_range": (1, 5)},
    {"device": "Smart Washing Machine", "consumption_range": (300, 700)},
    {"device": "Smart Dishwasher", "consumption_range": (200, 500)}
]

# Simulate current hour
current_hour = datetime.now().hour
simulation = simulate_day(smart_home_devices, start_hour=current_hour, hours=1)[0]
print(f"\nCurrent hour ({current_hour}:00) consumption: {simulation['total_consumption']}W")
print("\nDevice states:")
for device, state in simulation['device_states'].items():
    status = "ON" if state['active'] else "STANDBY"
    print(f"{device}: {status} - {state['consumption']}W")