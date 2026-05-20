import runloop
import motor, distance_sensor, color_sensor, color
from hub import port, button

# Programm auf kleines Feld agestimmt

# Hub Anschluss: Motor X1 = Port A, Motor X2 = Port B, Motor Y2 = Port C, Motor Z2 = Port D, Distance Sensor = Port E, Color Sensor = Port F

#global variables
velocity_X1 = 150
velocity_X2 = 90
velocity_Y2 = -100
velocity_Z2 = 50
Motor_X1 = port.A           # Hub Port A
Motor_X2 = port.B           # Hub Port B
Motor_Y2 = port.C           # Hub Port C
Motor_Z2 = port.D           # Hub Port D
height_tablet = 15          # [mm]

# tap on the touchscreen to place the token
async def Z2_tap():

    # press down
    await motor.run_to_absolute_position(
        Motor_Z2,
        110,
        velocity_Z2
    )

    # short press time
    await runloop.sleep_ms(300)

    # move back up
    await motor.run_to_absolute_position(
        Motor_Z2,
        180,
        velocity_Z2
    )

    # wait for stable end position
    await runloop.sleep_ms(300)

async def main():
    await Z2_tap()

runloop.run(main())


