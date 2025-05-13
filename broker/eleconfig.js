const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { exec } = require('child_process');
const fs = require('fs');
const mqtt = require('mqtt');
const util = require('util');
const execPromise = util.promisify(exec);

// Import custom logging functions
const { API, SUCC, WARN, ERR, SERV } = require('./tmessage');

function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: true,
            enableRemoteModule: false,
            preload: path.join(__dirname, 'preload.js')
        }
    });

    win.loadFile(path.join(__dirname, 'index.html'));
    win.setMenu(null);
}


let user_email = ""
let url_consumption = 'https://sirienergy.uab.cat/add_consumption'
let url_production = 'https://sirienergy.uab.cat/add_production'


async function processData(data) {
    try {
        const parsedData = JSON.parse(data);

        // Extract the hour field from the incoming data
        const dateTime = parsedData.hour; // Example: "2025-04-09 01"
        const [date_str, hour_str] = dateTime.split(' '); // Split into date and hour

        // Handle production data
        if (parsedData.production !== undefined && typeof parsedData.production === 'number') {
            console.log("Production Data:", parsedData.production);

            const payload = {
                user_email: user_email,
                date: date_str,
                hour: hour_str,
                value: parsedData.production
            };

            try {
                const response = await fetch(url_production, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (response.ok) {
                    API(`Production data sent successfully to Sirienergy, ${JSON.stringify(payload)}`);
                } else {
                    WARN(`Failed to send production data: ${response.statusText}`);
                }
            } catch (error) {
                ERR(`Error sending production data: ${error.message}`);
            }
        } else {
            console.warn("Invalid or missing production data.");
        }

        // Handle consumption data
        if (parsedData.consumption !== undefined && typeof parsedData.consumption === 'number') {
            console.log("Consumption Data:", parsedData.consumption);

            const payload = {
                user_email: user_email,
                date: date_str,
                hour: hour_str,
                value: parsedData.consumption
            };

            try {
                const response = await fetch(url_consumption, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (response.ok) {
                    API(`Consumption data sent successfully to Sirienergy: ${JSON.stringify(payload)}`);
                } else {
                    WARN(`Failed to send consumption data: ${response.statusText}`);
                }
            } catch (error) {
                ERR(`Error sending consumption data: ${error.message}`);
            }
        } else {
            console.warn("Invalid or missing consumption data.");
        }
    } catch (error) {
        console.error("Error processing data:", error.message);
    }
}




// --- UI IPC Handlers ---

ipcMain.on('open-terminal', (event) => {
    exec('xterm', (error) => {
        if (error) console.error(`Error opening terminal: ${error.message}`);
    });
});

ipcMain.on('broker-terminal', (event) => {
    exec(`xterm -e "docker exec -it emqx /bin/sh; exec bash"`, (error) => {
        if (error) console.error(`Error opening broker terminal: ${error.message}`);
    });
});

ipcMain.on('request-status', (event) => {
    const command = `docker inspect --format='{{.State.Running}}' emqx`;
    SERV(`Checking broker status: ${command}`);
    exec(command, (error, stdout) => {
        if (error) {
            console.error(`Error checking status: ${error.message}`);
            event.reply('status-response', false);
            return;
        }
        event.reply('status-response', stdout.trim() === 'true');
    });
});

ipcMain.on('shutdown-broker', (event) => {
    exec(`docker stop emqx`, (error) => {
        if (error) console.error(`Error stopping broker: ${error.message}`);
        else SUCC('Broker stopped');
    });
});

ipcMain.on('start-broker', (event) => {
    exec(`docker run --rm -d --name emqx -p 8083:1883 emqx/emqx`, (error) => {
        if (error) console.error(`Error starting broker: ${error.message}`);
        else SUCC('Broker started');
    });
});

ipcMain.on('get-broker-status', (event) => {
    const command = `docker inspect --format='{{.State.Running}}' emqx`;
    SERV(`Checking broker status: ${command}`);
    exec(command, (error, stdout) => {
        if (error) {
            console.error(`Error checking status: ${error.message}`);
            event.reply('get-broker-status-response', false);
            return;
        }
        event.reply('get-broker-status-response', stdout.trim() === 'true');
    });
});

ipcMain.on('restart-broker', (event) => {
    exec(`docker restart emqx`, (error) => {
        if (error) console.error(`Error restarting broker: ${error.message}`);
        else SUCC('Broker restarted');
    });
});

ipcMain.on('get-host-info', (event) => {
    const command = `hostname -I && ip route | awk '/default/ { print $3 }' && cat /etc/os-release | grep "PRETTY_NAME"`;
    SERV(`Fetching host info: ${command}`);
    exec(command, (error, stdout) => {
        if (error) {
            console.error(`Error fetching host info: ${error.message}`);
            event.reply('host-info-response', false);
            return;
        }
        event.reply('host-info-response', stdout);
    });
});

// --- MQTT and Client Management Functions ---

async function kickUser(clientId) {
    try {
        const command = `docker exec emqx ./bin/emqx_ctl clients kick ${clientId}`;
        const { stdout, stderr } = await execPromise(command);
        if (stderr) {
            console.error('Kick error stderr:', stderr);
            return false;
        }
        SUCC(`User ${clientId} kicked successfully: ${stdout}`);
        return true;
    } catch (error) {
        console.error('Kick execution error:', error);
        return false;
    }
}

function addToWhitelist(clientId) {
    const folderPath = path.join(__dirname, 'client_data');
    if (!fs.existsSync(folderPath)) {
        fs.mkdirSync(folderPath, { recursive: true });
        SUCC(`Folder created at ${folderPath}`);
    }
    const filePath = path.join(folderPath, 'whitelist.json');
    let data = { users: {} };
    if (fs.existsSync(filePath)) {
        data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    }
    if (data.users[clientId]) {
        SERV(`User ${clientId} is already in the whitelist`);
    } else {
        data.users[clientId] = { added: new Date().toISOString() };
        fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
        SUCC(`User ${clientId} added to whitelist`);
    }
    return true;
}

function checkWhitelist(clientId) {
    const folderPath = path.join(__dirname, 'client_data');
    const filePath = path.join(folderPath, 'whitelist.json');
    if (!fs.existsSync(filePath)) return false;
    const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    return !!data.users[clientId];
}

function updateConnectedClients(clientId, metadata = null) {
    const folderPath = path.join(__dirname, 'client_data');
    if (!fs.existsSync(folderPath)) {
        fs.mkdirSync(folderPath, { recursive: true });
        SUCC(`Folder created at ${folderPath}`);
    }
    const connectedFilePath = path.join(folderPath, 'connected.json');
    let data = { clients: {} };
    if (fs.existsSync(connectedFilePath)) {
        data = JSON.parse(fs.readFileSync(connectedFilePath, 'utf-8'));
    }
    if (metadata) {
        data.clients[metadata.name] = { id: clientId, timestamp: metadata.timestamp };
        SUCC(`Updated connected clients: ${metadata.name} (ID: ${clientId})`);
    }
    fs.writeFileSync(connectedFilePath, JSON.stringify(data, null, 2));
}

// --- MQTT Server Logic ---

const PORT = 8083;

exec("hostname -I | awk '{print $1}'", (error, stdout) => {
    if (error) {
        console.error(`Error fetching host IP: ${error.message}`);
        return;
    }

    const hostIP = stdout.trim();
    SERV(`Host IP: ${hostIP}`);
    SERV(`Host port: ${PORT}`);

    const client = mqtt.connect(`mqtt://${hostIP}:${PORT}`, { clientId: 'server' });

    client.on('connect', () => {
        SUCC('Connected to broker');
        client.subscribe(['connection/inirequest', 'connection/challenge/#', 'client/#'], (err) => {
            if (err) console.error('Subscription error:', err);
            else SUCC('Subscribed to topics: connection/inirequest, connection/challenge/#, client/#');
        });
    });

    client.on('message', (topic, message) => {
        const msgStr = message.toString();
        SERV(`Message received on ${topic}: ${msgStr}`);

        if (topic === 'connection/inirequest') {
            const clientId = msgStr;
            addToWhitelist(clientId);
            client.publish(`connection/challenge/${clientId}`, 'authenticated');
            SERV(`Client ${clientId} authenticated`);
        } else if (topic.startsWith('client/')) {
            const [_, clientId, action] = topic.split('/');
            if (!checkWhitelist(clientId)) {
                WARN(`User ${clientId} not in whitelist, kicking...`);
                kickUser(clientId);
                return;
            }

            const folderPath = path.join(__dirname, 'client_data');
            if (!fs.existsSync(folderPath)) {
                fs.mkdirSync(folderPath, { recursive: true });
                SUCC(`Folder created at ${folderPath}`);
            }

            switch (action) {
                case 'addwhitelist':
                    addToWhitelist(clientId);
                    break;
                case 'energy_data': {
                    processData(msgStr);
                    SUCC(`Energy data from ${clientId} processed successfully`);
                    break;
                }
                case 'modelMTDT': {
                    const metadata = JSON.parse(msgStr);
                    updateConnectedClients(clientId, metadata);
                    SUCC(`Metadata received: ${metadata.name}, ${metadata.timestamp}`);
                    break;
                }
                case 'disconnect': {
                    const connectedFilePath = path.join(folderPath, 'connected.json');
                    if (fs.existsSync(connectedFilePath)) {
                        const data = JSON.parse(fs.readFileSync(connectedFilePath, 'utf-8'));
                        if (data.clients[msgStr]) {
                            delete data.clients[msgStr];
                            fs.writeFileSync(connectedFilePath, JSON.stringify(data, null, 2));
                            SUCC(`Client ${msgStr} disconnected and removed`);
                        }
                    }
                    break;
                }
                case 'email': {
                    const email = msgStr;
                    user_email = email;
                    SUCC(`User email updated to ${user_email}`);
                    break;
                }
            }
        }
    });

    client.on('error', (err) => WARN(`Broker error: ${err}`));
    client.on('disconnect', () => WARN('Disconnected from broker'));
});

// --- App Process ---

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
});