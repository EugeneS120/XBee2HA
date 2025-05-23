import logging
from digi.xbee.devices import XBeeDevice, XBee64BitAddress
from digi.xbee.io import IOLine, IOMode
import struct
import re
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

class XBeeDeviceHandler:
    def __init__(self, port, baud_rate, sample_rate_ms):
        self.port = port
        self.baud_rate = baud_rate
        self.sample_rate_ms = sample_rate_ms
        self.device = None
        self.data = {
            "status": None,
            "sample_time": None,
            "dio2_ad2": None,
            "dio3_ad3": None,
        }

    def open_device(self):
        """Open the XBee device and fetch device information."""
        try:
            self.device = XBeeDevice(self.port, self.baud_rate)
            self.device.open(force_settings=True)
            #_LOGGER.info("Device opened successfully on port %s", self.port)
            node_id = self.device.get_node_id().strip()
            firmware_bytes = self.device.get_firmware_version()
            version_hex = "".join(f"{b:02x}" for b in firmware_bytes)
            status_str = f"XBEE module: {node_id}, Firmware version: {version_hex}"
            self.data["status"] = status_str
            _LOGGER.info(status_str)

            ## Structured and formatted version
            #self.data["status_struct"] = {
            #    "node_id": node_id,
            #    "firmware_version": version_hex
            #}
            #self.data["status"] = f"XBEE module: {node_id}, Firmware version: {version_hex}"

        except Exception as e:
            _LOGGER.error("Failed to open XBee device: %s", e)
            raise

    def configure_device(self):
        """Configure the XBee device."""
        try:
            # Configure DIO2_AD2 as Analog Input
            self.device.set_io_configuration(IOLine.DIO2_AD2, IOMode.ADC)
            # Configure DIO3_AD3 as Digital Input
            self.device.set_io_configuration(IOLine.DIO3_AD3, IOMode.DIGITAL_IN)
            _LOGGER.info("DIO2 and DIO3 configured")

            # Set destination address to broadcast
            self.device.set_dest_address(XBee64BitAddress.from_hex_string("000000000000FFFF"))
            _LOGGER.info("Address set to broadcast")

            # Set I/O sampling rate
            sample_rate_bytes = struct.pack(">H", self.sample_rate_ms)
            self.device.set_parameter("IR", sample_rate_bytes)
            _LOGGER.info("Sample rate set to %d milliseconds", self.sample_rate_ms)

            # Apply changes to save the configuration
            self.device.apply_changes()
            _LOGGER.info("Configuration changes applied")

            # note: IS command executed as request, not expected returned data
            self.device.execute_command("IS")
            _LOGGER.info("IS command sent to request immediate sample")

        except Exception as e:
            _LOGGER.error("Failed to configure XBee device: %s", e)
            raise

    def register_io_sample_callback(self):
        """Register a callback function to process incoming I/O samples."""
        def io_sample_callback(io_sample, remote_xbee, send_time):
            _LOGGER.info("I/O sample received at time %s", datetime.now().strftime('%H:%M:%S'))

            try:
                # Convert the object to a string and parse it manually
                sample_str = str(io_sample)
                _LOGGER.info("Raw sample data: %s", sample_str)

                # Parse digital values
                digital_matches = re.findall(r'IOLine\.([A-Z0-9_]+):\s*IOValue\.([A-Z]+)', sample_str)
                for line, value in digital_matches:
                    if line == "DIO3_AD3":
                        self.data["dio3_ad3"] = value
                    _LOGGER.info("%s: %s", line, value)

            # Parse analog values
                analog_matches = re.findall(r'IOLine\.([A-Z0-9_]+):\s*(\d+)', sample_str)
                for line, value_str in analog_matches:
                    if line == "DIO2_AD2":
                        value = int(value_str)
                        voltage = (value / 1023) * 3.3  # Assuming a 3.3V reference
                        formatted = f"{line}: {value} (approx. {voltage:.2f}V)"
                        self.data["dio2_ad2"] = formatted
                    _LOGGER.info(formatted)
                # Save the sample time
                self.data["sample_time"] = datetime.now().isoformat()
                _LOGGER.info("Sample time: %s", self.data["sample_time"])
            except Exception as e:
                _LOGGER.error("Error processing I/O sample: %s", e)

        try:
            self.device.add_io_sample_received_callback(io_sample_callback)
            _LOGGER.info("I/O sample callback registered")
        except Exception as e:
            _LOGGER.error("Failed to register I/O sample callback: %s", e)
            raise

    def disable_io_sampling(self):
        """Disable I/O sampling."""
        try:
            self.device.set_parameter("IR", b'\x00\x00')  # Set IR to 0
            self.device.apply_changes()
            _LOGGER.info("I/O sampling disabled")
        except Exception as e:
            _LOGGER.error("Failed to disable I/O sampling: %s", e)
            raise

    def close_device(self):
        """Close the XBee device."""
        if self.device and self.device.is_open():
            try:
                self.device.close()
                _LOGGER.info("Device closed")
            except Exception as e:
                _LOGGER.error("Error closing XBee device: %s", e)

    def execute_sequence(self):
        """Execute the full sequence: open, configure, register callback, wait for one sample, disable sampling, close."""
        try:
            self.open_device()
            self.configure_device()
            self.register_io_sample_callback()
            _LOGGER.info("Waiting for I/O sample...")
            time.sleep(5)  # Wait for a sample to be received
            self.disable_io_sampling()
        finally:
            self.close_device()
