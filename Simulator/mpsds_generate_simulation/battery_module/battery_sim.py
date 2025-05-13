import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import json
import os
from tqdm import tqdm

def ah_to_kwh(ah, voltage):
    """Convert Amp-hours to kilowatt-hours"""
    return (ah * voltage) / 1000  # Convert Wh to kWh

def kwh_to_ah(kwh, voltage):
    """Convert kilowatt-hours to Amp-hours"""
    return (kwh * 1000) / voltage  # Convert kWh to Wh, then to Ah

def battery_status(battery_capacity_ah, voltage, solar_prod, total_consumpt, charge_eff, discharge_eff, energy_loss_convrt, degrading_ratio, initial_state_charge=100.0, current_time=None):
    """
    Simulates and returns battery status over time, managing state via history.

    Parameters:
    - battery_capacity_ah (float): Battery capacity in Amp-hours (Ah)
    - voltage (float): Battery voltage in Volts
    - solar_prod (float): Solar production in kWh
    - total_consumpt (float): Total consumption in kWh
    - charge_eff (float): Charging efficiency (0 to 1)
    - discharge_eff (float): Discharging efficiency (0 to 1)
    - energy_loss_convrt (float): Energy loss due to conversion (0 to 1)
    - degrading_ratio (float): Battery degradation ratio per cycle/time
    - initial_state_charge (float, optional): Initial state of charge (%) if no history (default: 100.0)
    - current_time (datetime, optional): Time of update (defaults to now)

    Returns:
    dict: Battery status with charge_level_ah, charge_level_kwh, discharging_rate, health_status
    """
    if current_time is None:
        current_time = datetime.now()

    # Convert capacity to kWh
    battery_capacity_kwh = ah_to_kwh(battery_capacity_ah, voltage)

    # History file
    HISTORY_FILE = 'battery_history.json'

    # Load or initialize history
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
        last_update = datetime.fromisoformat(history['last_update'])
        total_cycles = history['total_cycles']
        current_health = history['current_health']
        state_charge = history['readings'][-1]['state_charge'] if history['readings'] else initial_state_charge
    else:
        history = {
            'last_update': current_time.isoformat(),
            'total_cycles': 0,
            'voltage': voltage,
            'current_health': 100,
            'readings': []
        }
        last_update = current_time
        total_cycles = 0
        current_health = 100
        state_charge = initial_state_charge

    # Time elapsed since last update (in hours)
    time_elapsed = (current_time - last_update).total_seconds() / 3600

    # Energy calculations
    net_energy = solar_prod - total_consumpt
    current_charge_kwh = (battery_capacity_kwh * state_charge / 100)

    if net_energy > 0:
        energy_in = net_energy * charge_eff * (1 - energy_loss_convrt)
        new_charge_kwh = min(battery_capacity_kwh, current_charge_kwh + energy_in)
        discharging_rate = 0
    else:
        energy_out = abs(net_energy) / discharge_eff / (1 - energy_loss_convrt)
        new_charge_kwh = max(0, current_charge_kwh - energy_out)
        discharging_rate = energy_out / time_elapsed if time_elapsed > 0 else 0

    new_charge_ah = kwh_to_ah(new_charge_kwh, voltage)
    new_state_charge = (new_charge_kwh / battery_capacity_kwh) * 100
    cycle_fraction = abs(new_state_charge - state_charge) / 100
    total_cycles += cycle_fraction

    # Degradation
    time_factor = time_elapsed * degrading_ratio / (365 * 24)
    cycle_factor = cycle_fraction * degrading_ratio / 1000
    current_health = max(0, current_health - (time_factor + cycle_factor))

    # Current reading
    current_reading = {
        'timestamp': current_time.isoformat(),
        'state_charge': new_state_charge,
        'charge_level_ah': new_charge_ah,
        'charge_level_kwh': new_charge_kwh,
        'discharging_rate': discharging_rate,
        'health_status': current_health,
        'cycles': total_cycles,
        'solar_prod': solar_prod,
        'total_consumpt': total_consumpt
    }

    # Update history
    history['last_update'] = current_time.isoformat()
    history['total_cycles'] = total_cycles
    history['current_health'] = current_health
    history['readings'].append(current_reading)

    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

    return {
        'battery': {
            'charge_level_ah': round(new_charge_ah, 2),
            'charge_level_kwh': round(new_charge_kwh, 2),
            'discharging_rate': round(discharging_rate, 2),
            'health_status': round(current_health, 2)
        }
    }