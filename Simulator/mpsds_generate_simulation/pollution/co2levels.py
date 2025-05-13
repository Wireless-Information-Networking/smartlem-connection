import numpy as np
import matplotlib.pyplot as plt
from random import randint

# Parameters
V = 297.5  # Volume of the house in m³
CO2_ext = randint(200, 400)   # Outdoor CO2 concentration in ppm
person_emission = 15  # CO2 emission per person per hour in L
timestep = 5  # Time step in minutes
steps = 24 * 60 // timestep  # Number of simulation steps for 24 hours
ACH_winter = 0.3  # Air Changes per Hour in winter
ACH_summer = 0.7  # Air Changes per Hour in summer

# Enhanced occupant schedule with door/window behavior
# Occupancy changes throughout the day
occupancy_schedule = [2] * 84 + [0] * 96 + [3] * 84  # Night: 2, Day: 0, Evening: 3
window_schedule = [0] * 84 + [1] * 96 + [0] * 84    # Windows open during the day
door_closed_schedule = [1] * 84 + [0] * 96 + [1] * 84  # Bedroom doors closed at night and evening

# Repeat schedules to match the number of steps
occupancy_schedule = (occupancy_schedule * (steps // len(occupancy_schedule) + 1))[:steps]
window_schedule = (window_schedule * (steps // len(window_schedule) + 1))[:steps]
door_closed_schedule = (door_closed_schedule * (steps // len(door_closed_schedule) + 1))[:steps]

# Season-specific parameters
season = "winter"  # Change to "winter" for winter simulation
ACH = ACH_winter if season == "winter" else ACH_summer

# Simulation
CO2_levels = [CO2_ext]  # Initial CO2 concentration in ppm
for step in range(steps):
    occupants = occupancy_schedule[step]
    windows_open = window_schedule[step]
    doors_closed = door_closed_schedule[step]

    # Adjust ACH based on windows
    current_ACH = ACH * (1.5 if windows_open else 1.0)  # Higher ventilation with open windows

    # CO2 generation
    gen_CO2 = (occupants * person_emission * timestep / 60) * 1000 / V  # Convert to ppm

    # Ventilation effect
    ventilation_loss = (CO2_levels[-1] - CO2_ext) * (1 - np.exp(-current_ACH * timestep / 60))

    # Door effect: reduce ventilation efficiency by 30% if doors are closed
    if doors_closed:
        ventilation_loss *= 0.7

    # Update CO2 levels
    new_CO2 = CO2_levels[-1] + gen_CO2 - ventilation_loss
    CO2_levels.append(new_CO2)

    # Debugging Output
    print(f"Step {step}: Occupants={occupants}, Gen_CO2={gen_CO2:.2f}, "
          f"Ventilation_Loss={ventilation_loss:.2f}, CO2={new_CO2:.2f}")

# Time array for plotting
time = np.arange(0, 24, timestep / 60)

# Plot
plt.figure(figsize=(12, 6))
plt.plot(time, CO2_levels[:-1], label="CO2 Levels (ppm)")
plt.axhline(1000, color='red', linestyle='--', label="Recommended Limit (1000 ppm)")
plt.xlabel("Time (hours)")
plt.ylabel("CO2 Concentration (ppm)")
plt.title(f"CO2 Levels Simulation ({season.capitalize()})")
plt.legend()
plt.grid()
plt.show()
