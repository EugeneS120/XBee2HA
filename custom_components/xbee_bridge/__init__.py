import logging
import threading
from .mqtt_client import MQTTClient
from .xbee_device_handler import XBeeDeviceHandler

_LOGGER = logging.getLogger(__name__)
_LOGGER.warning("xbee_bridge __init__.py file loaded")

DOMAIN = "xbee_bridge"

def start_xbee_listener(handler, stop_event):
    # This will run in a background thread
    _LOGGER.warning("xbee_bridge: start_xbee_listener called N1")
    try:
        _LOGGER.warning("xbee_bridge: about to call handler.open_device() N2")
        handler.open_device()
        _LOGGER.warning("xbee_bridge: handler.open_device() succeeded N3")
        handler.configure_device()
        handler.register_io_sample_callback()
        _LOGGER.info("XBee listener started, running until stopped...")
        while not stop_event.is_set():
            import time
            time.sleep(1)
    except Exception as e:
        _LOGGER.error(f"XBee listener stopped: {e}", exc_info=True)
    finally:
        try:
            handler.disable_io_sampling()
        except Exception as e:
            _LOGGER.error(f"Failed to disable I/O sampling: {e}", exc_info=True)
        try:
            handler.close_device()
        except Exception as e:
            _LOGGER.error(f"Failed to close device: {e}", exc_info=True)

async def async_setup(hass, config):
    _LOGGER.info("XBee Bridge initializing...")
    _LOGGER.warning("xbee_bridge async_setup() called")
    conf = config.get(DOMAIN, {})
    broker = conf.get("mqtt_broker", "localhost")
    port = conf.get("mqtt_port", 1883)
    username = conf.get("mqtt_user")
    password = conf.get("mqtt_password")
    debug_mode = conf.get("debug_mode", False)
    xbee_port = conf.get("port", "/dev/ttyUSB1")
    baud_rate = conf.get("baud_rate", 57600)
    sample_rate_ms = conf.get("sample_rate_ms", 1000)

    # Save config for reload use
    hass.data.setdefault(DOMAIN, {})["config"] = conf

    # Disconnect and cleanup old client if present
    if DOMAIN in hass.data and "mqtt_client" in hass.data[DOMAIN]:
        old_client = hass.data[DOMAIN]["mqtt_client"]
        old_client.disconnect()

    # Create and connect new MQTT client
    mqtt = MQTTClient(broker, port, username, password)
    mqtt.connect()
    hass.data[DOMAIN]["mqtt_client"] = mqtt

    async def handle_test_publish(call):
        _LOGGER.warning("xbee_bridge: Test publish service called")
        await hass.async_add_executor_job(hass.data[DOMAIN]["mqtt_client"].publish_constant_test)
    hass.services.async_register(DOMAIN, "test_publish", handle_test_publish)

    ## Debug mode: only send test MQTT messages, skip XBee setup
    if debug_mode:
        _LOGGER.warning("Running in debug_mode: publishing constant test values.")
        await hass.async_add_executor_job(hass.data[DOMAIN]["mqtt_client"].publish_constant_test)

    ## Real mode: Use XBee device handler
    # 1. Only check device availability here
    try:
        test_device = XBeeDeviceHandler(xbee_port, baud_rate, sample_rate_ms)
        test_device.open_device()
        test_device.close_device()
        _LOGGER.info("XBee device available and port can be opened/closed")
    except Exception as e:
        _LOGGER.error(f"XBee device unavailable at setup: {e}")
        _LOGGER.error("xbee_bridge: Returning False from async_setup due to XBee device error")
        return False

    # 2. XBee data callback: always use latest mqtt_client from hass.data
    # Called whenever new sensor data is available
    # Publish each value to MQTT
    def xbee_data_callback(data):
        _LOGGER.warning(f"xbee_bridge: Received XBee data: {data}")
        mqtt_client = hass.data[DOMAIN].get("mqtt_client")
        if mqtt_client:
            for key, value in data.items():
                topic = f"home/sensors/xbee/{key}"
                mqtt_client.client.publish(topic, str(value), retain=True)
                _LOGGER.info(f"Published {key}: {value} to {topic}")
        else:
            _LOGGER.error("No mqtt_client available to publish data!")

    # 3. Helper to start handler
    def start_handler():
        _LOGGER.warning("xbee_bridge: start_handler called N1")
        stop_event = threading.Event()
        handler = XBeeDeviceHandler(xbee_port, baud_rate, sample_rate_ms)
        handler.set_data_callback(xbee_data_callback)
        thread = threading.Thread(target=start_xbee_listener, args=(handler, stop_event), daemon=True)
        thread.start()
        _LOGGER.warning("xbee_bridge: start_handler called N2")
        return handler, thread, stop_event

    # 4. Helper to stop handler
    def stop_handler():
        stop_event = hass.data[DOMAIN].get("stop_event")
        if stop_event:
            stop_event.set()
        thread = hass.data[DOMAIN].get("thread")
        if thread:
            thread.join(timeout=5)
        _LOGGER.info("XBee handler stopped.")

    # 5. Store everything in hass.data
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    handler, thread, stop_event = start_handler()
    hass.data[DOMAIN]["handler"] = handler
    hass.data[DOMAIN]["thread"] = thread
    hass.data[DOMAIN]["stop_event"] = stop_event

    # 6. Reload service
    async def handle_reload(call):
        _LOGGER.warning("xbee_bridge: Reload service called")
        await hass.async_add_executor_job(stop_handler)

        # Disconnect MQTT client before restarting
        try:
            old_mqtt = hass.data[DOMAIN].get("mqtt_client")
            if old_mqtt:
                old_mqtt.disconnect()
                _LOGGER.info("Disconnected old MQTT client.")
        except Exception as e:
            _LOGGER.error(f"Error disconnecting MQTT client: {e}")

        # Re-create and connect new MQTT client using saved config
        conf = hass.data[DOMAIN].get("config", {})
        broker = conf.get("mqtt_broker", "localhost")
        port = conf.get("mqtt_port", 1883)
        username = conf.get("mqtt_user")
        password = conf.get("mqtt_password")
        new_mqtt = MQTTClient(broker, port, username, password)
        new_mqtt.connect()
        hass.data[DOMAIN]["mqtt_client"] = new_mqtt

        new_handler, new_thread, new_stop_event = await hass.async_add_executor_job(start_handler)
        hass.data[DOMAIN]["handler"] = new_handler
        hass.data[DOMAIN]["thread"] = new_thread
        hass.data[DOMAIN]["stop_event"] = new_stop_event
        _LOGGER.info("xbee_bridge: Reload complete.")

    hass.services.async_register(DOMAIN, "reload", handle_reload)

    _LOGGER.warning("xbee_bridge: About to return True from async_setup")
    return True
