const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs').promises;
const { exec, spawn } = require('child_process');
const chokidar = require('chokidar');
const mqtt = require('mqtt');

let win; // Form window
let hostmodelWin; // Dashboard window
let hostID = ""; // Global variable for house ID
let clientID = ""; // Use clientID directly instead of houseID
let email = ""; // Email of the user
let outputDir = path.join(__dirname, 'sim_result');
let outputFile = "";
let client; // MQTT client

function createWindow() {
  win = new BrowserWindow({
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });
  win.loadFile('public/index.html');
  win.setMenuBarVisibility(false);
  win.setAutoHideMenuBar(true);
  win.maximize();
  // win.webContents.openDevTools(); // Uncomment for debugging
}

function createHostModelWindow(simulationData) {
  hostmodelWin = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });
  hostmodelWin.loadFile('public/host_model.html');
  hostmodelWin.setMenuBarVisibility(false);
  hostmodelWin.setAutoHideMenuBar(true);
  hostmodelWin.maximize();
  // hostmodelWin.webContents.openDevTools(); // Uncomment for debugging

  hostmodelWin.webContents.on('did-finish-load', () => {
    hostmodelWin.webContents.send('simulation-data', { simulationData, houseID: hostID });
  });

  hostmodelWin.on('closed', () => {
    hostmodelWin = null;
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// Load config and initialize MQTT after email is set
async function initializeMQTT() {
  await loadConfig();
  if (email && clientID) {
    initMQTTClient(brokerURL, clientID, email);
  } else {
    console.log('Waiting for email and clientID to initialize MQTT...');
  }
}

//With custom config file
ipcMain.handle('save-config', async (event, configData) => {
  try {
    const houseName = (configData.basic_parameters.name || 'config').trim();
    hostID = houseName;
    clientID = houseName; // Set clientID
    const fileName = houseName.toLowerCase().replace(/\s+/g, '_') + '.json';
    const saveDir = path.join(__dirname, 'config_files');
    await fs.mkdir(saveDir, { recursive: true });
    const configFilePath = path.join(saveDir, fileName);
    await fs.writeFile(configFilePath, JSON.stringify(configData, null, 4), 'utf8');
    console.log('Config file saved at:', configFilePath);

    outputFile = path.join(outputDir, `${houseName.toLowerCase().replace(/\s+/g, '_')}_output.json`);

    // Initialize MQTT after config is saved and email is set
    if (email && clientID) {
      initMQTTClient(brokerURL, clientID, email);
    } else {
      console.log('Waiting for email to initialize MQTT...');
    }

    return { success: true, configFilePath };
  } catch (err) {
    console.error('Error in save-config:', err);
    return { success: false, error: err.message };
  }
});

//Default simulation
ipcMain.on('run-default-simulation', (event) => {
  const venvPython = path.join(__dirname, '.venv', 'bin', 'python3');
  const scriptPath = path.join(__dirname, 'mpsds_generate_simulation', 'puppeteer.py');
  const defaultConfigFile = path.join(__dirname, 'mpsds_generate_simulation', 'config_default.json');
  const command = `${venvPython} "${scriptPath}" "${defaultConfigFile}"`;

  fs.readFile(defaultConfigFile, 'utf-8')
    .then((data) => {
      const defaultConfig = JSON.parse(data);
      const typeOfSimulation = defaultConfig.basic_parameters.type_of_simulation.type;
      console.log('Type of simulation for default config:', typeOfSimulation);

      if (typeOfSimulation === 'fast_forward') {
        exec(command, (error, stdout, stderr) => {
          if (error) {
            console.error('Error running default simulation:', error);
            win.webContents.send('simulation-error', error.message);
            return;
          }
          console.log('Default simulation output:', stdout);
          if (stderr) console.error('Default simulation stderr:', stderr);

          const outputFile = path.join(__dirname, 'sim_result', "john_doe's_smart_house_output.json");
          fs.access(outputFile, fs.constants.F_OK)
            .then(async () => {
              console.log('Default output file found:', outputFile);
              try {
                const data = await fs.readFile(outputFile, 'utf-8');
                const parsedData = JSON.parse(data);
                win.webContents.send('simulation-complete', { filePath: outputFile, data: parsedData, houseID: "john_doe's_smart_house" });
                createHostModelWindow(parsedData);
                win.close();
              } catch (err) {
                console.error('Error reading default output file:', err);
                win.webContents.send('simulation-error', 'Failed to read default output file');
              }
            })
            .catch(() => {
              console.error('Default output file not found:', outputFile);
              win.webContents.send('simulation-error', 'Default output file not found');
            });
        });
      } else if (typeOfSimulation === 'real_time') {
        console.log('Starting real-time simulation with command:', command);

        outputFile = path.join(__dirname, 'sim_result', "john_doe's_smart_house_output.json");

        console.log('About to spawn Python process...');
        const pythonProcess = spawn(venvPython, [scriptPath, defaultConfigFile]);

        console.log('Spawning Python process with command:', `${venvPython} ${scriptPath} ${defaultConfigFile}`);
        console.log('Python process started with PID:', pythonProcess.pid);

        pythonProcess.stdout.on('data', (data) => {
          console.log(`Python stdout: ${data.toString()}`);
        });

        pythonProcess.stderr.on('data', (data) => {
          console.error(`Python stderr: ${data.toString()}`);
        });

        pythonProcess.on('error', (error) => {
          console.error('Failed to start Python process:', error);
        });

        pythonProcess.on('close', (code) => {
          console.log(`Python process exited with code ${code}`);
        });

        pythonProcess.unref();

        // Ensure the output directory exists
        fs.mkdir(outputDir, { recursive: true })
          .then(() => {
            console.log('Output directory ensured:', outputDir);

            // Start watching the file
            const watcher = chokidar.watch(outputFile, {
              persistent: true,
              awaitWriteFinish: { stabilityThreshold: 2000, pollInterval: 100 },
            });

            console.log('Watching file:', outputFile);

            watcher.on('ready', () => {
              console.log('Watcher is ready and monitoring');
            });

            watcher.on('add', (path) => {
              console.log(`File added: ${path}`);
            });

            watcher.on('change', (path) => {
              console.log(`File changed: ${path}`);
              fs.readFile(outputFile, 'utf-8', (err, data) => {
                if (err) {
                  console.error('Error reading output file:', err);
                  return;
                }
                try {
                  const parsedData = JSON.parse(data);
                  console.log('Real-time output file updated:', parsedData);
                  win.webContents.send('simulation-update', { filePath: outputFile, data: parsedData, houseID: "john_doe's_smart_house" });
                } catch (parseErr) {
                  console.error('Error parsing output file:', parseErr);
                }
              });
            });

            watcher.on('error', (error) => {
              console.error('Watcher error:', error);
            });

            // Periodic read every 5 seconds with error handling
            console.log('Starting periodic read every 4 minutes');
            const readInterval = setInterval(async () => {
              try {
                const exists = await fs.access(outputFile, fs.constants.F_OK).then(() => true).catch(() => false);
                if (exists) {
                  const data = await fs.readFile(outputFile, 'utf-8');
                  const parsedData = JSON.parse(data);
                  console.log('Periodic read of output file:', parsedData);

                  //Process and send the data to broker
                  processNewDataPoint(parsedData);
                } else {
                  console.log('Periodic read: Output file does not exist yet');
                }
              } catch (err) {
                console.error('Periodic read error:', err.message);
              }
            }, 240000); //Check every 4 minutes


            // Cleanup
            win.on('closed', () => {
              watcher.close();
              clearInterval(readInterval);
              console.log('File watcher and interval cleared');
            });

            win.on('close', () => {
              if (pythonProcess && !pythonProcess.killed) {
                pythonProcess.kill('SIGTERM');
                console.log('Real-time simulation process terminated');
              }
              if (client) {
                client.end();
                console.log('MQTT client disconnected');
              }
            });
          })
          .catch((err) => {
            console.error('Error creating output directory:', err);
          });
      }
    })
    .catch((err) => {
      console.error('Error reading default config file:', err);
      win.webContents.send('simulation-error', 'Failed to read default config file');
    });
});

ipcMain.handle('load-sim-data', async (event, houseID) => {
  try {
    const filePath = path.join(__dirname, 'sim_result', `${houseID}_output.json`);
    const data = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Error reading simulation data:', error);
    return [];
  }
});

/****************************************************************** IPC to get the variables I need ***************************************************************/

let configPath = path.join(__dirname, 'mpsds_generate_simulation', 'config_default.json'); // Default path

// Handle custom config file path sent from renderer
ipcMain.handle('set-config-path', async (event, customPath) => {
    try {
        if (customPath) {
            configPath = customPath;
            console.log(`Config path updated to: ${configPath}`);
            await loadConfig(); // Reload the configuration with the new path
            return { success: true, configPath };
        } else {
            throw new Error('Invalid custom path');
        }
    } catch (err) {
        console.error('Error setting custom config path:', err);
        return { success: false, error: err.message };
    }
});

const configPathDefault = path.join(__dirname, 'mpsds_generate_simulation', 'config_default.json');

let brokIP = "";
let port = "";
let brokerURL = "";

async function loadConfig() {
    try {
        const configData = JSON.parse(await fs.readFile(configPath, 'utf-8'));
        brokIP = configData.remote_connection.not_local_params.remote_brok_ip || "127.0.0.1";
        port = configData.remote_connection.not_local_params.remote_brok_port || "1883";
        brokerURL = `mqtt://${brokIP}:${port}`;
        console.log(`Broker URL set to: ${brokerURL}`);
    } catch (err) {
        console.error('Error loading config file:', err);
    }
}

// Call this function when the app starts
loadConfig();

const topic = `client/${clientID}/energy_data`; // Topic in the broker on how to publish the data

// Module-level variables
let hourlyData = {}; // Holds sums and counts for each hour
let lastHour = null; // Tracks the previous hour processed

// Handle broker URL sent from renderer
ipcMain.handle('set-broker-url', async (event, url) => {
  brokIP = url;
  return `OK to: ${brokIP}`;
});

// Handle email sent from renderer
ipcMain.handle('set-email', async (event, userEmail) => {
  email = userEmail;
  console.log(`Email set to: ${email}`);
  if (clientID && !client) { // Only initialize if clientID is set and client isn’t already initialized
    initMQTTClient(brokerURL, clientID, email);
  }
  return `OK to: ${email}`;
});

// Handle port sent from renderer
ipcMain.handle('set-port', async (event, userPort) => {
  port = userPort;
  return `OK to: ${port}`;
});

/****************************************************************** API connection  ***************************************************************/

// Function to initialize the MQTT client
function initMQTTClient(brokerURL, clientID, email) {
  client = mqtt.connect(brokerURL, { clientId: clientID });

  client.on('connect', () => {
      console.log('Connected to broker');

      // Send clientID for authentication
      client.publish('connection/inirequest', clientID, (err) => {
          if (err) {
              console.error('Error sending connection request:', err);
          } else {
              console.log(`Sent clientID to connection/inirequest: ${clientID}`);
          }
      });

      // Send email
      client.publish(`client/${clientID}/email`, email, (err) => {
          if (err) {
              console.error('Error sending email:', err);
          } else {
              console.log(`Sent email to client/${clientID}/email: ${email}`);
          }
      });
  });

  client.on('error', (err) => {
      console.error('Connection error:', err);
  });

  client.on('close', () => {
      console.log('Disconnected from broker');
  });
}

// Function to calculate total device consumption for a data point
function calculateDeviceConsumption(dataPoint) {
  const deviceConsumption = dataPoint.energy_management_sensors.energy_efficiency.device_consumption;
  return Object.values(deviceConsumption).reduce((sum, value) => sum + value, 0);
}

// Function to process a new external data point
function processNewDataPoint(data) {
  if (!data || !Array.isArray(data) || !data[0] || !data[0].timestamp || !data[0].energy_management_sensors) {
    console.error('Invalid data format in processNewDataPoint:', data);
    return;
  }

  const dataPoint = data[0]; // Use the first (most recent) data point
  const hour = dataPoint.timestamp.substring(0, 13);

  // Check if we've moved to a new hour
  if (lastHour !== null && hour !== lastHour) {
    if (hourlyData[lastHour] && hourlyData[lastHour].count > 0) {
      const productionAvg = hourlyData[lastHour].productionSum / hourlyData[lastHour].count;
      const consumptionAvg = hourlyData[lastHour].consumptionSum / hourlyData[lastHour].count;
      const message = JSON.stringify({
        hour: lastHour,
        production: productionAvg,
        consumption: consumptionAvg
      });
      client.publish(topic, message, (err) => {
        if (err) {
          console.error(`Error publishing to ${topic}:`, err);
        } else {
          console.log(`Published to ${topic}: ${message}`);
        }
      });
      delete hourlyData[lastHour];
    }
  }

  lastHour = hour;

  if (!hourlyData[hour]) {
    hourlyData[hour] = { productionSum: 0, consumptionSum: 0, count: 0 };
  }

  const production = dataPoint.energy_management_sensors.solar_power.production;
  const consumption = calculateDeviceConsumption(dataPoint);

  hourlyData[hour].productionSum += production;
  hourlyData[hour].consumptionSum += consumption;
  hourlyData[hour].count += 1;

  // Initialize MQTT client only if not already connected
  if (!client || !client.connected) {
    initMQTTClient(brokerURL, clientID, email);
  }
}

// Call this whenever you update your data point variable:
//processNewDataPoint(exampleDataPoint);