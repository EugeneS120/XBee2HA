from .mqtt_client import MQTTClient

def setup(hass, config):
    conf = config.get("xbee_bridge", {})
    broker = conf.get("mqtt_broker", "localhost")
    port = conf.get("mqtt_port", 1883)

    mqtt = MQTTClient(broker, port)
    mqtt.publish_constant_test()
    return True