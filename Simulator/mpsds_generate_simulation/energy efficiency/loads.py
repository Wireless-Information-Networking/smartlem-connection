import numpy as np
import random

def gini_coefficient(consumptions):
    """
    Calculate the Gini coefficient for energy consumption distribution.
    
    The Gini coefficient measures inequality in distribution, where:
    - 0 represents perfect equality (all values are the same)
    - 1 represents perfect inequality (one value has everything, others have zero)
    
    Parameters:
    -----------
    consumptions : array-like
        Array of energy consumption values (must be non-negative)
        
    Returns:
    --------
    float
        Gini coefficient value between 0 and 1
        
    Raises:
    -------
    ValueError
        If input array is empty or contains negative values
    """
    # Input validation
    if len(consumptions) == 0:
        raise ValueError("Input array cannot be empty")
    
    consumptions = np.array(consumptions)
    if np.any(consumptions < 0):
        raise ValueError("Energy consumption values cannot be negative")
    
    # If all values are zero, return 0 to avoid division by zero
    if np.all(consumptions == 0):
        return 0.0
    
    # Calculate Gini coefficient
    n = len(consumptions)
    consumptions_sorted = np.sort(consumptions)
    cum_consumptions = np.cumsum(consumptions_sorted)
    
    # Create Lorenz curve points
    lorenz_curve = cum_consumptions / cum_consumptions[-1]
    lorenz_curve = np.insert(lorenz_curve, 0, 0)  # Add starting point (0,0)
    
    # Calculate area under Lorenz curve using trapezoidal rule
    x_points = np.linspace(0, 1, n + 1)  # Include both endpoints
    area_under_lorenz_curve = np.trapz(lorenz_curve, x_points)
    
    # Calculate Gini coefficient
    gini_index = 1 - 2 * area_under_lorenz_curve
    
    return gini_index

if __name__ == "__main__":
    # Define a list of devices and their approximate consumption range in watts
    smart_home_devices = [
        {"device": "Smart Light Bulb", "consumption_range": (5, 20)},  # Light bulbs use small watts
        {"device": "Smart Thermostat", "consumption_range": (3, 10)},  # Low power for thermostats
        {"device": "Smart Refrigerator", "consumption_range": (100, 250)},  # High for fridges
        {"device": "Smart TV", "consumption_range": (50, 150)},  # TVs can vary based on size
        {"device": "Smart Speaker", "consumption_range": (5, 20)},  # Low consumption speakers
        {"device": "Smart Plug", "consumption_range": (1, 10)},  # Plugs are minimal
        {"device": "Smart Security Camera", "consumption_range": (5, 15)},  # Cameras use a little more power
        {"device": "Smart Door Lock", "consumption_range": (1, 5)},  # Locks use very little
        {"device": "Smart Washing Machine", "consumption_range": (300, 700)},  # Washers are energy-hungry
        {"device": "Smart Dishwasher", "consumption_range": (200, 500)},  # Dishwashers also use quite a bit
    ]
    
    import matplotlib.pyplot as plt

    # Initialize an empty list to store Gini coefficients
    gini_indices = []



    # Loop to calculate Gini coefficients for 100 different sets of consumption values
    for _ in range(100):
        consumption_values = np.array([random.randint(device["consumption_range"][0], device["consumption_range"][1]) for device in smart_home_devices])
        gini_index = gini_coefficient(consumption_values)
        gini_indices.append(gini_index)

    
    print("Gini Coefficients for SMD:")
    print("-"*20)
    print(f"Max Gini Coefficient: {max(gini_indices):.4f}")
    print(f"Min Gini Coefficient: {min(gini_indices):.4f}")
    print(f"Average Gini Coefficient: {np.mean(gini_indices):.4f}")
    print(f"Standard Deviation: {np.std(gini_indices):.4f}")
    print("-"*20)

    # Plot the Gini coefficients
    plt.figure(figsize=(10, 6))
    plt.plot(gini_indices, marker='o', linestyle='-', color='b')
    plt.title('Gini Coefficient for Smart Home Devices Over 100 Iterations')
    plt.xlabel('Iteration')
    plt.ylabel('Gini Coefficient')
    plt.grid(True)
    plt.show()