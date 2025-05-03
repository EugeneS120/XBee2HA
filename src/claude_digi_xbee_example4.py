from digi.xbee.devices import XBeeDevice, RemoteXBeeDevice, XBee64BitAddress
from digi.xbee.io import IOLine, IOMode, IOValue
from digi.xbee.util import utils
import time
import struct
import re

# Replace with the serial port and baud rate of your XBee module
PORT = "/dev/ttyUSB0"  # Example for Linux; use "COMx" for Windows
BAUD_RATE = 57600

# Sample rate in milliseconds
SAMPLE_RATE_MS = 1000  # 1 second

def main():
    # Initialize the XBee device
    device = XBeeDevice(PORT, BAUD_RATE)
    callback_added = False

    try:
        # Open the XBee device
        device.open(force_settings=True)
        print("Device opened successfully!")

        print("XBee device is:", device.get_node_id())  # Node Identifier (NI)
        print("Firmware version:", device.get_firmware_version())
        print("Packet listener:", device._packet_listener.is_running())

        # Configure the DIO2_AD2 line of the remote device to be Analog input (ADC).
        device.set_io_configuration(IOLine.DIO2_AD2, IOMode.ADC)
        # Configure the DIO3_AD3 line of the local device to be Digital input.
        device.set_io_configuration(IOLine.DIO3_AD3, IOMode.DIGITAL_IN)
        print("DIO2, DIO3 configured")

        # Set the destination address (broadcast)
        device.set_dest_address(XBee64BitAddress.from_hex_string("000000000000FFFF"))
        print("Address set to broadcast")

        # Set a higher timeout to avoid response errors
        device.set_sync_ops_timeout(5000)  # 5 seconds timeout

        # Define the IO sample receive callback
        def io_sample_callback(io_sample, remote_xbee, send_time):
            print(f"\nIO sample received at time {time.strftime('%H:%M:%S')}")

            try:
                # Convert the object to a string and parse it manually
                sample_str = str(io_sample)
                print(f"Raw sample data: {sample_str}")

                # Parse digital values
                digital_matches = re.findall(r'IOLine\.([A-Z0-9_]+):\s*IOValue\.([A-Z]+)', sample_str)
                if digital_matches:
                    print("Digital values:")
                    for line, value in digital_matches:
                        print(f"  {line}: {value}")

                # Parse analog values
                analog_matches = re.findall(r'IOLine\.([A-Z0-9_]+):\s*(\d+)', sample_str)
                if analog_matches:
                    print("Analog values:")
                    for line, value_str in analog_matches:
                        value = int(value_str)
                        voltage = (value / 1023) * 3.3  # Assuming 3.3V reference
                        print(f"  {line}: {value} (approx. {voltage:.2f}V)")

            except Exception as e:
                print(f"Error processing sample: {e}")
                print(f"Raw sample data: {io_sample}")

        # Register the callback for IO samples
        device.add_io_sample_received_callback(io_sample_callback)
        callback_added = True

        # Set the I/O sampling rate
        print(f"Setting I/O sampling rate to {SAMPLE_RATE_MS} milliseconds...")
        sample_rate_bytes = struct.pack(">H", SAMPLE_RATE_MS)
        device.set_parameter("IR", sample_rate_bytes)
        print("Sample rate set successfully")

        # Verify the sample rate setting
        current_rate_bytes = device.get_parameter("IR")
        current_rate = int.from_bytes(current_rate_bytes, byteorder='big')
        print(f"Confirmed sample rate is: {current_rate} milliseconds")

        # Apply changes to make sure settings are saved
        device.apply_changes()
        print("Changes applied")

        # Request an immediate sample
        print("\nRequesting an immediate IO sample...")
        result = device.execute_command("IS")
        if result:
            print("IS command result:", result)
        else:
            print("IS command executed but returned no data")

        print("\nListening for periodic IO samples...")
        print("(Press Enter to stop)")

        # Keep the program running to listen for I/O samples
        input()

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Cleanup before closing
        if device is not None and device.is_open():
            # Disable IO sampling before closing
            print("Disabling IO sampling...")
            try:
                device.set_parameter("IR", b'\x00\x00')  # Set IR to 0
                device.apply_changes()
            except Exception as e:
                print(f"Error disabling sampling: {e}")

            # Remove callback if it was added
            if callback_added:
                try:
                    device.del_io_sample_received_callback(io_sample_callback)
                except Exception as e:
                    print(f"Error removing callback: {e}")

            # Close device
            device.close()
            print("Device closed.")

if __name__ == "__main__":
    main()