import argparse
from time import sleep

import serial

from kal100 import KAL100

M603_BAUDRATE = 115200
M603_TIMEOUT = 0.3
CALIBRATION_POINTS = {"-1000", "-200", "0", "200", "1000"}


def calculate_crc_ccitt_from_str(input_str, initial=0xFFFF, polynomial=0x1021):
    """Calculate the CRC-CCITT-16 for a given string."""
    crc = initial
    for char in input_str:
        crc ^= ord(char) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ polynomial
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def pressure_from_frame(frame):
    """Return the pressure from a valid field 950 command, if supported."""
    try:
        command = frame.decode("ascii")
    except UnicodeDecodeError:
        return None

    if len(command) < 8 or command[:3] != "950" or command[3] != "G":
        return None

    payload, received_crc = command[:-4], command[-4:]
    if f"{calculate_crc_ccitt_from_str(payload):04X}" != received_crc:
        return None

    pressure = payload[4:]
    return pressure if pressure in CALIBRATION_POINTS else None


def main():
    parser = argparse.ArgumentParser(
        description="Control a KAL100 from M603 calibration commands."
    )
    parser.add_argument("m603_port", help="M603 serial port, e.g. COM4")
    parser.add_argument("kal100_port", help="KAL100 serial port, e.g. COM7")
    args = parser.parse_args()

    m603 = serial.Serial(
        port=args.m603_port,
        baudrate=M603_BAUDRATE,
        timeout=M603_TIMEOUT,
    )

    try:
        with KAL100(args.kal100_port) as calibrator, m603:
            calibrator.set_unit("hPa")
            sleep(0.1)

            print("Starting M603 to KAL100 calibration loop.")
            while True:
                frame = m603.read_until(b"\r").rstrip(b"\r\n")
                pressure = pressure_from_frame(frame)
                if pressure is None:
                    continue

                m603.write(b"\x06")
                m603.flush()

                if pressure == "0":
                    print("Received zero pressure command.")
                    calibrator.vent()
                else:
                    print(f"Received pressure command: {pressure} hPa")
                    calibrator.start_measurement()
                    sleep(0.1)
                    calibrator.set_setpoint(abs(int(pressure)))

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
