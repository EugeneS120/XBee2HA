import logging
import paho.mqtt.client as mqtt

_LOGGER = logging.getLogger(__name__)

class MQTTClient:
    def __init__(self, broker, port, username=None, password=None):
        try:
            # your init
            _LOGGER.warning("MQTTClient initialized")
        except Exception as e:
            _LOGGER.error("MQTTClient __init__ failed: %s", e)
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client = mqtt.Client()
        if self.username:
            self.client.username_pw_set(self.username, self.password)

    def connect(self):
        try:
            self.client.connect(self.broker, self.port)
            _LOGGER.info("Connected to MQTT broker at %s:%s", self.broker, self.port)
        except Exception as e:
            _LOGGER.error("Failed to connect to MQTT broker: %s", e)

    def publish_constant_test(self):
        _LOGGER.warning("Entered publish_constant_test()")
        self.connect()
        self.client.publish("home/sensors/xbee/xbee_status", "TEST: XBEE module online", retain=True)
        self.client.publish("home/sensors/xbee/sample_time", "2025-05-23T20:00:00", retain=True)
        self.client.publish("home/sensors/xbee/dio2_ad2", "1234", retain=True)
        self.client.publish("home/sensors/xbee/dio3_ad3", "HIGH", retain=True)
        _LOGGER.info("Published constant test values to MQTT topics.", retain=True)
        self.client.disconnect()
