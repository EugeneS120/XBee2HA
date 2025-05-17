import logging
import paho.mqtt.client as mqtt  # Paho MQTT library

# Logger for Home Assistant
_LOGGER = logging.getLogger(__name__)

class MQTTClient:
    def __init__(self, broker, port, username=None, password=None):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client = mqtt.Client()

        if username and password:
            self.client.username_pw_set(username, password)

    def connect(self):
        """Connect to the MQTT broker."""
        try:
            self.client.connect(self.broker, self.port)
            _LOGGER.info("Connected to MQTT broker at %s:%s", self.broker, self.port)
        except Exception as e:
            _LOGGER.error("Failed to connect to MQTT broker: %s", e)

    def publish(self, topic, payload):
        """Publish a message to the MQTT broker."""
        try:
            self.client.publish(topic, payload, retain=False)
            _LOGGER.debug("Published to %s: %s", topic, payload)
        except Exception as e:
            _LOGGER.error("Failed to publish message: %s", e)

# Example usage (replace with actual parameters)
if __name__ == "__main__":
    mqtt_client = MQTTClient(broker="localhost", port=1883)
    mqtt_client.connect()
    mqtt_client.publish("home/sensors/xbee/xbee_status", "online")