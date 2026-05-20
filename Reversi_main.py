# ============================================
#              PYBRICKS VERSION
# ============================================

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor, UltrasonicSensor
from pybricks.parameters import Port, Color, Button, Stop
from pybricks.tools import wait

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

ROBOT_COLOR = 2
ENEMY_COLOR = 1

# ============================================
#                    DEBUG
# ============================================

DEBUG = True

def debug(text):

    if DEBUG:
        print("[DEBUG]", text)

# ============================================
#               WAIT FOR BUTTON
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

    wait(300)

# ============================================
#               MOTOR FUNCTIONS
# ============================================

def default_position():

    debug("DEFAULT POSITION")

    motor_x2.run_target(
        velocity_X2,
        0,
        wait=True
    )

    motor_y2.run_target(
        velocity_Y2,
        0,
        wait=True
    )

    motor_z2.run_target(
        velocity_Z2,
        180,
        wait=True
    )

    debug("DEFAULT POSITION FINISHED")


def X2_relative(distance):

    debug("X2 MOVE")
    debug("distance = " + str(distance))

    motor_x2.run_angle(
        velocity_X2,
        distance * 5,
        wait=True
    )

    debug("X2 MOVE FINISHED")


def Y2_relative(distance):

    debug("Y2 MOVE")
    debug("distance = " + str(distance))

    motor_y2.run_angle(
        velocity_Y2,
        -distance * 5,
        wait=True
    )

    debug("Y2 MOVE FINISHED")


def Z2_tap():

    debug("Z2 TAP START")

    motor_z2.run_target(
        velocity_Z2,
        110,
        wait=True
    )

    wait(300)

    motor_z2.run_target(
        velocity_Z2,
        180,
        wait=True
    )

    wait(300)

    debug("Z2 TAP END")

# ============================================
#             REVERSI BOARD
# ============================================

class ReversiBoard:

    def __init__(self):

        debug("CREATE BOARD")

        self.board = []

        for row in range(8):

            new_row = []

            for col in range(8):
                new_row.append(0)

            self.board.append(new_row)

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

        return self.board[row][col]

    def get_all_positions(self):

        all_positions = []

        for row in range(8):

            for col in range(8):

                column_letter = chr(ord('A') + col)
                row_number = str(row + 1)

                position = column_letter + row_number

                value = self.board[row][col]

                all_positions.append((position, value))

        return all_positions

# ============================================
#               FIELD SCAN
# ============================================

def field_scan(position, board):

    debug("SCAN FIELD -> " + position)

    wait(500)

    detected_color = color_sensor.color()

    debug("Detected Color = " + str(detected_color))

    if detected_color == Color.GREEN:

        board.set(position, 0)

        debug(position + " = GREEN")

    elif detected_color == Color.WHITE:

        board.set(position, 1)

        debug(position + " = WHITE")

    elif detected_color == Color.BLACK:

        board.set(position, 2)

        debug(position + " = BLACK")

    else:

        debug(position + " = UNKNOWN")

# ============================================
#              REVERSI AI
# ============================================

DIRECTIONS = [
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1)
]


def is_on_board(row, col):

    return row >= 0 and row < 8 and col >= 0 and col < 8


def indices_to_position(row, col):

    column_letter = chr(ord('A') + col)
    row_number = str(row + 1)

    return column_letter + row_number


def get_flippable_tokens(board, position, player):

    opponent = ENEMY_COLOR if player == ROBOT_COLOR else ROBOT_COLOR

    row, col = board._parse_position(position)

    if board.board[row][col] != 0:
        return []

    flippable = []

    for row_dir, col_dir in DIRECTIONS:

        current_row = row + row_dir
        current_col = col + col_dir

        direction_tokens = []

        while is_on_board(current_row, current_col):

            current_value = board.board[current_row][current_col]

            if current_value == opponent:

                direction_tokens.append(
                    (current_row, current_col)
                )

            elif current_value == player:

                if len(direction_tokens) > 0:
                    flippable.extend(direction_tokens)

                break

            else:
                break

            current_row += row_dir
            current_col += col_dir

    return flippable


def get_valid_moves(board, player):

    valid_moves = []

    for row in range(8):

        for col in range(8):

            position = indices_to_position(row, col)

            flippable = get_flippable_tokens(
                board,
                position,
                player
            )

            if len(flippable) > 0:

                valid_moves.append(
                    (position, len(flippable))
                )

    return valid_moves


def evaluate_move(position, flips):

    score = flips

    if position in ["A1", "A8", "H1", "H8"]:
        score += 100

    elif (
        position[0] in ["A", "H"]
        or
        position[1] in ["1", "8"]
    ):
        score += 20

    elif position in [
        "B1", "A2", "B2",
        "G1", "H2", "G2",
        "A7", "B7", "B8",
        "G7", "G8", "H7"
    ]:
        score -= 25

    return score


def get_best_move(board, player):

    valid_moves = get_valid_moves(board, player)

    if len(valid_moves) == 0:
        return None

    best_move = None
    best_score = -9999

    for position, flips in valid_moves:

        score = evaluate_move(position, flips)

        debug("MOVE " + position + " SCORE = " + str(score))

        if score > best_score:

            best_score = score
            best_move = position

    return best_move


def apply_move(board, position, player):

    flippable = get_flippable_tokens(
        board,
        position,
        player
    )

    board.set(position, player)

    for row, col in flippable:

        flip_position = indices_to_position(row, col)

        board.set(flip_position, player)

# ============================================
#            ROBOT MOVEMENT
# ============================================

def move_to_position(position):

    debug("MOVE TO POSITION -> " + position)

    row = int(position[1])
    col = ord(position[0]) - ord('A')

    x_distance = (8 - row) * 18
    y_distance = col * 20

    debug("x_distance = " + str(x_distance))
    debug("y_distance = " + str(y_distance))

    default_position()

    wait_for_left_button(
        "Vor Bewegung zu " + position
    )

    X2_relative(18 + x_distance)
    Y2_relative(20 + y_distance)

    debug("TARGET POSITION REACHED")

    wait_for_left_button(
        "Vor Z2 Tap"
    )

    Z2_tap()

    debug("MOVE EXECUTED")

    wait_for_left_button(
        "Vor Rückfahrt Default Position"
    )

    default_position()

# ============================================
#              START SEQUENCE
# ============================================

def start_sequence():

    debug("START SEQUENCE")

    motor_x1.run(velocity_X1)

    while True:

        distance = distance_sensor.distance()

        debug("Distance = " + str(distance))

        if distance <= 110:
            break

        wait(10)

    motor_x1.run_angle(
        velocity_X1,
        10,
        then=Stop.HOLD,
        wait=True
    )

    debug("START SEQUENCE END")

# ============================================
#               CALIBRATION
# ============================================

def calibration():

    print("Drücke linken Button zum Kalibrieren")

    while Button.LEFT not in hub.buttons.pressed():
        wait(10)

    debug("CALIBRATION START")

    motor_x2.reset_angle(0)
    motor_y2.reset_angle(0)
    motor_z2.reset_angle(180)

    default_position()

    print("Kalibriert")

    print(
        motor_x2.angle(),
        motor_y2.angle(),
        motor_z2.angle()
    )

    debug("CALIBRATION END")

# ============================================
#            PLAYGROUND SCAN
# ============================================

def playground_scan(board):

    debug("PLAYGROUND SCAN START")

    row = 8
    column = 65

    default_position()

    wait_for_left_button(
        "Default Position erreicht"
    )

    X2_relative(18)
    Y2_relative(20)

    debug("Moved to A8")

    wait_for_left_button(
        "Vor erstem Feldscan"
    )

    field_scan("A8", board)

    while column <= 72:

        debug("--------------------------------")
        debug("COLUMN = " + chr(column))
        debug("ROW = " + str(row))

        if row == 8:

            row = 7

            while row >= 1:

                position = chr(column) + str(row)

                wait_for_left_button(
                    "Vor Bewegung zu " + position
                )

                X2_relative(18)

                field_scan(position, board)

                row -= 1

        else:

            while row <= 8:

                position = chr(column) + str(row)

                wait_for_left_button(
                    "Vor Bewegung zu " + position
                )

                X2_relative(-18)

                field_scan(position, board)

                row += 1

        if row == 0:
            row = 1

        elif row == 9:
            row = 8

        column += 1

        if column > 72:

            debug("SCAN FINISHED")

            break

        debug("COLUMN TRANSITION")

        wait_for_left_button(
            "Vor nächster Column"
        )

        Y2_relative(20)

        position = chr(column) + str(row)

        field_scan(position, board)

        if column % 2 == 0:
            row += 1

    debug("PLAYGROUND SCAN END")

# ============================================
#               GAME TURN
# ============================================

def reversi_turn(board):

    print("SCAN PLAYGROUND")

    playground_scan(board)

    print(board.get_all_positions())

    best_move = get_best_move(
        board,
        ROBOT_COLOR
    )

    if best_move is None:

        print("NO VALID MOVE")

        return

    print("BEST MOVE:", best_move)

    move_to_position(best_move)

    apply_move(
        board,
        best_move,
        ROBOT_COLOR
    )

    print("BOARD UPDATED")

    print(board.get_all_positions())

    wait_for_left_button(
        "Gegner hat Zug ausgeführt"
    )

# ============================================
#                   MAIN
# ============================================

def main():

    debug("PROGRAM START")

    board = ReversiBoard()

    calibration()

    wait_for_left_button(
        "Vor Startsequenz"
    )

    start_sequence()

    wait_for_left_button(
        "Vor erstem Spielzug"
    )

    while True:

        reversi_turn(board)

main()