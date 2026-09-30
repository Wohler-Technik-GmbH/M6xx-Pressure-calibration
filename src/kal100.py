"""A small serial interface for controlling a KAL100."""

import math
from typing import ClassVar

import serial


class KAL100:
    """Control a KAL100 through its USB serial port."""

    PERCENT: ClassVar[dict[str, int]] = {
        "5%": 0,
        "10%": 1,
        "20%": 2,
        "25%": 3,
        "50%": 4,
        "100%": 5,
    }

    UNIT: ClassVar[dict[str, int]] = {
        "kPa": 0,
        "Pa": 1,
        "hPa": 2,
        "mbar": 3,
        "psi": 4,
        "Torr": 5,
        "mmHg": 6,
        "mmH2O": 7,
        "inHg": 8,
        "inH2O": 9,
    }

    LANGUAGE: ClassVar[dict[str, int]] = {
        "German": 0,
        "English": 1,
        "French": 2,
        "Italian": 3,
        "Spanish": 4,
    }

    def __init__(self, port, timeout=1.0):
        self.serial = serial.Serial(
            port=port,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout,
        )

    def close(self):
        self.serial.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _write_command(self, command):
        self.serial.write(command.encode("ascii") + b"\r\n")
        self.serial.flush()

    def _write_command_with_response(self, command, expected=None):
        """Read the response and optionally check the expected echo."""
        self._write_command(command)
        response = self.serial.read_until(b"\r")
        if not response:
            raise TimeoutError(f"No response to command {command!r}")
        response = response.decode("ascii", errors="replace").rstrip("\r\n")
        if not response.strip():
            raise TimeoutError(f"Empty response to command {command!r}")
        response = response.strip()
        # print(f"Device response: {response}")
        if expected is not None and "".join(response.split()) != "".join(
            expected.split()
        ):
            raise RuntimeError(
                f"Unexpected response to {command!r}: {response!r}; "
                f"expected {expected!r}"
            )
        return response

    # Operating modes

    def set_test_mode(self):
        """Set the KAL100 to test mode."""
        return self._write_command_with_response("MT", expected="MT")

    def set_zero_mode(self):
        """Set the KAL100 to zero mode."""
        return self._write_command_with_response("MZ", expected="MZ")

    def set_setpoint_mode(self):
        """Enable setpoint mode."""
        return self._write_command_with_response("MS", expected="MS")

    def set_pressure_measurement_mode(self):
        """Enable pressure measurement mode."""
        return self._write_command_with_response("MP", expected="MP")

    def enable_keyboard(self):
        """Enable the device keyboard."""
        return self._write_command_with_response("MK1", expected="MK1")

    def disable_keyboard(self):
        """Disable the device keyboard."""
        return self._write_command_with_response("MK0", expected="MK0")

    def block_inputs(self):
        """Block the inputs and set the device to inactive mode."""
        return self._write_command_with_response("MB", expected="MB")

    def vent(self):
        """Vent in pressure or setpoint mode."""
        return self._write_command_with_response("ME", expected="ME")

    def start_measurement(self):
        """Start a measurement in pressure or setpoint mode."""
        return self._write_command_with_response("MM", expected="MM")

    def select_positive_input(self):
        """Select the positive pressure input."""
        return self._write_command_with_response("MI0", expected="MI0")

    def select_negative_input(self):
        """Select the negative pressure input."""
        return self._write_command_with_response("MI1", expected="MI1")

    def select_differential_pressure_input(self):
        """Select the differential pressure input."""
        return self._write_command_with_response("MI2", expected="MI2")

    # Set parameters

    @staticmethod
    def _validate_integer(value, name, minimum, maximum):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer.")
        if not minimum <= value <= maximum:
            raise ValueError(f"{name} must be between {minimum} and {maximum}.")
        return value

    @staticmethod
    def _option_value(value, options, name):
        normalized_value = value.casefold()
        for option, mapped_value in options.items():
            if option.casefold() == normalized_value:
                return mapped_value
        raise ValueError(
            f"Invalid {name}. Allowed values are: {', '.join(options.keys())}"
        )

    def set_setpoint(self, setpoint):
        """Set the setpoint in hPa to five decimal places."""
        setpoint = float(setpoint)
        if not math.isfinite(setpoint) or not 0 <= setpoint <= 1000:
            raise ValueError("The setpoint must be finite and between 0 and 1000 hPa.")
        self._write_command_with_response(
            f">PS{setpoint:.5f}", expected=f"PS{setpoint:.5f}"
        )
        return setpoint

    def set_step_size(self, step):
        """Set the step size (0 to 5)."""
        NAME = "step size"
        if isinstance(step, str):
            step = self._option_value(step, self.PERCENT, NAME)
        step = self._validate_integer(step, NAME, 0, 5)
        self._write_command_with_response(f">PD{step}", expected=f"PD{step}")

    def set_unit(self, unit):
        """Set the measurement unit (0 to 9)."""
        NAME = "measurement unit"
        if isinstance(unit, str):
            unit = self._option_value(unit, self.UNIT, NAME)
        unit = self._validate_integer(unit, NAME, 0, 9)
        self._write_command_with_response(f">PE{unit}", expected=f"PE{unit}")

    def set_language(self, language):
        """Set the language (0 German, 1 English, 2 French, 3 Italian, 4 Spanish)."""
        NAME = "language"
        if isinstance(language, str):
            language = self._option_value(language, self.LANGUAGE, NAME)
        language = self._validate_integer(language, NAME, 0, 4)
        self._write_command_with_response(f">PL{language}", expected=f"PL{language}")

    def set_percentage(self, percentage):
        """Set the percentage value (0 to 100)."""
        NAME = "percentage value"
        percentage = self._validate_integer(percentage, NAME, 0, 100)
        self._write_command_with_response(
            f">PP{percentage:03d}", expected=f"PP{percentage}"
        )

    def set_auto_zero(self, enabled):
        """Enable or disable automatic zeroing."""
        if isinstance(enabled, bool):
            enabled = int(enabled)
        NAME = "automatic zeroing"
        enabled = self._validate_integer(enabled, NAME, 0, 1)
        self._write_command_with_response(f">PZ{enabled}", expected=f"PZ{enabled}")

    # Other commands

    def save_parameters(self):
        """Save the current settings."""
        return self._write_command_with_response("STOS", expected="OK")

    def load_settings(self):
        """Load the saved settings."""
        return self._write_command_with_response("RCLS", expected="OK")

    def load_device_parameters(self):
        """Load the device parameters."""
        return self._write_command_with_response("RCLP", expected="OK")

    def get_version(self):
        """Read a non-empty version string in any format."""
        return self._write_command_with_response("RV")

    # Query values

    def get_setpoint(self):
        """Get the setpoint in hPa."""
        return self._write_command_with_response("?PS")

    def get_pressure_range(self):
        """Get the pressure range in hPa."""
        return self._write_command_with_response("?PB")

    def get_step_size(self):
        """Get the configured step size."""
        return self._write_command_with_response("?PD")

    def get_unit(self):
        """Get the measurement unit."""
        return self._write_command_with_response("?PE")

    def get_language(self):
        """Get the configured language."""
        return self._write_command_with_response("?PL")

    def get_percentage(self):
        """Get the percentage value."""
        return self._write_command_with_response("?PP")

    def get_auto_zero(self):
        """Get the automatic zeroing status."""
        return self._write_command_with_response("?PZ")

    def get_input_mode(self):
        """Get the input mode."""
        return self._write_command_with_response("?MI")

    def get_status(self):
        """Get the device status."""
        return self._write_command_with_response("?ST")

    def get_measurement_range(self):
        """Get the measurement range."""
        return self._write_command_with_response("?BR")

    def get_battery_charge(self):
        """Get the battery charge level."""
        return self._write_command_with_response("?AL")

    def get_battery_voltage(self):
        """Get the battery voltage."""
        return self._write_command_with_response("?AU")

    def get_battery_current(self):
        """Get the battery current."""
        return self._write_command_with_response("?AI")

    def get_power_source(self):
        """Get the active power source."""
        return self._write_command_with_response("?AQ")

    def get_current_pressure(self):
        """Get the current pressure reading in hPa."""
        return self._write_command_with_response("?IP")

    def get_voltage(self):
        """Get the voltage in V."""
        return self._write_command_with_response("?IV")

    def get_current(self):
        """Get the current in mA."""
        return self._write_command_with_response("?IA")

    def get_test_difference_pressure(self):
        """Get the test pressure difference in hPa."""
        return self._write_command_with_response("?ID")

    def get_test_duration(self):
        """Get the test duration in seconds."""
        return self._write_command_with_response("?IZ")
