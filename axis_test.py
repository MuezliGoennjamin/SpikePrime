from pybricks.hubs import PrimeHub
from pybricks.pupdevices import ColorSensor
from pybricks.parameters import Port, Button
from pybricks.tools import wait

hub = PrimeHub()
sensor = ColorSensor(Port.D)

# Helligkeitsstufen in Prozent
brightness_levels = [0, 25, 50, 75, 100]
brightness_index = 2  # startet bei 50%

current_brightness = brightness_levels[brightness_index]
sensor.lights.on(current_brightness)
print("Helligkeit:", current_brightness, "%")

while True:
    pressed = hub.buttons.pressed()

    # Linker Button: Farbwerte messen und ausgeben
    if Button.LEFT in pressed:
        hsv = sensor.hsv(surface=False)
        ambient = sensor.ambient()
        print("HSV:", hsv, "| Ambient:", ambient, "| Helligkeit:", current_brightness, "%")
        wait(300)

    # Rechter Button: Helligkeit der Sensor-LEDs erhöhen (zyklisch)
    if Button.RIGHT in pressed:
        brightness_index = (brightness_index + 1) % len(brightness_levels)
        current_brightness = brightness_levels[brightness_index]
        sensor.lights.on(current_brightness)
        print("Helligkeit:", current_brightness, "%")
        wait(300)

    wait(10)





