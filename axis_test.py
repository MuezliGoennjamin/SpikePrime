from pybricks.pupdevices import ColorSensor, ForceSensor
from pybricks.parameters import Port

button = ForceSensor(Port.B)
sensor = ColorSensor(Port.F)

while True:
    if button.pressed():
        hsv = sensor.hsv(surface=False)
        ambient = sensor.ambient()
        print(hsv, ambient)





