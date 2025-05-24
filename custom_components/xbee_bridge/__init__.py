import logging
from .mqtt_client import MQTTClient
from .xbee_device_handler import XBeeDeviceHandler

_LOGGER = logging.getLogger(__name__)
_LOGGER.warning("xbee_bridge __init__.py file loaded")


async def async_setup(hass, config):
    _LOGGER.info("XBee Bridge initializing...")
    _LOGGER.warning("xbee_bridge async_setup() called")
    conf = config.get("xbee_bridge", {})
    port = conf.get("port", "/dev/ttyUSB0")
    baud_rate = conf.get("baud_rate", 57600)
    sample_rate_ms = conf.get("sample_rate_ms", 1000)
    debug_mode = conf.get("debug_mode", False)
    broker = conf.get("mqtt_broker", "localhost")
    mqtt_port = conf.get("mqtt_port", 1883)
    mqtt_user = conf.get("mqtt_user")
    mqtt_password = conf.get("mqtt_password")

    mqtt = MQTTClient(broker, mqtt_port, mqtt_user, mqtt_password)

    if debug_mode:
        # Publish constant test values
        await hass.async_add_executor_job(mqtt.publish_constant_test)
    else:
        # Start XBee handler for real values
        handler = XBeeDeviceHandler(port, baud_rate, sample_rate_ms)

        def on_new_data(data):
            # Called when new sensor data is available
            # Publish each value to relevant MQTT topic
            for key, value in data.items():
                topic = f"home/sensors/xbee/{key}"
                mqtt.client.publish(topic, str(value), retain=True)

        handler.set_data_callback(on_new_data)
        # Start the handler in a thread/executor
        await hass.async_add_executor_job(handler.run)

    return True
