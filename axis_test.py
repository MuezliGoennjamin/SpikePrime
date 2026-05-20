from pybricks.parameters import Port, Color
from pybricks.pupdevices import ColorSensor
from pybricks.tools import wait, multitask, run_task

# Sensor initialisieren
sensor = ColorSensor(Port.D)

# --------------------------------------------------
# Hintergrund-Task: Licht dauerhaft setzen
# --------------------------------------------------
async def light_task():
    while True:
        # konstantes Licht (grün hier als Beispiel)
        sensor.lights.on([0, 20, 0])
        await wait(100)

# --------------------------------------------------
# Haupt-Task: Farbe + Helligkeit ausgeben
# --------------------------------------------------


# --------------------------------------------------
# Main
# --------------------------------------------------
async def main():
    await multitask(
        light_task()
)

    print("Farbe:", sensor.color())
    print("Reflex:", sensor.reflection())
    print("----------------------")
    await wait(500)
# Start
run_task(main())





