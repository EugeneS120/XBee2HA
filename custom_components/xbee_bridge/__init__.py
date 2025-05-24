import logging

_LOGGER = logging.getLogger(__name__)

from .mqtt_client import MQTTClient

def setup(hass, config):
    _LOGGER.info("XBee Bridge initializing...")
    conf = config.get("xbee_bridge", {})
    broker = conf.get("mqtt_broker", "localhost")
    port = conf.get("mqtt_port", 1883)
    username = conf.get("mqtt_user")
    password = conf.get("mqtt_password")
    mqtt = MQTTClient(broker, port, username, password)
    mqtt.publish_constant_test()

    return True
