from xbee import XBee
import serial
import logging

_LOGGER = logging.getLogger(__name__)

class XBeeCommunication:
    def __init__(self, port, baud_rate):
        self.ser = serial.Serial(port, baud_rate)
        self.xbee = XBee(self.ser)

    def send_command(self, command):
        _LOGGER.info(f"Sending command to XBee: {command}")
        self.xbee.send(command)

    def get_response(self):
        response = self.xbee.wait_read_frame()
        _LOGGER.info(f"Received response from XBee: {response}")
        return response