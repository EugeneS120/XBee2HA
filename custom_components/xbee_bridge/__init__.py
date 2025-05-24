import logging
from .mqtt_client import MQTTClient

_LOGGER = logging.getLogger(__name__)
_LOGGER.warning("xbee_bridge __init__.py file loaded")


async def async_setup(hass, config):
    _LOGGER.info("XBee Bridge initializing...")
    _LOGGER.warning("xbee_bridge async_setup() called")
    conf = config.get("xbee_bridge", {})
    broker = conf.get("mqtt_broker", "localhost")
    port = conf.get("mqtt_port", 1883)
    username = conf.get("mqtt_user")
    password = conf.get("mqtt_password")
    mqtt = MQTTClient(broker, port, username, password)

    async def handle_test_publish(call):
        _LOGGER.warning("xbee_bridge: Test publish service called")
        await hass.async_add_executor_job(mqtt.publish_constant_test)

    hass.services.async_register("xbee_bridge", "test_publish", handle_test_publish)

    return True
