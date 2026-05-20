from pybricks.parameters import Port, Color
from pybricks.pupdevices import ColorSensor
from pybricks.tools import wait

# Initialize the sensor.
sensor = ColorSensor(Port.D)

def main():
    # Turn the sensor light ON (e.g. white for best color detection)
    while True:
        sensor.lights.on()

        print(sensor.color())
        wait(500)
        print(sensor.color())
        wait(2000)
        sensor.lights.off()
        wait(2000)
        sensor.lights.on(20)

main()





