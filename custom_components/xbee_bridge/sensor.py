import logging
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

from .mqtt_client import MQTTClient
from .xbee_api import XBeeAPI
from .xbee_communication import XBeeCommunication

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "XBee Sensor"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the XBee sensor platform."""
    name = config.get(CONF_NAME)
    mqtt_broker = hass.data["xbee_bridge"]["mqtt_broker"]
    mqtt_port = hass.data["xbee_bridge"]["mqtt_port"]
    request_topic = hass.data["xbee_bridge"]["request_topic"]
    response_topic = hass.data["xbee_bridge"]["response_topic"]
    xbee_port = hass.data["xbee_bridge"]["xbee_port"]
    xbee_baud_rate = hass.data["xbee_bridge"]["xbee_baud_rate"]

    xbee_comm = XBeeCommunication(xbee_port, xbee_baud_rate)
    mqtt_client = MQTTClient(mqtt_broker, mqtt_port, request_topic, response_topic, lambda client, userdata, msg: handle_message(client, userdata, msg, xbee_comm))

    add_entities([XBeeSensor(name, mqtt_client, xbee_comm)], True)

def handle_message(client, userdata, msg, xbee_comm):
    _LOGGER.info(f"Received message on topic {msg.topic}: {msg.payload}")
    command = XBeeAPI.encode_command(msg.payload)
    xbee_comm.send_command(command)
    response = xbee_comm.get_response()
    decoded_response = XBeeAPI.decode_response(response)
    client.publish(decoded_response)

class XBeeSensor(Entity):
    """Representation of an XBee sensor."""

    def __init__(self, name, mqtt_client, xbee_comm):
        """Initialize the sensor."""
        self._name = name
        self._state = None
        self._mqtt_client = mqtt_client
        self._xbee_comm = xbee_comm
        self._mqtt_client.connect()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self):
        """Fetch new state data for the sensor."""
        response = self._xbee_comm.get_response()
        self._state = XBeeAPI.decode_response(response)