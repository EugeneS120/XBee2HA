import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, broker, port, topic, on_message):
        self.client = mqtt.Client()
        self.broker = broker
        self.port = port
        self.topic = topic
        self.on_message = on_message
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT broker with result code {rc}")
        client.subscribe(self.topic)

    def connect(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()

    def send_message(self, topic, payload):
        self.client.publish(topic, payload)