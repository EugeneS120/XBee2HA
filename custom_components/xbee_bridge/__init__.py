import logging
from homeassistant.helpers import discovery

DOMAIN = "xbee_bridge"
_LOGGER = logging.getLogger(__name__)

def setup(hass, config):
    """Set up the XBee Bridge component."""
    mqtt_broker = config[DOMAIN].get("mqtt_broker")
    mqtt_port = config[DOMAIN].get("mqtt_port")
    request_topic = config[DOMAIN].get("request_topic")
    response_topic = config[DOMAIN].get("response_topic")
    xbee_port = config[DOMAIN].get("xbee_port")
    xbee_baud_rate = config[DOMAIN].get("xbee_baud_rate")

    hass.data[DOMAIN] = {
        "mqtt_broker": mqtt_broker,
        "mqtt_port": mqtt_port,
        "request_topic": request_topic,
        "response_topic": response_topic,
        "xbee_port": xbee_port,
        "xbee_baud_rate": xbee_baud_rate,
    }

    discovery.load_platform(hass, "sensor", DOMAIN, {}, config)

    return True