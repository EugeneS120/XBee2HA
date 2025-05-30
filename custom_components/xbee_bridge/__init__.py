import logging
import threading
from .mqtt_client import MQTTClient
from .xbee_device_handler import XBeeDeviceHandler

_LOGGER = logging.getLogger(__name__)
_LOGGER.warning("xbee_bridge __init__.py file loaded")
DOMAIN = "xbee_bridge"

def start_xbee_listener(handler, stop_event):
    # This will run in a background thread
    try:
        handler.open_device()
        handler.configure_device()
        handler.register_io_sample_callback()
        _LOGGER.info("XBee listener started, running until stopped...")
        while not stop_event.is_set():
            import time
            time.sleep(1)
    except Exception as e:
        _LOGGER.error(f"XBee listener stopped: {e}")
    finally:
        handler.disable_io_sampling()
        handler.close_device()

async def async_setup(hass, config):
    _LOGGER.info("XBee Bridge initializing...")
    _LOGGER.warning("xbee_bridge async_setup() called")
    conf = config.get("xbee_bridge", {})
    broker = conf.get("mqtt_broker", "localhost")
    port = conf.get("mqtt_port", 1883)
    username = conf.get("mqtt_user")
    password = conf.get("mqtt_password")
    debug_mode = conf.get("debug_mode", False)
    xbee_port = conf.get("port", "/dev/ttyUSB1")
    baud_rate = conf.get("baud_rate", 57600)
    sample_rate_ms = conf.get("sample_rate_ms", 1000)

    mqtt = MQTTClient(broker, port, username, password)

    async def handle_test_publish(call):
        _LOGGER.warning("xbee_bridge: Test publish service called")
        await hass.async_add_executor_job(mqtt.publish_constant_test)
    hass.services.async_register("xbee_bridge", "test_publish", handle_test_publish)

    ## Debug mode:
    if debug_mode:
        _LOGGER.warning("Running in debug_mode: publishing constant test values.")
        await hass.async_add_executor_job(mqtt.publish_constant_test)

    ## Real mode: Use XBee device handler
    # 1. Only check device availability here
    try:
        device = XBeeDeviceHandler(xbee_port, baud_rate, sample_rate_ms)
        device.open_device()
        device.close_device()
        _LOGGER.info("XBee device available and port can be opened/closed")
    except Exception as e:
        _LOGGER.error(f"XBee device unavailable at setup: {e}")
        return False

    # 2. Start the main handler in a background thread (non-blocking!)
    def xbee_data_callback(data):
        # Called whenever new sensor data is available
        # Publish each value to MQTT
        for key, value in data.items():
            topic = f"home/sensors/xbee/{key}"
            mqtt.client.publish(topic, str(value), retain=True)
            _LOGGER.info(f"Published {key}: {value} to {topic}")

    main_handler = XBeeDeviceHandler(xbee_port, baud_rate, sample_rate_ms)
    main_handler.set_data_callback(xbee_data_callback)

    thread = threading.Thread(target=start_xbee_listener, args=(main_handler,), daemon=True)
    thread.start()

    # 3. Store the handler for reload/service operations
    hass.data["xbee_bridge_handler"] = main_handler
    hass.data["xbee_bridge_thread"] = thread

    # Helper to start thread
    def start_handler():
        stop_event = threading.Event()
        handler = XBeeDeviceHandler(xbee_port, baud_rate, sample_rate_ms)
        handler.set_data_callback(xbee_data_callback)
        thread = threading.Thread(target=start_xbee_listener, args=(handler, stop_event), daemon=True)
        thread.start()
        return handler, thread, stop_event

    # Helper to stop thread
    def stop_handler():
        stop_event = hass.data[DOMAIN].get("stop_event")
        if stop_event:
            stop_event.set()
        thread = hass.data[DOMAIN].get("thread")
        if thread:
            thread.join(timeout=5)
        _LOGGER.info("XBee handler stopped.")

    # Store everything in hass.data
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    handler, thread, stop_event = start_handler()
    hass.data[DOMAIN]["handler"] = handler
    hass.data[DOMAIN]["thread"] = thread
    hass.data[DOMAIN]["stop_event"] = stop_event

    async def handle_reload(call):
        _LOGGER.warning("xbee_bridge: Reload service called")
        await hass.async_add_executor_job(stop_handler)
        handler, thread, stop_event = await hass.async_add_executor_job(start_handler)
        hass.data[DOMAIN]["handler"] = handler
        hass.data[DOMAIN]["thread"] = thread
        hass.data[DOMAIN]["stop_event"] = stop_event
        _LOGGER.info("xbee_bridge: Reload complete.")

    hass.services.async_register(DOMAIN, "reload", handle_reload)

    return True

