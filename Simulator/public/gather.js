// Function to collect form data
async function submitForm() {
    const email = document.getElementById('username').value || "";
    console.log('Email from input:', email);

    if (!email) {
        alert('Please enter an email address.');
        return;
    }

    const configData = {
        basic_parameters: {
            name: document.getElementById('house-name').value || "Default House",
            age_options: ["child", "teenager", "adult", "elderly"],
            number_of_people: parseInt(document.getElementById('num-people').value) || 0,
            npc: collectNpcData(),
            rooms: (parseInt(document.getElementById('num-bedrooms').value) || 0) +
                (parseInt(document.getElementById('num-bathrooms').value) || 0) +
                (parseInt(document.getElementById('num-kitchens').value) || 0),
            bathrooms: parseInt(document.getElementById('num-bathrooms').value) || 0,
            kitchen: parseInt(document.getElementById('num-kitchens').value) || 0,
            living_room: 1,
            dining_room: 1,
            garage: 1,
            garden: 1,
            type_of_simulation: {
                type: document.getElementById('simulation-type').value || "fast_forward",
                start_date: document.getElementById('start-date').value || "2021-01-01",
                end_date: document.getElementById('end-date').value || "2021-01-02",
                options: ["real_time", "fast_forward"]
            }
        },
        solar_panels: {
            panel_eff: parseFloat(document.getElementById('panel-efficiency').value) || 0,
            number_of_panels: parseInt(document.getElementById('num-panels').value) || 0,
            size_of_panels_m2: parseFloat(document.getElementById('panel-size').value) || 0
        },
        battery: {
            capacity_ah: parseFloat(document.getElementById('battery-capacity').value) || 0,
            voltage: parseFloat(document.getElementById('battery-voltage').value) || 0,
            initial_state_of_charge_percent: parseFloat(document.getElementById('initial-soc').value) || 0,
            charging_efficiency: parseFloat(document.getElementById('charge-efficiency').value) || 0,
            discharging_efficiency: parseFloat(document.getElementById('discharge-efficiency').value) || 0,
            energy_loss_conversion: parseFloat(document.getElementById('energy-loss').value) || 0,
            degrading_ratio: parseFloat(document.getElementById('degrading-ratio').value) || 0
        },
        water_heating: {
            selected_method: document.getElementById('water-heating-type').value || "electricity",
            options: ["electricity", "natural gas", "propane", "fossil fuel"]
        },
        remvote_connection: {
            inSameComputer: document.getElementById('in-same-computer').checked || false,
            endpoint_to_ddbb: document.getElementById('endpoint-to-db').value || "",
            username: email,
            password: document.getElementById('password').value || "",
            not_local_params: {
                remote_brok_ip: document.getElementById('remote-brok-ip').value || "",
                remote_brok_port: parseInt(document.getElementById('remote-port').value) || 0
            }
        },
        water_devices: collectWaterDevices(),
        electricity_devices: collectElectricityDevices()
    };

    try {
        const response = await window.electronAPI.saveConfig(configData);
        if (response.success) {
            console.log('Config saved at:', response.configFilePath);
            nextScreen();
        } else {
            console.error('Failed to save config:', response.error);
            alert(`Error saving config: ${response.error}`);
        }
    } catch (err) {
        console.error('Error during save-config IPC call:', err);
        alert('An unexpected error occurred while saving the config.');
    }

    try {
        await window.electronAPI.setEmail(email).then((response) => {
            console.log(response); // Logs: "Email set to: user@example.com"
        });
    } catch (err) {
        console.error('Error setting email:', err);
        alert('An unexpected error occurred while setting the email.');
    }
}

// Function to set custom config path
async function submitCustomConfig() {
    const customConfigPath = document.getElementById('custom-config-path').value; // Assume an input field for the path
    try {
        const response = await window.electronAPI.setConfigPath(customConfigPath);
        if (response.success) {
            console.log('Custom config path set to:', response.configPath);
        } else {
            console.error('Failed to set custom config path:', response.error);
            alert(`Error setting custom config path: ${response.error}`);
        }
    } catch (err) {
        console.error('Error during set-config-path IPC call:', err);
        alert('An unexpected error occurred while setting the custom config path.');
    }
}

// Example function to collect dynamic NPC data
function collectNpcData() {
    const npcList = [];
    const npcElements = document.querySelectorAll('.npc-entry'); // Assume NPC entries have this class
    npcElements.forEach(element => {
        const npc = {
            name: element.querySelector('.npc-name').value || "",
            age_group: element.querySelector('.npc-age').value || "",
            out_of_home_periods: []
        };
        const periods = element.querySelectorAll('.out-of-home-period');
        periods.forEach(period => {
            npc.out_of_home_periods.push({
                start: period.querySelector('.start-time').value || "",
                end: period.querySelector('.end-time').value || "",
                reason: period.querySelector('.reason').value || ""
            });
        });
        npcList.push(npc);
    });
    return npcList;
}

// Example function to collect water devices
function collectWaterDevices() {
    const devices = [];
    const deviceElements = document.querySelectorAll('.water-device-entry');
    deviceElements.forEach(element => {
        devices.push({
            device: element.querySelector('.device-type').value || "",
            room: element.querySelector('.device-room').value || "",
            flow_rate_liters_per_minute: parseFloat(element.querySelector('.flow-rate').value) || 0,
            typical_duration: [
                parseFloat(element.querySelector('.duration-min').value) || 0,
                parseFloat(element.querySelector('.duration-max').value) || 0
            ],
            max_uses_per_day: parseInt(element.querySelector('.max-uses').value) || 0,
            usage_patterns: {
                morning: parseFloat(element.querySelector('.pattern-morning').value) || 0,
                midday: parseFloat(element.querySelector('.pattern-midday').value) || 0,
                dinner: parseFloat(element.querySelector('.pattern-dinner').value) || 0,
                evening: parseFloat(element.querySelector('.pattern-evening').value) || 0,
                other: parseFloat(element.querySelector('.pattern-other').value) || 0
            }
        });
    });
    return devices;
}

// Example function to collect electricity devices
function collectElectricityDevices() {
    const devices = [];
    const deviceElements = document.querySelectorAll('.electricity-device-entry');
    deviceElements.forEach(element => {
        devices.push({
            device: element.querySelector('.device-type').value || "",
            room: element.querySelector('.device-room').value || "",
            power_watts: parseFloat(element.querySelector('.power-watts').value) || 0,
            typical_duration: [
                parseFloat(element.querySelector('.duration-min').value) || 0,
                parseFloat(element.querySelector('.duration-max').value) || 0
            ],
            max_uses_per_day: parseInt(element.querySelector('.max-uses').value) || 0,
            usage_patterns: {
                morning: parseFloat(element.querySelector('.pattern-morning').value) || 0,
                midday: parseFloat(element.querySelector('.pattern-midday').value) || 0,
                dinner: parseFloat(element.querySelector('.pattern-dinner').value) || 0,
                evening: parseFloat(element.querySelector('.pattern-evening').value) || 0,
                other: parseFloat(element.querySelector('.pattern-other').value) || 0
            }
        });
    });
    return devices;
}

// Attach the function to a button (example)
document.getElementById('generate-config').addEventListener('click', submitForm);