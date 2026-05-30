# ============================================
#   AUTO-DETECT: SPIKE PRIME vs PC DEBUG
#   Läuft auf dem PC ohne Hardware-Imports.
#   DEBUG_MODE wird automatisch gesetzt.
# ============================================

try:
    from pybricks.hubs import PrimeHub                  # type: ignore
    from pybricks.pupdevices import Motor, ColorSensor  # type: ignore
    from pybricks.parameters import Port, Color, Button # type: ignore
    from pybricks.tools import wait                     # type: ignore
    DEBUG_MODE = False

except ImportError:
    DEBUG_MODE = True
    import random

    # Mock-Spielbrett für den Scan-Sensor
    # Wird nach jedem Zug mit dem echten Board synchronisiert
    _mock_board = [[0] * 8 for _ in range(8)]
    _mock_board[3][3] = 1   # D4 = Weiss
    _mock_board[3][4] = 2   # E4 = Schwarz
    _mock_board[4][3] = 2   # D5 = Schwarz
    _mock_board[4][4] = 1   # E5 = Weiss

    class Color:
        GREEN = "GREEN"
        WHITE = "WHITE"
        BLACK = "BLACK"

    class Button:
        LEFT = "LEFT"

    class Port:
        A = B = C = D = E = F = None

    class _MockButtons:
        def pressed(self):
            return set()

    class _MockHub:
        def __init__(self):
            self.buttons = _MockButtons()

    class _MockMotor:
        def __init__(self, *_):
            pass
        def run_target(self, *_):
            pass
        def run_angle(self, *_):
            pass
        def angle(self):
            return 0

    class _MockColorSensor:
        def __init__(self, *_):
            pass
        def color(self):
            return None

    def wait(*_):
        pass

    PrimeHub      = _MockHub
    Motor         = _MockMotor
    ColorSensor   = _MockColorSensor


# global variables
velocity_X1 = 150
velocity_X2 = 90
velocity_Y2 = 100
velocity_Z2 = 50

hub          = PrimeHub()
motor_X1     = Motor(Port.A)
motor_X2     = Motor(Port.C)
motor_Y2     = Motor(Port.F)
motor_Z2     = Motor(Port.B)
color_sensor = ColorSensor(Port.D)


######################################################
#                    Functions                       #
######################################################

def wait_for_left_button(step=""):
    print("--------------------------------")
    if step != "":
        print("WAIT:", step)
    else:
        print("WAIT FOR LEFT BUTTON")
    if not DEBUG_MODE:
        while Button.LEFT not in hub.buttons.pressed():
            wait(100)
    print("AUTO: OK" if DEBUG_MODE else "BUTTON PRESSED")
    print("--------------------------------")


def default_position():
    if not DEBUG_MODE:
        motor_X2.run_target(velocity_X2, 0)
        motor_Y2.run_target(velocity_Y2, 0)
        motor_Z2.run_target(velocity_Z2, 180)


def X2_relative(distance):
    if not DEBUG_MODE:
        motor_X2.run_angle(velocity_X2, distance * 5)


def Y2_relative(distance):
    if not DEBUG_MODE:
        motor_Y2.run_angle(velocity_Y2, -distance * 5)


def Z2_tap():
    if not DEBUG_MODE:
        motor_Z2.run_target(velocity_Z2, 180)
        wait(300)
        motor_Z2.run_target(velocity_Z2, 140)
        wait(300)


def field_scan(position, board):
    if DEBUG_MODE:
        r, c = board._parse_position(position)
        board.board[r][c] = _mock_board[r][c]
        return
    wait(500)
    detected_color = color_sensor.color()
    if detected_color == Color.GREEN:
        board.set(position, 0)
    elif detected_color == Color.WHITE:
        board.set(position, 1)
    elif detected_color == Color.BLACK:
        board.set(position, 2)


# ============================================
# Reversi Board - Game Field Management
# ============================================

class ReversiBoard:

    def __init__(self):
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
#              REVERSI AI
# ============================================

DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    ( 0, -1),           ( 0, 1),
    ( 1, -1), ( 1, 0), ( 1, 1)
]

ROBOT_COLOR = 2
ENEMY_COLOR = 1


def is_on_board(row, col):
    return 0 <= row < 8 and 0 <= col < 8


def indices_to_position(row, col):
    return chr(ord('A') + col) + str(row + 1)


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
                direction_tokens.append((current_row, current_col))
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
    board.set(position, player)
    for row, col in flippable:
        board.set(indices_to_position(row, col), player)


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
    row = int(position[1])
    col = ord(position[0]) - ord('A')
    x_distance = (8 - row) * 18
    y_distance = col * 20

    if DEBUG_MODE:
        print("  [MOVE] -> " + position +
              "  X=" + str(18 + x_distance) + "mm  Y=" + str(20 + y_distance) + "mm")
        return

    default_position()
    X2_relative(18 + x_distance)
    Y2_relative(20 + y_distance)
    wait(500)
    Z2_tap()
    wait(500)
    default_position()


def calibration():
    if DEBUG_MODE:
        print("[DEBUG] Kalibrierung übersprungen")
        return
    print("Drücke linken Button zum Kalibrieren")
    while Button.LEFT not in hub.buttons.pressed():
        wait(10)
    default_position()
    print("Kalibriert")
    print(motor_X2.angle(), motor_Y2.angle(), motor_Z2.angle())


#### main program ####

def main():

    board = ReversiBoard()

    ######################################################
    #                    Playground Scan                 #
    ######################################################

    def playground_scan():
        default_position()
        wait_for_left_button()
        X2_relative(18)
        Y2_relative(20)
        wait_for_left_button()

        going_down = True

        for col_idx in range(8):
            col_letter = chr(ord('A') + col_idx)

            if going_down:
                for row in range(8, 0, -1):
                    field_scan(col_letter + str(row), board)
                    if row > 1:
                        X2_relative(18)
            else:
                for row in range(1, 9):
                    field_scan(col_letter + str(row), board)
                    if row < 8:
                        X2_relative(-18)

            if col_idx < 7:
                Y2_relative(20)
                going_down = not going_down

    ######################################################
    #                 REVERSI GAME LOOP                  #
    ######################################################

    def reversi_turn(turn):

        print("========== ZUG " + str(turn) + " ==========")
        print("SCAN PLAYGROUND")
        playground_scan()

        print("--- SPIELFELD NACH SCAN ---")
        print_board_debug(board)
        white = sum(1 for _, v in board.get_all_positions() if v == ENEMY_COLOR)
        black = sum(1 for _, v in board.get_all_positions() if v == ROBOT_COLOR)
        print("Weiss (W):", white, "  Schwarz (B):", black)

        # Roboterzug
        print("BERECHNE BESTEN ZUG (Tiefe=" + str(MINIMAX_DEPTH) + ")...")
        best_move = get_best_move(board, ROBOT_COLOR)

        if best_move is None:
            print("ROBOTER: Kein gueltiger Zug - Runde uebersprungen")
        else:
            print("BESTER ZUG:", best_move)
            move_to_position(best_move)
            apply_move(board, best_move, ROBOT_COLOR)
            print("--- SPIELFELD NACH ROBOTERZUG ---")
            print_board_debug(board)
            white = sum(1 for _, v in board.get_all_positions() if v == ENEMY_COLOR)
            black = sum(1 for _, v in board.get_all_positions() if v == ROBOT_COLOR)
            print("Weiss (W):", white, "  Schwarz (B):", black)

        # Gegnerzug
        if DEBUG_MODE:
            for r in range(8):
                _mock_board[r] = board.board[r][:]

            enemy_moves = get_valid_moves(board, ENEMY_COLOR)
            if enemy_moves:
                enemy_pos, _ = random.choice(enemy_moves)
                apply_move(board, enemy_pos, ENEMY_COLOR)
                print("GEGNER (simuliert) spielt:", enemy_pos)
                print_board_debug(board)
                white = sum(1 for _, v in board.get_all_positions() if v == ENEMY_COLOR)
                black = sum(1 for _, v in board.get_all_positions() if v == ROBOT_COLOR)
                print("Weiss (W):", white, "  Schwarz (B):", black)
                for r in range(8):
                    _mock_board[r] = board.board[r][:]
            else:
                print("GEGNER: Kein gueltiger Zug - Runde uebersprungen")
        else:
            wait_for_left_button("Gegner hat Zug ausgeführt")

    # ---- Startup ----

    calibration()
    wait_for_left_button()
    wait_for_left_button()

    print("PRE-GAME: SCAN STARTPOSITION")
    playground_scan()
    print_board_debug(board)
    start_ok = validate_start_position(board)
    if not start_ok:
        wait_for_left_button("Startposition pruefen, dann fortfahren")

    # ---- Spielschleife ----

    turn = 0
    while True:
        if DEBUG_MODE:
            robot_can_move = len(get_valid_moves(board, ROBOT_COLOR)) > 0
            enemy_can_move = len(get_valid_moves(board, ENEMY_COLOR)) > 0
            if not robot_can_move and not enemy_can_move:
                white = sum(1 for _, v in board.get_all_positions() if v == ENEMY_COLOR)
                black = sum(1 for _, v in board.get_all_positions() if v == ROBOT_COLOR)
                print("========== SPIEL VORBEI ==========")
                print_board_debug(board)
                print("Weiss (W):", white, "  Schwarz (B):", black)
                if black > white:
                    print("ROBOTER GEWINNT! (" + str(black) + ":" + str(white) + ")")
                elif white > black:
                    print("GEGNER GEWINNT! (" + str(white) + ":" + str(black) + ")")
                else:
                    print("UNENTSCHIEDEN! (" + str(black) + ":" + str(white) + ")")
                break

        turn += 1
        reversi_turn(turn)


main()
