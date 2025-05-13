import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict

def analyze_simulation(json_data):
    # Parse JSON if it's a string; otherwise, assume it's already a dict
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data
    
    actions = data["actions"]
    
    # **Step 1: Parse Timestamps**
    # Handle timestamps crossing midnight by tracking date changes
    prev_time = None
    date = datetime(2021, 1, 1)
    for action in actions:
        time_str = action["timestamp"]
        current_time = datetime.strptime(time_str, "%H:%M:%S").time()
        if prev_time and (current_time.hour * 3600 + current_time.minute * 60 + current_time.second) < \
                         (prev_time.hour * 3600 + prev_time.minute * 60 + prev_time.second):
            date += timedelta(days=1)
        action_dt = datetime.combine(date, current_time)
        action["start_dt"] = action_dt
        action["end_dt"] = action_dt + timedelta(seconds=action["duration"])
        prev_time = current_time
    
    # **Check 1: Device Usage Overlaps**
    device_usage = {}
    for action in actions:
        device = action["device_used"]
        if device and device != "NAN":
            if device not in device_usage:
                device_usage[device] = []
            device_usage[device].append((action["start_dt"], action["end_dt"], action["npc"]))

    overlap_issues = []
    for device, intervals in device_usage.items():
        intervals.sort(key=lambda x: x[0])  # Sort by start time
        for i in range(1, len(intervals)):
            if intervals[i-1][1] > intervals[i][0]:  # Previous end > Current start
                overlap_issues.append(
                    f"Device '{device}' overlap: {intervals[i-1][2]} used it from {intervals[i-1][0]} to {intervals[i-1][1]}, "
                    f"while {intervals[i][2]} started at {intervals[i][0]}"
                )
    
    # **Check 2: Out-of-Home Periods**
    npc_actions = {}
    for action in actions:
        npc = action["npc"]
        if npc not in npc_actions:
            npc_actions[npc] = []
        npc_actions[npc].append(action)
    
    out_of_home_issues = []
    for npc, npc_acts in npc_actions.items():
        npc_acts.sort(key=lambda x: x["start_dt"])
        out_periods = []
        current_period = None
        for action in npc_acts:
            if action["action"] in ["Work", "School", "Gym"]:  # Assuming "Gym" is also out-of-home
                if current_period is None:
                    current_period = [action["start_dt"], action["start_dt"]]
                else:
                    expected_next = current_period[1] + timedelta(minutes=5)
                    if abs((action["start_dt"] - expected_next).total_seconds()) <= 60:  # Allow 1-minute flexibility
                        current_period[1] = action["start_dt"]
                    else:
                        out_periods.append(current_period)
                        current_period = [action["start_dt"], action["start_dt"]]
            else:
                if current_period:
                    out_periods.append(current_period)
                    current_period = None
        if current_period:
            out_periods.append(current_period)
        
        for period in out_periods:
            start, end = period
            for action in npc_acts:
                if action["action"] not in ["Work", "School", "Gym"] and \
                   start <= action["start_dt"] <= end:
                    out_of_home_issues.append(
                        f"{npc} performed '{action['action']}' at {action['start_dt']} during out-of-home period {start} to {end}"
                    )
    
    # **Check 3: Resource Usage Consistency**
    total_energy_calc = sum(action["energy_used"] for action in actions)
    total_water_calc = sum(action["water_used"] for action in actions)
    energy_issue = abs(total_energy_calc - data["total_energy_used"]) > 1e-6
    water_issue = abs(total_water_calc - data["total_water_used"]) > 1e-6
    resource_issues = []
    if energy_issue:
        resource_issues.append(f"Energy mismatch: Calculated {total_energy_calc}, Reported {data['total_energy_used']}")
    if water_issue:
        resource_issues.append(f"Water mismatch: Calculated {total_water_calc}, Reported {data['total_water_used']}")
    
    # **Check 4: Action Duration Reasonableness**
    duration_issues = []
    for action in actions:
        if action["duration"] < 0:
            duration_issues.append(f"{action['npc']} '{action['action']}' has negative duration: {action['duration']}s")
        elif action["duration"] > 3600 and action["action"] not in ["watch_tv", "nap_sleep"]:  # Allow longer for specific actions
            duration_issues.append(f"{action['npc']} '{action['action']}' has long duration: {action['duration']}s")
    
    # **Check 5: Appropriate Resource Usage for NPCs**
    
    # Read the config.json file to get the npcs and their age groups
    with open("config.json", "r") as f:
        data = json.load(f)
    
    num_npcs = data["basic_parameters"]["number_of_people"]
    age_groups = []
    
    #Get list of age groups for each npc
    for i in range(num_npcs):
        age_group = data["basic_parameters"]["npc"][i]["age_group"]
        age_groups.append(age_group)
    
    # Define baseline usage ranges per person per day
    baseline_energy_per_day = {
        "child": {"min": 2.0, "max": 3.5},     # kWh per day
        "teenager": {"min": 3.5, "max": 5.0},  # kWh per day
        "adult": {"min": 4.0, "max": 6.0},     # kWh per day
        "elderly": {"min": 3.0, "max": 4.5}    # kWh per day
    }
    
    baseline_water_per_day = {
        "child": {"min": 50, "max": 100},      # Liters per day
        "teenager": {"min": 80, "max": 150},   # Liters per day
        "adult": {"min": 80, "max": 150},      # Liters per day
        "elderly": {"min": 70, "max": 120}     # Liters per day
    }
    
    # Calculate expected ranges
    expected_energy_min = sum(baseline_energy_per_day.get(age, baseline_energy_per_day["adult"])["min"] for age in age_groups)
    expected_energy_max = sum(baseline_energy_per_day.get(age, baseline_energy_per_day["adult"])["max"] for age in age_groups)
    
    expected_water_min = sum(baseline_water_per_day.get(age, baseline_water_per_day["adult"])["min"] for age in age_groups)
    expected_water_max = sum(baseline_water_per_day.get(age, baseline_water_per_day["adult"])["max"] for age in age_groups)
    
    # Determine simulation duration in days
    if actions:
        start_date = min(action["start_dt"] for action in actions)
        end_date = max(action["end_dt"] for action in actions)
        simulation_days = (end_date - start_date).total_seconds() / (24 * 3600)
        if simulation_days < 0.5:  # If less than 12 hours, assume at least half a day
            simulation_days = 0.5
    else:
        simulation_days = 1.0  # Default to 1 day if no actions
    
    # Adjust expected ranges for simulation duration
    expected_energy_min *= simulation_days
    expected_energy_max *= simulation_days
    expected_water_min *= simulation_days
    expected_water_max *= simulation_days
    
    # Check if actual usage is within expected ranges
    resource_appropriateness_issues = []
    if total_energy_calc < expected_energy_min * 0.7:  # Allow 30% below minimum
        resource_appropriateness_issues.append(
            f"\033[91mEnergy usage too low:\033[0m {total_energy_calc:.2f} kWh (expected min: {expected_energy_min:.2f} kWh for {num_npcs} people)"
        )
    elif total_energy_calc > expected_energy_max * 1.3:  # Allow 30% above maximum
        resource_appropriateness_issues.append(
            f"\033[91mEnergy usage too high:\033[0m {total_energy_calc:.2f} kWh (expected max: {expected_energy_max:.2f} kWh for {num_npcs} people)"
        )
    
    if total_water_calc < expected_water_min * 0.7:  # Allow 30% below minimum
        resource_appropriateness_issues.append(
            f"\033[91mWater usage too low:\033[0m {total_water_calc:.2f} L (expected min: {expected_water_min:.2f} L for {num_npcs} people)"
        )
    elif total_water_calc > expected_water_max * 1.3:  # Allow 30% above maximum
        resource_appropriateness_issues.append(
            f"\033[91mWater usage too high:\033[0m {total_water_calc:.2f} L (expected max: {expected_water_max:.2f} L for {num_npcs} people)"
        )
    # **New Feature: Action Counts and Resource Usage Statistics**
    # Count actions and track resource usage by action type and NPC
    action_counts = Counter()
    action_duration = defaultdict(float)
    action_energy = defaultdict(float)
    action_water = defaultdict(float)
    npc_action_counts = defaultdict(Counter)
    npc_energy_usage = defaultdict(float)
    npc_water_usage = defaultdict(float)
    device_usage_counts = defaultdict(int)
    device_energy_usage = defaultdict(float)
    device_water_usage = defaultdict(float)
    
    for action in actions:
        action_type = action["action"]
        npc = action["npc"]
        device = action["device_used"] if action["device_used"] != "NAN" else "none"
        energy = action["energy_used"]
        water = action["water_used"]
        duration = action["duration"]
        
        # Update counts and sums
        action_counts[action_type] += 1
        action_duration[action_type] += duration
        action_energy[action_type] += energy
        action_water[action_type] += water
        npc_action_counts[npc][action_type] += 1
        npc_energy_usage[npc] += energy
        npc_water_usage[npc] += water
        if device != "none":
            device_usage_counts[device] += 1
            device_energy_usage[device] += energy
            device_water_usage[device] += water
    
    # Calculate total time spent on each action
    action_time_hours = {action: duration / 3600 for action, duration in action_duration.items()}
    
    # Calculate average resource usage per action
    avg_energy_per_action = {action: energy / count for action, energy, count in 
                            [(a, e, c) for a, e, c in zip(action_energy.keys(), action_energy.values(), action_counts.values())]}
    avg_water_per_action = {action: water / count for action, water, count in 
                           [(a, w, c) for a, w, c in zip(action_water.keys(), action_water.values(), action_counts.values())]}
    
    # **Summary Report**
    print("\033[1m### Simulation Analysis Report ###\033[0m")
    print("\n - 1. Device Usage Overlaps - ")
    if overlap_issues:
        print("\033[93mIssues found:\033[0m")
        for issue in overlap_issues:
            print(f"- {issue}")
    else:
        print("\033[92mNo overlaps detected - Makes sense!\033[0m")

    print("\n - 2. Out-of-Home Periods - ")
    if out_of_home_issues:
        print("\033[93mIssues found:\033[0m")
        for issue in out_of_home_issues:
            print(f"- {issue}")
    else:
        print("\033[92mNo home actions during out periods - Makes sense!\033[0m")

    print("\n - 3. Resource Usage Consistency - ")
    if resource_issues:
        print("\033[93mIssues found:\033[0m")
        for issue in resource_issues:
            print(f"- {issue}")
    else:
        print("\033[92mTotals match - Makes sense!\033[0m")

    print("\n - 4. Action Durations - ")
    if duration_issues:
        print("\033[93mIssues found:\033[0m")
        for issue in duration_issues:
            print(f"- {issue}")
    else:
        print("\033[92mAll durations reasonable - Makes sense!\033[0m")
    
    print("\n - 5. Resource Usage Appropriateness - ")
    if resource_appropriateness_issues:
        print("\033[93mIssues found:\033[0m")
        for issue in resource_appropriateness_issues:
            print(f"- {issue}")
    else:
        print("\033[92mResource usage appropriate for household composition - Makes sense!\033[0m")
    
    print("\n - 6. Action Statistics - ")
    print(f"\033[1mTotal actions:\033[0m {sum(action_counts.values())}")
    print(f"\033[1mTotal energy used:\033[0m {total_energy_calc:.2f} kWh")
    print(f"\033[1mTotal water used:\033[0m {total_water_calc:.2f} L")
    print(f"\033[1mSimulation duration:\033[0m {simulation_days:.2f} days")
    
    print("\n   6.1 Most Frequent Actions:")
    for action, count in action_counts.most_common(5):
        print(f"   - {action}: {count} times")
    
    print("\n   6.2 Action Resource Usage:")
    print("   | Action Type | Count | Total Duration (h) | Energy (kWh) | Water (L) | Energy/Action | Water/Action |")
    print("   |-------------|-------|-------------------|--------------|-----------|---------------|-------------|")
    for action in sorted(action_counts.keys()):
        count = action_counts[action]
        duration = action_time_hours[action]
        energy = action_energy[action]
        water = action_water[action]
        avg_energy = avg_energy_per_action[action]
        avg_water = avg_water_per_action[action]
        print(f"   | \033[94m{action:<11}\033[0m | \033[92m{count:5d}\033[0m | \033[93m{duration:17.2f}\033[0m | \033[91m{energy:12.2f}\033[0m | \033[96m{water:9.2f}\033[0m | \033[95m{avg_energy:13.2f}\033[0m | \033[97m{avg_water:11.2f}\033[0m |")
    
    print("\n   6.3 NPC Resource Usage:")
    print("   | NPC | Total Actions | Energy Used (kWh) | Water Used (L) | Most Common Action |")
    print("   |-----|---------------|------------------|---------------|-------------------|")
    for npc in sorted(npc_action_counts.keys()):
        total_actions = sum(npc_action_counts[npc].values())
        most_common = npc_action_counts[npc].most_common(1)[0] if npc_action_counts[npc] else ("none", 0)
        print(f"   | \033[94m{npc:<3}\033[0m | \033[92m{total_actions:13d}\033[0m | \033[91m{npc_energy_usage[npc]:16.2f}\033[0m | \033[96m{npc_water_usage[npc]:13.2f}\033[0m | \033[93m{most_common[0]} ({most_common[1]} times)\033[0m |")
    
    print("\n   6.4 Device Usage Statistics:")
    print("   | Device | Times Used | Energy Used (kWh) | Water Used (L) |")
    print("   |--------|------------|------------------|---------------|")
    for device in sorted(device_usage_counts.keys(), key=lambda x: (x is None, x)):
        device_name = device if device is not None else "none"
        print(f"   | \033[94m{device_name:<6}\033[0m | \033[92m{device_usage_counts[device]:10d}\033[0m | \033[91m{device_energy_usage[device]:16.2f}\033[0m | \033[96m{device_water_usage[device]:13.2f}\033[0m |")
    
    print("\n ---  Final Verdict  --- ")
    if not (overlap_issues or out_of_home_issues or resource_issues or duration_issues or resource_appropriateness_issues):
        print("\033[92mAll checks passed - Simulation makes sense!\033[0m")
    else:
        print("\033[91mIssues detected - Review the details above.\033[0m")

if __name__ == "__main__":
    
    with open("./results/user_data.json", "r") as f:
        json_data = json.load(f)
    analyze_simulation(json_data)