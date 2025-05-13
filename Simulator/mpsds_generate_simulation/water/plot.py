import json
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from datetime import datetime, timedelta

# Define a function to read and process data from a JSON file
def plot_active_devices_from_json(json_file_path):
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    # Extract events data
    events = data.get("events", [])
    devices = set()
    time_intervals = []

    for entry in events:
        timestamp = datetime.strptime(entry["time"], "%H:%M")
        active_devices = entry["active_devices"]
        for device_info in active_devices:
            device = device_info["device"]
            start_time = datetime.strptime(device_info["original_event_time"], "%H:%M")
            duration = timedelta(minutes=device_info["duration"])
            end_time = start_time + duration
            devices.add(device)
            time_intervals.append((device, start_time, end_time))

    # Assign colors to devices
    device_colors = {device: color for device, color in zip(devices, plt.cm.tab10.colors[:len(devices)])}


    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))

    for device, start_time, end_time in time_intervals:
        ax.plot(
            [start_time, end_time],
            [device, device],
            color=device_colors[device],
            linewidth=5,
            solid_capstyle="butt",
            label=device if ax.get_legend_handles_labels()[1].count(device) == 0 else ""
        )

    # Format the x-axis with time
    ax.xaxis.set_major_formatter(dates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(dates.MinuteLocator(interval=5))
    plt.xticks(rotation=45)

    # Set labels and legend
    ax.set_xlabel("Time")
    ax.set_ylabel("Device")
    ax.legend(title="Device", loc="upper left")
    ax.set_title("Active Device Intervals Over Time")
    plt.tight_layout()
    plt.show()


# Call the function with the path to the JSON file
plot_active_devices_from_json("water_usage_snapshots.json")