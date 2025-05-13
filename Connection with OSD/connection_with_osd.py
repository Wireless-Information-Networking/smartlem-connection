import json
import time
from azure.iot.device import IoTHubDeviceClient, Message

# Define connection strings for each Raspberry Pi device
# These strings are used to authenticate and connect to the Azure IoT Hub
CONNECTION_STRING_PI_1 = "HostName=ioth-smartlem-poc.azure-devices.net;DeviceId=Dev-Raspberry-Pie-1;SharedAccessKey=3bmfIkSJHwTi/2fTMJX5Gj9RuyOxONWfBCfkuxWgMOs="
CONNECTION_STRING_PI_2 = "HostName=ioth-smartlem-poc.azure-devices.net;DeviceId=Dev-Raspberry-Pie-2;SharedAccessKey=s5dESJ3VwTNDEvuFUEfuox2AnhIeAkM1H1uqD908Kws="

# Define file paths to JSON files containing sensor data for each Raspberry Pi
JSON_FILE_PATH_PI_1 = "sensor_data_rp1.json"
JSON_FILE_PATH_PI_2 = "sensor_data_rp2.json"

def iothub_client_init(connection_string):
    """
    Initialize an IoT Hub client using the provided connection string.
    
    Args:
        connection_string (str): The connection string for the IoT Hub device.
    
    Returns:
        IoTHubDeviceClient: An instance of the IoT Hub client.
    """
    client = IoTHubDeviceClient.create_from_connection_string(connection_string)
    return client

def read_json_as_message(file_path):
    """
    Read JSON data from a file and convert it into a message object for transmission.
    
    Args:
        file_path (str): Path to the JSON file containing sensor data.
    
    Returns:
        Message: A message object containing the JSON data as a string, or None if an error occurs.
    """
    try:
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
            # Convert JSON data to a string and wrap it in a Message object
            message = Message(json.dumps(data))
            return message
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return None

def send_telemetry_data(client, file_path):
    """
    Continuously send telemetry data from a JSON file to the IoT Hub.
    
    Args:
        client (IoTHubDeviceClient): The IoT Hub client used to send messages.
        file_path (str): Path to the JSON file containing sensor data.
    """
    try:
        print("Sending data to IoT Hub, press Ctrl-C to exit")
        while True:
            # Read the JSON file and prepare the message
            message = read_json_as_message(file_path)
            if message:
                print(f"Sending message: {message}")
                client.send_message(message)
                print("Message successfully sent")
            else:
                print("Skipping send due to missing or invalid data.")

            # Exit the loop after one iteration (adjust for continuous sending if needed)
            break  # Replace with time.sleep(3) for periodic sending
    except KeyboardInterrupt:
        print("IoTHubClient stopped")

if __name__ == '__main__':
    # Main entry point of the script
    print("Press Ctrl-C to exit")
    
    # Initialize IoT Hub clients for each Raspberry Pi device
    client_pi1 = iothub_client_init(CONNECTION_STRING_PI_1)
    client_pi2 = iothub_client_init(CONNECTION_STRING_PI_2)
    
    # Start sending telemetry data for Raspberry Pi 1
    print("Sending data for Raspberry Pi 1...")
    send_telemetry_data(client_pi1, JSON_FILE_PATH_PI_1)

    # Uncomment the following lines to send data for Raspberry Pi 2
    # print("Sending data for Raspberry Pi 2...")
    # send_telemetry_data(client_pi2, JSON_FILE_PATH_PI_2)