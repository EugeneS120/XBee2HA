from xbee import XBee
import serial

class XBeeCommunication:
    def __init__(self, port, baud_rate):
        self.ser = serial.Serial(port, baud_rate)
        self.xbee = XBee(self.ser)

    def send_command(self, command):
        self.xbee.send(command)

    def get_response(self):
        response = self.xbee.wait_read_frame()
        return response