import runloop
import motor, distance_sensor, color_sensor, color
from hub import port, button

# Programm auf kleines Feld agestimmt

# Hub Anschluss: Motor X1 = Port A, Motor X2 = Port B, Motor Y2 = Port C, Motor Z2 = Port D, Distance Sensor = Port E, Color Sensor = Port F

#global variables
velocity_X1 = 150
velocity_X2 = 90
velocity_Y2 = 100
velocity_Z2 = 50
Motor_X1 = port.A           # Hub Port A
Motor_X2 = port.C           # Hub Port B
Motor_Y2 = port.F           # Hub Port C
Motor_Z2 = port.B           # Hub Port D
height_tablet = 40          # [mm]


###################################################### 
#                    Functions                       #
######################################################

# sets the default position of the Coordinate System
async def default_position():
   await motor.run_to_absolute_position(Motor_X2, 0, velocity_X2)
   await motor.run_to_absolute_position(Motor_Y2, 0, velocity_Y2)
   await motor.run_to_absolute_position(Motor_Z2, 0, velocity_Z2)

# defines the moving distance of the Motors
async def X2_relative(distance):    # [cm]
    motor.run_for_degrees(Motor_X2, distance *55, velocity_X2)
async def Y2_relative(distance):    # [cm]
    motor.run_for_degrees(Motor_Y2, -distance *55, velocity_Y2)




        
######################################################
#                    Start Sequence                  #
######################################################
async def start_sequence():
    # start sequence to move the base platform over the tablet
    motor.run(Motor_X1, velocity_X1)

    while True:
        distance = distance_sensor.distance(port.E)

        if distance <= 110:
            break

        await runloop.sleep_ms(10)

    await motor.run_for_degrees(Motor_X1, 90, velocity_X1, stop=motor.HOLD)

    

# function to calibrate actors
async def calibration():
    print("Drücke linken Button zum Kalibrieren")

    while not button.pressed(button.LEFT):
        await runloop.sleep_ms(10)

    await default_position()
    print("Kalibriert")


async def main():

    await calibration()
    await start_sequence()
  

runloop.run(main())