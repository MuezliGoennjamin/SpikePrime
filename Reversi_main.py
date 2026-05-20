from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor, UltrasonicSensor
from pybricks.parameters import Port, Color, Button, Stop
from pybricks.tools import wait

# ============================================
# HUB + DEVICES
# ============================================

hub = PrimeHub()

motor_x1 = Motor(Port.A)
motor_x2 = Motor(Port.C)
motor_y2 = Motor(Port.F)
motor_z2 = Motor(Port.B)

distance_sensor = UltrasonicSensor(Port.E)
color_sensor = ColorSensor(Port.D)

# ============================================
# GLOBALS
# ============================================

velocity_X1 = 150
velocity_X2 = 90
velocity_Y2 = 100
velocity_Z2 = 50

ROBOT_COLOR = 2
ENEMY_COLOR = 1

# ============================================
# BUTTON
# ============================================

def wait_for_left_button(step=""):
    print("--------------------------------")

    if step:
        print("WAIT:", step)
    else:
        print("WAIT FOR LEFT BUTTON")

    while Button.LEFT not in hub.buttons.pressed():
        wait(100)

    print("BUTTON PRESSED")
    print("--------------------------------")


# ============================================
# MOTORS
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
# FIELD SCAN
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
# BOARD
# ============================================

class ReversiBoard:

    def __init__(self):
        self.board = [[0 for _ in range(8)] for _ in range(8)]

    def _parse_position(self, position):
        col = ord(position[0].upper()) - ord('A')
        row = int(position[1]) - 1
        return row, col

    def set(self, position, value):
        r, c = self._parse_position(position)
        self.board[r][c] = value

    def get(self, position):
        r, c = self._parse_position(position)
        return self.board[r][c]


# ============================================
# AI CORE
# ============================================

DIRECTIONS = [
    (-1,-1), (-1,0), (-1,1),
    (0,-1),          (0,1),
    (1,-1),  (1,0),  (1,1)
]


def is_on_board(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def indices_to_position(r, c):
    return chr(ord('A') + c) + str(r + 1)


def get_flippable_tokens(board, position, player):

    opponent = ENEMY_COLOR if player == ROBOT_COLOR else ROBOT_COLOR

    r, c = board._parse_position(position)

    if board.board[r][c] != 0:
        return []

    flips = []

    for dr, dc in DIRECTIONS:

        rr, cc = r + dr, c + dc
        line = []

        while is_on_board(rr, cc):

            v = board.board[rr][cc]

            if v == opponent:
                line.append((rr, cc))

            elif v == player:
                if line:
                    flips.extend(line)
                break
            else:
                break

            rr += dr
            cc += dc

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

    if position in ["A1","A8","H1","H8"]:
        score += 100

    elif position[0] in ["A","H"] or position[1] in ["1","8"]:
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
        board.board[r][c] = player


# ============================================
# ROBOT MOVE
# ============================================

def move_to_position(position):

    r = int(position[1])
    c = ord(position[0]) - ord('A')

    x = (8 - r) * 18
    y = c * 20

    default_position()

    X2_relative(18 + x)
    Y2_relative(20 + y)

    wait(500)

    Z2_tap()

    wait(500)

    default_position()


# ============================================
# START
# ============================================

def start_sequence():

    motor_x1.run(velocity_X1)

    while True:
        d = distance_sensor.distance()

        if d <= 110:
            break

        wait(10)

    motor_x1.run_time(velocity_X1, 10, then=Stop.HOLD, wait=True)


# ============================================
# CALIBRATION
# ============================================

def calibration():

    print("Drücke linken Button zum Kalibrieren")

    while Button.LEFT not in hub.buttons.pressed():
        wait(10)

    default_position()

    print("Kalibriert")


# ============================================
# SCAN
# ============================================

def playground_scan(board):

    row = 8
    col = 65

    default_position()

    wait_for_left_button("Scan Start")

    X2_relative(18)
    Y2_relative(20)

    field_scan("A8", board)

    while col <= 72:

        if row == 8:
            row = 7

            while row >= 1:
                pos = chr(col) + str(row)

                X2_relative(18)
                field_scan(pos, board)

                row -= 1

        else:

            while row <= 8:
                pos = chr(col) + str(row)

                X2_relative(-18)
                field_scan(pos, board)

                row += 1

        if row == 0:
            row = 1
        elif row == 9:
            row = 8

        col += 1

        if col > 72:
            break

        Y2_relative(20)

        pos = chr(col) + str(row)
        field_scan(pos, board)

        if col % 2 == 0:
            row += 1


# ============================================
# TURN
# ============================================

def reversi_turn(board):

    print("SCAN")

    playground_scan(board)

    move = get_best_move(board, ROBOT_COLOR)

    if move is None:
        print("NO MOVE")
        return

    print("BEST MOVE:", move)

    move_to_position(move)

    apply_move(board, move, ROBOT_COLOR)

    wait_for_left_button("Enemy done")


# ============================================
# MAIN
# ============================================

def main():

    board = ReversiBoard()

    calibration()

    wait_for_left_button("Start Sequence")
    start_sequence()

    wait_for_left_button("Start Game")

    while True:
        reversi_turn(board)


main()