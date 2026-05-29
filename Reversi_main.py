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


###################################################### 
#                    Functions                       #
######################################################

async def wait_for_left_button(step=""):

    print("--------------------------------")

    if step != "":
        print("WAIT:", step)
    else:
        print("WAIT FOR LEFT BUTTON")

    while not button.pressed(button.LEFT):
        await runloop.sleep_ms(100)

    print("BUTTON PRESSED")
    print("--------------------------------")

# sets the default position of the Coordinate System
async def default_position():
   await motor.run_to_absolute_position(Motor_X2, 0, velocity_X2)
   await motor.run_to_absolute_position(Motor_Y2, 0, velocity_Y2)
   await motor.run_to_absolute_position(Motor_Z2, 180, velocity_Z2)

# defines the moving distance of the Motors
async def X2_relative(distance):    # [mm]


    await motor.run_for_degrees(
        Motor_X2,
        distance * 5,
        velocity_X2
    )

async def Y2_relative(distance):    # [mm]


    await motor.run_for_degrees(
        Motor_Y2,
        -distance * 5,
        velocity_Y2
    )

# tap on the touchscreen to place the token
async def Z2_tap():

    # press down
    await motor.run_to_absolute_position(
        Motor_Z2,
        180,
        velocity_Z2
    )

    # short press time
    await runloop.sleep_ms(300)

    # move back up
    await motor.run_to_absolute_position(
        Motor_Z2,
        140,
        velocity_Z2
    )

    # wait for stable end position
    await runloop.sleep_ms(300)

# scan field for white or black token and save the data of the field
async def field_scan(position, board):

    # wait a certain time to detect the color
    await runloop.sleep_ms(500)

    detected_color = color_sensor.color(port.D)

    if detected_color is color.GREEN:
        board.set(position, 0)

    elif detected_color is color.WHITE:
        board.set(position, 1)

    elif detected_color is color.BLACK:
        board.set(position, 2)
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
                new_row.append(0)# 0 means empty field
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
            (-1, -1),# Top-left
            (-1,0),# Top
            (-1,1),# Top-right
            ( 0, -1),# Left
            ( 0,1),# Right
            ( 1, -1),# Bottom-left
            ( 1,0),# Bottom
            ( 1,1)# Bottom-right
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
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1)
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

                direction_tokens.append(
                    (current_row, current_col)
                )

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

    flippable = get_flippable_tokens(
        board,
        position,
        player
    )

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

async def move_to_position(position):

    # convert position
    row = int(position[1])
    col = ord(position[0]) - ord('A')

    # movement values
    # A8 corresponds to:
    # X = 18 mm
    # Y = 20 mm

    x_distance = (8 - row) * 18
    y_distance = col * 20

    # move from default position
    await default_position()

    # move to target field
    await X2_relative(18 + x_distance)
    await Y2_relative(20 + y_distance)

    # short pause before tap
    await runloop.sleep_ms(500)

    # execute move on touchscreen
    await Z2_tap()

    # short wait after tap
    await runloop.sleep_ms(500)

    # move back to default position
    await default_position()



# function to calibrate actors
async def calibration():
    print("Drücke linken Button zum Kalibrieren")

    while not button.pressed(button.LEFT):
        await runloop.sleep_ms(10)

    await default_position()
    print("Kalibriert")
    print (motor.absolute_position(Motor_X2), motor.absolute_position(Motor_Y2), motor.absolute_position(Motor_Z2))


#### main programm ####

async def main():


    # creates the playground
    board = ReversiBoard()

    ######################################################
    #                    Playground Scan                 #
    ######################################################
    # scans each field on the playground for black and white tokens
    async def playground_scan():

        await default_position()
        await wait_for_left_button()
        await X2_relative(18)
        await Y2_relative(20)
        await wait_for_left_button()

        going_down = True   # True = Zeile 8→1 (+X), False = Zeile 1→8 (-X)

        for col_idx in range(8):
            col_letter = chr(ord('A') + col_idx)

            if going_down:
                for row in range(8, 0, -1):
                    await field_scan(col_letter + str(row), board)
                    if row > 1:
                        await X2_relative(18)
            else:
                for row in range(1, 9):
                    await field_scan(col_letter + str(row), board)
                    if row < 8:
                        await X2_relative(-18)

            if col_idx < 7:
                await Y2_relative(20)
                going_down = not going_down
    
    ######################################################
    #                 REVERSI GAME LOOP                  #
    ######################################################

    async def reversi_turn():

        print("========== NEUER ZUG ==========")
        print("SCAN PLAYGROUND")

        await playground_scan()

        print("--- SPIELFELD NACH SCAN ---")
        print_board_debug(board)
        white = sum(1 for _, v in board.get_all_positions() if v == ENEMY_COLOR)
        black = sum(1 for _, v in board.get_all_positions() if v == ROBOT_COLOR)
        print("Weiss (W):", white, "  Schwarz (B):", black)

        # calculate best move
        print("BERECHNE BESTEN ZUG (Tiefe=" + str(MINIMAX_DEPTH) + ")...")
        best_move = get_best_move(
            board,
            ROBOT_COLOR
        )

        if best_move is None:
            print("KEIN GUELTIGER ZUG MOEGLICH - Zug wird uebersprungen")
            return

        print("BESTER ZUG:", best_move)

        # move robot
        print("BEWEGE ROBOTER ZU:", best_move)
        await move_to_position(best_move)

        # update board
        apply_move(
            board,
            best_move,
            ROBOT_COLOR
        )

        print("--- SPIELFELD NACH ROBOTERZUG ---")
        print_board_debug(board)
        white = sum(1 for _, v in board.get_all_positions() if v == ENEMY_COLOR)
        black = sum(1 for _, v in board.get_all_positions() if v == ROBOT_COLOR)
        print("Weiss (W):", white, "  Schwarz (B):", black)

        # wait for enemy move
        await wait_for_left_button(
            "Gegner hat Zug ausgeführt"
        )

    await calibration()
    await wait_for_left_button()
    await wait_for_left_button()

    # Pre-Game: Startposition einmalig scannen und prüfen
    print("PRE-GAME: SCAN STARTPOSITION")
    await playground_scan()
    print_board_debug(board)
    start_ok = validate_start_position(board)
    if not start_ok:
        await wait_for_left_button("Startposition pruefen, dann fortfahren")

    while True:

        await reversi_turn()

runloop.run(main())