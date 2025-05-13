# Smartlem Connection

## Overview
The **smartlem-connection** project is designed to facilitate seamless communication and integration between various components of a smart home system. Below is an explanation of its key components: the Simulator, Broker, and the Connection with OSD.

## Simulator
The **Simulator** is responsible for generating and running simulations of a smart home environment. It includes the following features:

- Models energy consumption, water usage, solar energy production, and battery management.
- Supports two modes:
  - **Fast-forward simulations**: Simulates predefined time periods.
- Uses configuration files to define parameters such as:
  - NPC (Non-Player Character) behaviors.
  - Device usage patterns.
  - Environmental factors.

## Broker
The **Broker** serves as the communication hub for the system, enabling data exchange between components. Key functionalities include:

- Utilizes MQTT (Message Queuing Telemetry Transport) for managing connections and data flow.
- Handles tasks such as:
  - Authenticating clients.
  - Processing energy and water consumption data.
  - Managing connected devices.
- Provides a user interface for monitoring and controlling the broker's status.

## Connection with OSD
The **Connection with OSD** module integrates the system with the external DataLake from OSD . Its main features include:

- Sends telemetry data (e.g., sensor readings) from IoT devices to an Azure IoT Hub for processing and analysis.
- Ensures seamless communication between the smart home system and cloud-based services.
