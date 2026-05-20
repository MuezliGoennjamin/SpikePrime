from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor, UltrasonicSensor
from pybricks.parameters import Port, Color, Button, Stop
from pybricks.tools import wait, run_task

# ============================================
#               HUB + DEVICES
# ============================================

hub = PrimeHub()

motor_x1 = Motor(Port.A)
motor_x2 = Motor(Port.C)
motor_y2 = Motor(Port.F)
motor_z2 = Motor(Port.B)

distance_sensor = UltrasonicSensor(Port.E)
color_sensor = ColorSensor(Port.D)

# ============================================
#               GLOBAL VALUES
# ============================================

velocity_X1 = 150
velocity_X2 = 90
velocity_Y2 = 100
velocity_Z2 = 50

Motor_X1 = motor_x1
Motor_X2 = motor_x2
Motor_Y2 = motor_y2
Motor_Z2 = motor_z2


# ============================================
#            WAIT FOR LEFT BUTTON
# ============================================

def wait_for_left_button(step=""):

    print("--------------------------------")

    if step != "":
        print("WAIT:", step)
    else:
        print("WAIT FOR LEFT BUTTON")

    while Button.LEFT not in hub.buttons.pressed():
        wait(100)

    print("BUTTON PRESSED")
    print("--------------------------------")


# ============================================
#               MOTOR FUNCTIONS
# ============================================

def default_position():
    motor_x2.run_target(velocity_X2, 0, wait=True)
    motor_y2.run_target(velocity_Y2, 0, wait=True)
    motor_z2.run_target(velocity_Z2, 180, wait=True)


def X2_relative(distance):
    motor_x2.run_angle(velocity_X2, distance * 5, wait=True)


def Y2_relative(distance):
    motor_y2.run_angle(velocity_Y2, -distance * 5, wait=True)


def Z2_tap():
    motor_z2.run_target(velocity_Z2, 180, wait=True)
    wait(300)
    motor_z2.run_target(velocity_Z2, 140, wait=True)
    wait(300)


# ============================================
#               FIELD SCAN
# ============================================

def field_scan(position, board):

    wait(500)

    detected_color = color_sensor.color()

    if detected_color == Color.GREEN:
        board.set(position, 0)

    elif detected_color == Color.WHITE:
        board.set(position, 1)

    elif detected_color == Color.BLACK:
        board.set(position, 2)


# ============================================
#               REVERSI BOARD
# ============================================

class ReversiBoard:

    def __init__(self):
        self.board = []
        for row in range(8):
            self.board.append([0] * 8)

    def _parse_position(self, position):
        column_letter = position[0].upper()
        column_number = ord(column_letter) - ord('A')

        row_number = int(position[1])
        row_index = row_number - 1

        return row_index, column_number

    def set(self, position, value):
        row, col = self._parse_position(position)
        self.board[row][col] = value

    def get(self, position):
        row, col = self._parse_position(position)
        return self.board[row][col

    def get_all_positions(self):
        all_positions = []

        for row in range(8):
            for col in range(8):

                position = chr(ord('A') + col) + str(row + 1)
                value = self.board[row][col]

                all_positions.append((position, value))

        return all_positions


# ============================================
#              ROBOT MOVEMENT
# ============================================

def move_to_position(position):

    row = int(position[1])
    col = ord(position[0]) - ord('A')

    x_distance = (8 - row) * 18
    y_distance = col * 20

    default_position()

    X2_relative(18 + x_distance)
    Y2_relative(20 + y_distance)

    wait(500)

    Z2_tap()

    wait(500)

    default_position()


# ============================================
#              START SEQUENCE
# ============================================

def start_sequence():

    motor_x1.run(velocity_X1)

    while True:
        distance = distance_sensor.distance()

        if distance <= 110:
            break

        wait(10)

    motor_x1.run_time(velocity_X1, 10, then=Stop.HOLD, wait=True)


# ============================================
#              CALIBRATION
# ============================================

def calibration():

    print("Drücke linken Button zum Kalibrieren")

    while Button.LEFT not in hub.buttons.pressed():
        wait(10)

    default_position()

    print("Kalibriert")

    print(
        motor_x2.angle(),
        motor_y2.angle(),
        motor_z2.angle()
    )


# ============================================
#            PLAYGROUND SCAN
# ============================================

def playground_scan(board):

    row = 8
    column = 65

    default_position()

    wait_for_left_button("Start Scan")

    X2_relative(18)
    Y2_relative(20)

    field_scan("A8", board)

    while column <= 72:

        if row == 8:
            row = 7

            while row >= 1:

                position = chr(column) + str(row)

                X2_relative(18)
                field_scan(position, board)

                row -= 1

        else:

            while row <= 8:

                position = chr(column) + str(row)

                X2_relative(-18)
                field_scan(position, board)

                row += 1

        if row == 0:
            row = 1
        elif row == 9:
            row = 8

        column += 1

        if column > 72:
            break

        Y2_relative(20)

        position = chr(column) + str(row)
        field_scan(position, board)

        if column % 2 == 0:
            row += 1


# ============================================
#              GAME LOOP
# ============================================

def reversi_turn(board):

    print("SCAN PLAYGROUND")

    playground_scan(board)

    print(board.get_all_positions())

    wait_for_left_button("Enemy move")



# ============================================
#                  MAIN
# ============================================

def main():

    board = ReversiBoard()

    calibration()

    wait_for_left_button("Start Sequence")
    start_sequence()

    wait_for_left_button("Start Game")

    while True:
        reversi_turn(board)


run_task(main())