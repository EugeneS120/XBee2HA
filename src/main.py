from mqtt_client import MQTTClient
from xbee_api.py import XBeeAPI
from xbee_communication import XBeeCommunication

def on_message(client, userdata, msg):
    print(f"Received message on topic {msg.topic}: {msg.payload}")
    command = XBeeAPI.encode_command(msg.payload)
    xbee_comm.send_command(command)
    response = xbee_comm.get_response()
    decoded_response = XBeeAPI.decode_response(response)
    mqtt_client.send_message("response/topic", decoded_response)

# MQTT configuration
broker = "mqtt_broker_address"
port = 1883
topic = "request/topic"

# XBee configuration
xbee_port = "/dev/ttyUSB0"
xbee_baud_rate = 9600

mqtt_client = MQTTClient(broker, port, topic, on_message)
xbee_comm = XBeeCommunication(xbee_port, xbee_baud_rate)

if __name__ == "__main__":
    mqtt_client.connect()
    # Keep the script running
    import time
    while True:
        time.sleep(1)