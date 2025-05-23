import logging
import paho.mqtt.client as mqtt

_LOGGER = logging.getLogger(__name__)

class MQTTClient:
    def __init__(self, broker, port):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client()

    def connect(self):
        try:
            self.client.connect(self.broker, self.port)
            _LOGGER.info("Connected to MQTT broker at %s:%s", self.broker, self.port)
        except Exception as e:
            _LOGGER.error("Failed to connect to MQTT broker: %s", e)

    def publish_constant_test(self):
        self.connect()
        # Publish constant test values
        self.client.publish("home/sensors/xbee/xbee_status", "TEST: XBEE module online")
        self.client.publish("home/sensors/xbee/sample_time", "2025-05-23T20:00:00")
        self.client.publish("home/sensors/xbee/dio2_ad2", "1234")
        self.client.publish("home/sensors/xbee/dio3_ad3", "HIGH")
        _LOGGER.info("Published constant test values to MQTT topics.")
        # Disconnect for clean exit
        self.client.disconnect()