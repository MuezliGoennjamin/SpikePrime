import runloop
import motor, distance_sensor, color_sensor, color
from hub import port, button

# Programm auf kleines Feld agestimmt

# Hub Anschluss: Motor X1 = Port A, Motor X2 = Port B, Motor Y2 = Port C, Motor Z2 = Port D, Distance Sensor = Port E, Color Sensor = Port F

#global variables
velocity_X1 = 90
velocity_X2 = 90
velocity_Y2 = 50
velocity_Z2 = 10
Motor_X1 = port.A           # Hub Port A
Motor_X2 = port.B           # Hub Port B
Motor_Y2 = port.C           # Hub Port C
Motor_Z2 = port.D           # Hub Port D
height_tablet = 15          # [mm]




motor.run_for_degrees(Motor_X1, 900, velocity_X1, stop=motor.CONTINUE)
motor.run_for_degrees(Motor_X2, 400, velocity_X2, stop=motor.CONTINUE)
motor.run_for_degrees(Motor_Y2, 400, velocity_Y2, stop=motor.CONTINUE)
motor.run_for_degrees(Motor_Z2, 100, velocity_Z2, stop=motor.CONTINUE)
