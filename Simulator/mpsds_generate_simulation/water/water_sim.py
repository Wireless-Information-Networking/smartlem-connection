import random
import json
from datetime import datetime, timedelta


class WaterUsageSimulator:
    def __init__(self, config_file, sampling_rate=5):
        """
        Initialize the simulator using a configuration file.

        :param config_file: Path to the JSON file with device configurations.
        :param sampling_rate: Sampling interval in minutes.
        """
        with open(config_file, 'r') as f:
            self.devices = json.load(f)
            print(f"Loaded {len(self.devices)} devices from {config_file}")
        self.sampling_rate = sampling_rate
        self.total_simulation_time = 24 * 60  # 24 hours in minutes

    def _get_activation_probability(self, device, current_hour, current_uses):
        """
        Determine the probability of device activation based on usage patterns.

        :param device: Device configuration.
        :param current_hour: Current hour of the day.
        :param current_uses: Number of times the device has been used.
        :return: Probability of activation.
        """
        usage_patterns = device['usage_patterns']
        max_use_factor = 1 - (current_uses / device['max_uses_per_day'])

        # Define time periods and their associated pattern keys
        if 6 <= current_hour < 9:
            time_key = 'morning'
        elif 11 <= current_hour < 14:
            time_key = 'midday'
        elif 17 <= current_hour < 20:
            time_key = 'dinner'
        elif 20 <= current_hour < 22:
            time_key = 'evening'
        else:
            time_key = 'other'

        # Get the specific probability for the time period
        activation_prob = usage_patterns.get(time_key, 0.0)

        # Only proceed if there's a non-zero probability for this time period
        if activation_prob > 0:
            return activation_prob * max_use_factor

        return 0.0

    def simulate(self):
        """
        Run the water usage simulation for 24 hours with 5-minute snapshots

        :return: Time-based simulation results
        """
        # Track uses for each device
        device_uses = {device['device']: 0 for device in self.devices}

        # Track ongoing device events
        ongoing_events = {}

        # Events tracking (snapshots every 5 minutes)
        all_events = []

        # Simulate each 5-minute interval of the day
        for minute in range(0, self.total_simulation_time, self.sampling_rate):
            current_hour = minute // 60
            current_time = f"{current_hour:02d}:{minute % 60:02d}"

            # Snapshot for this sampling period
            snapshot = {
                'time': current_time,
                'active_devices': []
            }

            # Process ongoing events
            for device_name, event in list(ongoing_events.items()):
                # Check if event is still ongoing
                end_time = datetime.strptime(event['end_time'], "%H:%M")
                current_datetime = datetime.strptime(current_time, "%H:%M")

                if current_datetime <= end_time:
                    # Device is still active, slightly vary water usage
                    variation_factor = random.uniform(0.9, 1.1)
                    water_used = event['flow_rate'] * self.sampling_rate * variation_factor

                    device_snapshot = {
                        'device': device_name,
                        'flow_rate': round(event['flow_rate'] * variation_factor, 2),
                        'water_used': round(water_used, 2),
                        'original_event_time': event['time'],
                        'duration': event['duration'],
                        'end_time': event['end_time']
                    }

                    snapshot['active_devices'].append(device_snapshot)
                else:
                    # Remove expired events
                    del ongoing_events[device_name]

            # Process new device activations
            for device in self.devices:
                device_name = device['device']

                # Skip if device is already ongoing
                if device_name in ongoing_events:
                    continue

                # Determine activation probability
                activation_prob = self._get_activation_probability(
                    device,
                    current_hour,
                    device_uses[device_name]
                )

                # Prevent exceeding max uses
                if device_uses[device_name] >= device['max_uses_per_day']:
                    continue

                # Decide if device activates
                if random.random() < activation_prob:
                    # Generate random flow rate and duration
                    flow_rate = random.uniform(device['flow_rate'][0], device['flow_rate'][1])  # in L/min
                    duration = random.uniform(device['typical_duration'][0],
                                              device['typical_duration'][1])  # in minutes

                    # Calculate water usage
                    water_used = flow_rate * duration

                    # Calculate end time
                    start_datetime = datetime.strptime(current_time, "%H:%M")
                    end_datetime = start_datetime + timedelta(minutes=int(duration),
                                                              seconds=int((duration - int(duration)) * 60))
                    end_time = end_datetime.strftime("%H:%M")

                    # Create event entry
                    event = {
                        'time': current_time,
                        'end_time': end_time,
                        'device': device_name,
                        'flow_rate': round(flow_rate, 2),
                        'duration': round(duration, 2),
                        'water_used': round(water_used, 2),
                        'usage_counter': device_uses[device_name]
                    }

                    # Store as an ongoing event
                    ongoing_events[device_name] = event

                    # Add initial device activation to the current snapshot
                    device_snapshot = {
                        'device': device_name,
                        'flow_rate': event['flow_rate'],
                        'water_used': event['water_used'],
                        'original_event_time': event['time'],
                        'duration': event['duration'],
                        'end_time': event['end_time']
                    }
                    snapshot['active_devices'].append(device_snapshot)

                    # Update device uses
                    device_uses[device_name] += 1

            # Always add the snapshot, even if empty
            all_events.append(snapshot)

        return {
            'events': all_events
        }


def main():
    config_file = 'water_config.json'
    simulator = WaterUsageSimulator(config_file)
    results = simulator.simulate()

    with open('water_usage_snapshots.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Simulation complete. Results saved to water_usage_snapshots.json")

    # Optional: Analyze events and water usage
    total_snapshots = len(results['events'])
    snapshots_with_activity = sum(1 for snapshot in results['events'] if snapshot['active_devices'])
    total_water_used = sum(
        sum(device['water_used'] for device in snapshot['active_devices']) for snapshot in results['events'])

    print(f"Total snapshots: {total_snapshots}")
    print(f"Snapshots with activity: {snapshots_with_activity}")
    print(f"Total water used: {total_water_used:.2f} L")


if __name__ == "__main__":
    main()