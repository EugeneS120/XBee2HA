class XBeeAPI:
    @staticmethod
    def encode_command(command):
        # Encode command to XBee API format
        return command.encode('utf-8')

    @staticmethod
    def decode_response(response):
        # Decode response from XBee API format
        return response.decode('utf-8')