import paho.mqtt.client as mqtt
import logging

_LOGGER = logging.getLogger(__name__)

class MQTTClient:
    def __init__(self, broker, port, request_topic, response_topic, on_message):
        self.client = mqtt.Client()
        self.broker = broker
        self.port = port
        self.request_topic = request_topic
        self.response_topic = response_topic
        self.on_message = on_message
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        _LOGGER.info(f"Connected to MQTT broker with result code {rc}")
        client.subscribe(self.request_topic)

    def connect(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

    def send_message(self, payload):
        self.client.publish(self.response_topic, payload)