from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Port, Button
from pybricks.tools import wait

# Programm auf kleines Feld abgestimmt

# Hub Anschluss: Motor X1 = Port A, Motor X2 = Port C, Motor Y2 = Port F, Motor Z2 = Port B, Color Sensor = Port D

hub = PrimeHub()

# global variables
velocity_X1 = 150
velocity_X2 = 90
velocity_Y2 = 100
velocity_Z2 = 50

motor_X1 = Motor(Port.A)
motor_X2 = Motor(Port.C)
motor_Y2 = Motor(Port.F)
motor_Z2 = Motor(Port.B)
color_sensor = ColorSensor(Port.D)
color_sensor.lights.on(0)

move_distance_x = 85   # [Grad] Abstand von Zeile zu Zeile
move_distance_y = 85   # [Grad] Abstand von Spalte zu Spalte


######################################################
#                    Functions                       #
######################################################

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


# sets the default position of the Coordinate System
def default_position():
    motor_X2.run_target(velocity_X2, 0)
    motor_Y2.run_target(velocity_Y2, 0)
    motor_Z2.run_target(velocity_Z2, 180)


# defines the moving distance of the Motors
def X2_relative(distance):    # [degrees]
    motor_X2.run_angle(velocity_X2, distance)


def Y2_relative(distance):    # [degrees]
    motor_Y2.run_angle(velocity_Y2, -distance)


# tap on the touchscreen to place the token
def Z2_tap():

    # press down
    motor_Z2.run_target(velocity_Z2, 180)

    # short press time
    wait(300)

    # move back up
    motor_Z2.run_target(velocity_Z2, 140)

    # wait for stable end position
    wait(300)


# HSV ranges: (h_lo, h_hi, s_lo, s_hi, v_lo, v_hi)
# 0 = green (empty), 1 = white, 2 = black
_HSV_RANGES = {
    0: (135, 136, 61, 62,  26,  27),
    1: (194, 208, 21, 35,  71, 100),
    2: (153, 193, 39, 49,   8,  15),
}
_TOLERANCE = 0.05


def _in_range(value, low, high):
    return low * (1 - _TOLERANCE) <= value <= high * (1 + _TOLERANCE)


# scan field for white or black token and save the data of the field
def field_scan(position, board):

    wait(500)

    hsv = color_sensor.hsv(surface=False)
    h, s, v = hsv.h, hsv.s, hsv.v

    for color_value, (h_lo, h_hi, s_lo, s_hi, v_lo, v_hi) in _HSV_RANGES.items():
        if _in_range(h, h_lo, h_hi) and _in_range(s, s_lo, s_hi) and _in_range(v, v_lo, v_hi):
            board.set(position, color_value)
            return


# ============================================
# Reversi Board - Game Field Management
# ============================================

class ReversiBoard:

    """Manages the 8x8 Reversi game board"""

    def __init__(self):
        # Create empty 8x8 board (0 = empty)
        self.board = []
        for row in range(8):
            new_row = []
            for col in range(8):
                new_row.append(0)  # 0 means empty field
            self.board.append(new_row)

    def _parse_position(self, position):
        """Converts string position (e.g. 'D4') to array indices

        Example: 'D4' means column D (4th column) and row 4
        - Column 'A' = 0, 'B' = 1, 'C' = 2, 'D' = 3, etc.
        - Row 1 = 0, 2 = 1, 3 = 2, 4 = 3, etc.
        """
        # Get column letter and convert to number (A=0, B=1, ...)
        column_letter = position[0].upper()
        column_number = ord(column_letter) - ord('A')

        # Get row number and convert to array index (1=0, 2=1, ...)
        row_number = int(position[1])
        row_index = row_number - 1

        return row_index, column_number

    def set(self, position, value):
        """Sets a game piece at the given position

        position: String like 'D4', 'E5', etc.
        value: Number representing the piece (0=green, 1=white, 2=black)
        """
        row, col = self._parse_position(position)
        self.board[row][col] = value

    def get(self, position):
        """Returns the value at a position

        position: String like 'D4', 'E5', etc.
        Returns: The value at that position (0 = green, 1 = white, 2 = black)
        """
        row, col = self._parse_position(position)
        return self.board[row][col]

    def get_all_positions(self):
        """Returns a list of all positions with their values

        Returns: List of tuples like [('A1', 0), ('B1', 0), ...]
        """
        all_positions = []

        # Go through each row
        for row in range(8):
            # Go through each column
            for col in range(8):
                # Build position string like 'A1', 'B2', etc.
                column_letter = chr(ord('A') + col)
                row_number = str(row + 1)
                position = column_letter + row_number

                # Get the value at this position
                value = self.board[row][col]

                # Add to list
                all_positions.append((position, value))

        return all_positions

    def get_neighbors(self, position):
        """Returns all neighbors of a position (up to 8 neighbors)

        position: String like 'D4'
        Returns: List of tuples like [('C3', 0), ('C4', 1), ...]

        A field can have up to 8 neighbors:
        - Top-left, top, top-right
        - Left, right
        - Bottom-left, bottom, bottom-right
        """
        row, col = self._parse_position(position)
        neighbors = []

        # All 8 possible directions to check
        # (row_change, column_change)
        all_directions = [
            (-1, -1),  # Top-left
            (-1,  0),  # Top
            (-1,  1),  # Top-right
            ( 0, -1),  # Left
            ( 0,  1),  # Right
            ( 1, -1),  # Bottom-left
            ( 1,  0),  # Bottom
            ( 1,  1)   # Bottom-right
        ]

        # Check each direction
        for row_change, col_change in all_directions:
            # Calculate new position
            new_row = row + row_change
            new_col = col + col_change

            # Check if new position is still on the board (0-7)
            if new_row >= 0 and new_row < 8 and new_col >= 0 and new_col < 8:
                # Build position string
                column_letter = chr(ord('A') + new_col)
                row_number = str(new_row + 1)
                neighbor_position = column_letter + row_number

                # Get value at neighbor position
                neighbor_value = self.board[new_row][new_col]

                # Add to neighbors list
                neighbors.append((neighbor_position, neighbor_value))

        return neighbors


# ============================================
#              REVERSI AI
# ============================================
# directions for checking fields
DIRECTIONS = [
    (-1, -1),
    (-1,  0),
    (-1,  1),
    ( 0, -1),
    ( 0,  1),
    ( 1, -1),
    ( 1,  0),
    ( 1,  1)
]

ROBOT_COLOR = 2      # black
ENEMY_COLOR = 1      # white


def is_on_board(row, col):
    return row >= 0 and row < 8 and col >= 0 and col < 8


def indices_to_position(row, col):
    column_letter = chr(ord('A') + col)
    row_number = str(row + 1)
    return column_letter + row_number


def get_flippable_tokens(board, position, player):

    opponent = ENEMY_COLOR if player == ROBOT_COLOR else ROBOT_COLOR

    row, col = board._parse_position(position)

    # field already occupied
    if board.board[row][col] != 0:
        return []

    flippable = []

    # check all directions
    for row_dir, col_dir in DIRECTIONS:

        current_row = row + row_dir
        current_col = col + col_dir

        direction_tokens = []

        while is_on_board(current_row, current_col):

            current_value = board.board[current_row][current_col]

            # opponent token
            if current_value == opponent:
                direction_tokens.append((current_row, current_col))

            # own token -> valid direction
            elif current_value == player:
                if len(direction_tokens) > 0:
                    flippable.extend(direction_tokens)
                break

            # empty field
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
            flippable = get_flippable_tokens(board, position, player)
            if len(flippable) > 0:
                valid_moves.append((position, len(flippable)))

    return valid_moves


MINIMAX_DEPTH = 3


def evaluate_board(board):

    score = 0

    for row in range(8):
        for col in range(8):
            val = board.board[row][col]
            if val == 0:
                continue
            pos = indices_to_position(row, col)
            if pos in ["A1", "A8", "H1", "H8"]:
                weight = 100
            elif pos in ["B1", "A2", "B2", "G1", "H2", "G2", "A7", "B7", "B8", "G7", "G8", "H7"]:
                weight = -25
            elif pos[0] in "AH" or pos[1] in "18":
                weight = 20
            else:
                weight = 1
            if val == ROBOT_COLOR:
                score += weight
            else:
                score -= weight

    return score


def copy_board_state(board):
    return [row[:] for row in board.board]


def restore_board_state(board, state):
    for i in range(8):
        board.board[i] = state[i][:]


def minimax(board, depth, maximizing, alpha, beta):

    player = ROBOT_COLOR if maximizing else ENEMY_COLOR
    valid_moves = get_valid_moves(board, player)

    if depth == 0 or len(valid_moves) == 0:
        return evaluate_board(board), None

    best_move = None

    if maximizing:
        best_val = -9999
        for position, _ in valid_moves:
            saved = copy_board_state(board)
            apply_move(board, position, player)
            val, _ = minimax(board, depth - 1, False, alpha, beta)
            restore_board_state(board, saved)
            if val > best_val:
                best_val = val
                best_move = position
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return best_val, best_move

    else:
        best_val = 9999
        for position, _ in valid_moves:
            saved = copy_board_state(board)
            apply_move(board, position, player)
            val, _ = minimax(board, depth - 1, True, alpha, beta)
            restore_board_state(board, saved)
            if val < best_val:
                best_val = val
                best_move = position
            beta = min(beta, val)
            if beta <= alpha:
                break
        return best_val, best_move


def get_best_move(board, _):
    _, best_move = minimax(board, MINIMAX_DEPTH, True, -9999, 9999)
    return best_move


def apply_move(board, position, player):

    flippable = get_flippable_tokens(board, position, player)

    # place token
    board.set(position, player)

    # flip enemy tokens
    for row, col in flippable:
        flip_position = indices_to_position(row, col)
        board.set(flip_position, player)


# ============================================
#              DEBUG HELPERS
# ============================================

def print_board_debug(board):
    print("  A B C D E F G H")
    for row in range(8, 0, -1):
        line = str(row) + " "
        for col in range(8):
            val = board.board[row - 1][col]
            if val == 0:
                line += ". "
            elif val == ENEMY_COLOR:
                line += "W "
            elif val == ROBOT_COLOR:
                line += "B "
            else:
                line += "? "
        print(line)


def validate_start_position(board):
    """Prüft ob die 4 Anfangssteine korrekt erkannt wurden (D4/E4/D5/E5)."""
    start_fields = ["D4", "E4", "D5", "E5"]
    white = sum(1 for p in start_fields if board.get(p) == ENEMY_COLOR)
    black = sum(1 for p in start_fields if board.get(p) == ROBOT_COLOR)
    empty = sum(1 for p in start_fields if board.get(p) == 0)
    total = sum(1 for _, v in board.get_all_positions() if v != 0)

    print("STARTCHECK: W=" + str(white) + " S=" + str(black) + " LEER=" + str(empty))
    print("STEINE GESAMT: " + str(total))

    if total == 0:
        print("!!! FEHLER: Keine Steine erkannt!")
        print("!!! Roboter ist moeglicherweise nicht ueber dem Spielfeld")
        print("!!! oder Farbsensor ist falsch kalibriert (Port pruefen)")
        return False

    if empty > 0:
        print("!!! WARNUNG: " + str(empty) + " Anfangssteine in D4/E4/D5/E5 nicht erkannt!")
        print("!!! Prüfe: Liegt der Sensor korrekt ueber den Mittelfeldern?")
        print("!!! Prüfe: Stimmen die X/Y-Abstände (18mm / 20mm) fuer dein Feld?")
        return False

    if white != 2 or black != 2:
        print("!!! WARNUNG: Unerwartete Startaufstellung erkannt!")
        print("!!! Erwartet: 2 Weiss + 2 Schwarz in D4/E4/D5/E5")
        print("!!! Erkannt:  W=" + str(white) + " S=" + str(black))
        return False

    print("STARTPOSITION OK")
    return True


# ============================================
#          ROBOT MOVEMENT
# ============================================

def move_to_position(position):

    # convert position
    row = int(position[1])
    col = ord(position[0]) - ord('A')

    # movement values
    # A8 corresponds to:
    # X = 17 mm
    # Y = 18 mm

    x_distance = (8 - row) * move_distance_x
    y_distance = col * move_distance_y

    # move from default position
    default_position()

    # move to target field
    X2_relative(move_distance_x + x_distance)
    Y2_relative(move_distance_y + y_distance)

    # short pause before tap
    wait(500)

    # execute move on touchscreen
    Z2_tap()

    # short wait after tap
    wait(500)

    # move back to default position
    default_position()


# function to calibrate actors
def calibration():
    print("Drücke linken Button zum Kalibrieren")

    while Button.LEFT not in hub.buttons.pressed():
        wait(10)

    default_position()
    print("Kalibriert")
    print(motor_X2.angle(), motor_Y2.angle(), motor_Z2.angle())


#### main program ####

def main():

    # creates the playground
    board = ReversiBoard()

    ######################################################
    #                    Playground Scan                 #
    ######################################################
    # scans each field on the playground for black and white tokens
    def playground_scan():

        default_position()
        wait_for_left_button()

        going_down = True   # True = Zeile 8→1 (+X), False = Zeile 1→8 (-X)

        for col_idx in range(8):
            col_letter = chr(ord('A') + col_idx)

            if going_down:
                for row in range(8, 0, -1):
                    field_scan(col_letter + str(row), board)
                    if row > 1:
                        X2_relative(move_distance_x)
            else:
                for row in range(1, 9):
                    field_scan(col_letter + str(row), board)
                    if row < 8:
                        X2_relative(-move_distance_x)

            if col_idx < 7:
                Y2_relative(move_distance_y)
                going_down = not going_down

    ######################################################
    #                 REVERSI GAME LOOP                  #
    ######################################################

    def reversi_turn():

        print("========== NEUER ZUG ==========")
        print("SCAN PLAYGROUND")

        playground_scan()

        print("--- SPIELFELD NACH SCAN ---")
        print_board_debug(board)
        white = sum(1 for _, v in board.get_all_positions() if v == ENEMY_COLOR)
        black = sum(1 for _, v in board.get_all_positions() if v == ROBOT_COLOR)
        print("Weiss (W):", white, "  Schwarz (B):", black)

        # calculate best move
        print("BERECHNE BESTEN ZUG (Tiefe=" + str(MINIMAX_DEPTH) + ")...")
        best_move = get_best_move(board, ROBOT_COLOR)

        if best_move is None:
            print("KEIN GUELTIGER ZUG MOEGLICH - Zug wird uebersprungen")
            return

        print("BESTER ZUG:", best_move)

        # move robot
        print("BEWEGE ROBOTER ZU:", best_move)
        move_to_position(best_move)

        # update board
        apply_move(board, best_move, ROBOT_COLOR)

        print("--- SPIELFELD NACH ROBOTERZUG ---")
        print_board_debug(board)
        white = sum(1 for _, v in board.get_all_positions() if v == ENEMY_COLOR)
        black = sum(1 for _, v in board.get_all_positions() if v == ROBOT_COLOR)
        print("Weiss (W):", white, "  Schwarz (B):", black)

        # wait for enemy move
        wait_for_left_button("Gegner hat Zug ausgeführt")

    calibration()
    wait_for_left_button()
    wait_for_left_button()

    # Pre-Game: Startposition einmalig scannen und prüfen
    print("PRE-GAME: SCAN STARTPOSITION")
    playground_scan()
    print_board_debug(board)
    start_ok = validate_start_position(board)
    if not start_ok:
        wait_for_left_button("Startposition pruefen, dann fortfahren")

    while True:
        reversi_turn()


main()
