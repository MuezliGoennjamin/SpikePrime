## ============================================
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

    motor_x2.run_target(velocity_X2, 0, wait=True)
    motor_y2.run_target(velocity_Y2, 0, wait=True)
    motor_z2.run_target(velocity_Z2, 180, wait=True)


def X2_relative(distance):

    motor_x2.run_angle(
        velocity_X2,
        distance * 5,
        wait=True
    )


def Y2_relative(distance):

    motor_y2.run_angle(
        velocity_Y2,
        -distance * 5,
        wait=True
    )


def Z2_tap():

    motor_z2.run_target(velocity_Z2, 110, wait=True)
    wait(300)
    motor_z2.run_target(velocity_Z2, 180, wait=True)
    wait(300)

# ============================================
#             REVERSI BOARD
# ============================================

class ReversiBoard:

    def __init__(self):

        self.board = []

        for _ in range(8):
            self.board.append([0] * 8)

    def _parse_position(self, position):

        col = ord(position[0].upper()) - ord('A')
        row = int(position[1]) - 1

        return row, col

    def set(self, position, value):

        row, col = self._parse_position(position)
        self.board[row][col] = value

    def get(self, position):

        row, col = self._parse_position(position)
        return self.board[row][col]

    def get_all_positions(self):

        result = []

        for r in range(8):
            for c in range(8):

                pos = chr(ord('A') + c) + str(r + 1)
                result.append((pos, self.board[r][c]))

        return result

# ============================================
#               FIELD SCAN
# ============================================

def field_scan(position, board):

    wait(500)

    detected = color_sensor.color()

    if detected == Color.GREEN:
        board.set(position, 0)

    elif detected == Color.WHITE:
        board.set(position, 1)

    elif detected == Color.BLACK:
        board.set(position, 2)

# ============================================
#              REVERSI AI
# ============================================

DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1)
]

def is_on_board(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def indices_to_position(r, c):
    return chr(ord('A') + c) + str(r + 1)


def get_flippable_tokens(board, position, player):

    opponent = ENEMY_COLOR if player == ROBOT_COLOR else ROBOT_COLOR
    row, col = board._parse_position(position)

    if board.board[row][col] != 0:
        return []

    flips = []

    for dr, dc in DIRECTIONS:

        r, c = row + dr, col + dc
        temp = []

        while is_on_board(r, c):

            val = board.board[r][c]

            if val == opponent:
                temp.append((r, c))

            elif val == player:
                flips.extend(temp)
                break

            else:
                break

            r += dr
            c += dc

    return flips


def get_valid_moves(board, player):

    moves = []

    for r in range(8):
        for c in range(8):

            pos = indices_to_position(r, c)

            flips = get_flippable_tokens(board, pos, player)

            if flips:
                moves.append((pos, len(flips)))

    return moves


def evaluate_move(position, flips):

    score = flips

    if position in ["A1", "A8", "H1", "H8"]:
        score += 100

    elif position[0] in ["A", "H"] or position[1] in ["1", "8"]:
        score += 20

    elif position in [
        "B1","A2","B2",
        "G1","H2","G2",
        "A7","B7","B8",
        "G7","G8","H7"
    ]:
        score -= 25

    return score


def get_best_move(board, player):

    moves = get_valid_moves(board, player)

    if not moves:
        return None

    best = None
    best_score = -9999

    for pos, flips in moves:

        score = evaluate_move(pos, flips)

        if score > best_score:
            best_score = score
            best = pos

    return best


def apply_move(board, position, player):

    flips = get_flippable_tokens(board, position, player)

    board.set(position, player)

    for r, c in flips:
        board.set(indices_to_position(r, c), player)

# ============================================
#            ROBOT MOVEMENT
# ============================================

def move_to_position(position):

    row = int(position[1])
    col = ord(position[0]) - ord('A')

    x_distance = (8 - row) * 18
    y_distance = col * 20

    default_position()

    wait_for_left_button("Vor Bewegung")

    X2_relative(18 + x_distance)
    Y2_relative(20 + y_distance)

    wait_for_left_button("Z Tap")

    Z2_tap()

    wait_for_left_button("Return")

    default_position()

# ============================================
#              START SEQUENCE
# ============================================

def start_sequence():

    print("START SEQUENCE")

    motor_x1.run(velocity_X1)

    while distance_sensor.distance() > 110:
        wait(10)

    motor_x1.run_angle(
        velocity_X1,
        10,
        wait=True,
        then=Stop.HOLD
    )

    print("START SEQUENCE END")

# ============================================
#               CALIBRATION
# ============================================

def calibration():

    print("Drücke linken Button zum Kalibrieren")

    while Button.LEFT not in hub.buttons.pressed():
        wait(10)

    print("CALIBRATION START")

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

    print("CALIBRATION END")

# ============================================
#               MAIN
# ============================================

def main():

    board = ReversiBoard()

    calibration()

    wait_for_left_button("Start Sequence")
    start_sequence()

    wait_for_left_button("Start Game")

    while True:

        # hier bleibt dein Game Loop (unverändert)
        pass


main()