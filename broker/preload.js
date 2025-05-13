const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
    ipcRenderer: {
        send: (channel, data) => ipcRenderer.send(channel, data), //General channel for sending messages
        receive: (channel, func) => ipcRenderer.on(channel, (event, ...args) => func(...args)), //General channel for receiving messages
        invoke: (channel, data) => ipcRenderer.invoke(channel, data), //General channel for invoking messages

        requestStatus: () => ipcRenderer.send('request-status'), // Predefined channel for requesting status of the broker
        selectFile: () => ipcRenderer.invoke('select-file'), // Predefined channel for selecting a file
        addMetadata: (id, modelPath, lastPull, createdDate) => 
            ipcRenderer.invoke('add-metadata', id, modelPath, lastPull, createdDate) // Expose add-metadata
    }
});
