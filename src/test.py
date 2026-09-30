from time import sleep

from kal100 import KAL100

with KAL100("COM7") as kal:
    print("Starting calibration sequence...")
    kal.set_zero_mode()
    sleep(5)
    print("Setting up the device...")
    kal.set_unit("hPa")
    sleep(0.1)
    kal.set_language("German")
    sleep(0.1)
    kal.set_auto_zero(False)
    sleep(0.1)
    kal.set_percentage("100%")
    sleep(0.1)
    kal.set_setpoint(0)
    sleep(0.1)

    print("Starting measurement sequence...")
    kal.start_measurement()
    sleep(0.1)
    kal.set_setpoint(100)
    sleep(10)
    kal.set_setpoint(200)
    sleep(10)
    kal.set_setpoint(300)
    sleep(10)
    kal.vent()

    print("Measurement sequence completed.")
