import logging
from .mqtt_client import MQTTClient
from .xbee_device_handler import XBeeDeviceHandler

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
    debug_mode = conf.get("debug_mode", False)
    xbee_port = conf.get("port", "/dev/ttyUSB0")
    baud_rate = conf.get("baud_rate", 57600)
    sample_rate_ms = conf.get("sample_rate_ms", 1000)

    mqtt = MQTTClient(broker, port, username, password)

    async def handle_test_publish(call):
        _LOGGER.warning("xbee_bridge: Test publish service called")
        await hass.async_add_executor_job(mqtt.publish_constant_test)

    hass.services.async_register("xbee_bridge", "test_publish", handle_test_publish)

    if debug_mode:
        _LOGGER.warning("Running in debug_mode: publishing constant test values.")
        await hass.async_add_executor_job(mqtt.publish_constant_test)
        return True

    # Real mode: Use XBee device handler
    def xbee_data_callback(data):
        # Called whenever new sensor data is available
        # Publish each value to MQTT
        for key, value in data.items():
            topic = f"home/sensors/xbee/{key}"
            mqtt.client.publish(topic, str(value), retain=True)
            _LOGGER.info(f"Published {key}: {value} to {topic}")

    handler = XBeeDeviceHandler(xbee_port, baud_rate, sample_rate_ms)
    handler.set_data_callback(xbee_data_callback)

    # Run the handler in a background thread so it doesn't block Home Assistant
    await hass.async_add_executor_job(handler.run)

    return True
