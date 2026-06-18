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

move_distance_x = 83   # [Grad] Abstand von Zeile zu Zeile
move_distance_y = 87   # [Grad] Abstand von Spalte zu Spalte
pen_offset_y    =  70   # [Grad] Y-Versatz des Stifts hinter dem Farbsensor (TODO: kalibrieren)

# Anzeige-Position (Motorwinkel zur Uhr-Anzeige) – TODO: kalibrieren
INDICATOR_X2 = 700
INDICATOR_Y2 = 200


######################################################
#                    Functions                       #
######################################################

def wait_for_left_button(step=""):

    if step != "":
        print("Warte: " + step)
    else:
        print("Warte auf linken Button...")

    while Button.LEFT not in hub.buttons.pressed():
        wait(100)


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


def center_on_field():
    """Feinkorrektur nach Absolutpositionierung per run_target.
    Prueft ob der Sensor einen gueltigen Farbwert liest (gruen/weiss/schwarz).
    Falls nicht (Sensor auf einer Feldlinie), werden kleine Schritte in X
    und dann Y versucht bis ein gueltiger Wert gefunden wird.
    Die Korrektur gilt nur fuer die aktuelle Messung – die naechste
    run_target-Bewegung kehrt ohnehin zum absoluten Zielwinkel zurueck.
    """
    STEP  = 3    # [Grad] ~0.8 mm pro Korrekturschritt
    MAX_N = 3    # Suchweite: bis zu ±3 Schritte = ±2.6 mm

    def on_field():
        wait(100)
        hsv = color_sensor.hsv(surface=False)
        h, s, v = hsv.h, hsv.s, hsv.v
        for key in _HSV_RANGES:
            h_lo, h_hi, s_lo, s_hi, v_lo, v_hi = _HSV_RANGES[key]
            if (_in_range(h, h_lo, h_hi) and
                    _in_range(s, s_lo, s_hi) and
                    _in_range(v, v_lo, v_hi)):
                return True
        return False

    if on_field():
        return True

    # Kreuzsuche: zuerst X, dann Y – bei Erfolg Motor an korrigierter Position lassen
    for motor, vel in [(motor_X2, velocity_X2), (motor_Y2, velocity_Y2)]:
        offset = 0
        for n in range(1, MAX_N + 1):
            for sign in [1, -1]:
                target = STEP * n * sign
                motor.run_angle(vel, target - offset)
                offset = target
                if on_field():
                    return True
        motor.run_angle(vel, -offset)  # Achse zurueck zur Ausgangsposition

    return False


def move_sensor_to(row, col):
    """Positioniert den Farbsensor absolut ueber Feld (row=1-8, col=0-7).
    Nutzt run_target statt run_angle: der Motor faehrt immer zu einem
    festen Winkel relativ zur Nullposition – Haker in der Mechanik werden
    bei der naechsten Bewegung automatisch kompensiert.
    Anschliessend prueft center_on_field() ob der Sensor auf einem
    gueltigen Feld steht, und korrigiert falls er auf einer Feldlinie liegt.
    """
    motor_X2.run_target(velocity_X2,  move_distance_x * (8 - row))
    motor_Y2.run_target(velocity_Y2, -(move_distance_y * col))
    center_on_field()


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
    2: (145, 203, 35, 55,   0,  25),
}
_TOLERANCE = 0.05


def _in_range(value, low, high):
    return low * (1 - _TOLERANCE) <= value <= high * (1 + _TOLERANCE)


# scan field for white or black token and save the data of the field
def field_scan(position, board):
    NUM_SAMPLES = 5
    counts = {}

    wait(300)
    for _ in range(NUM_SAMPLES):
        wait(100)
        hsv = color_sensor.hsv(surface=False)
        h, s, v = hsv.h, hsv.s, hsv.v

        for color_value, (h_lo, h_hi, s_lo, s_hi, v_lo, v_hi) in _HSV_RANGES.items():
            if (_in_range(h, h_lo, h_hi) and
                    _in_range(s, s_lo, s_hi) and
                    _in_range(v, v_lo, v_hi)):
                if color_value in counts:
                    counts[color_value] += 1
                else:
                    counts[color_value] = 1
                break

    best_color = None
    best_count = 0
    for k in counts:
        if counts[k] > best_count:
            best_count = counts[k]
            best_color = k
    if best_color is not None:
        board.set(position, best_color)


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

ROBOT_COLOR = 2      # default: schwarz (wird in main() per Hub-Auswahl gesetzt)
ENEMY_COLOR = 1      # default: weiss   (wird in main() per Hub-Auswahl gesetzt)


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
#         FARB-AUSWAHL (Hub-Buttons)
# ============================================

def show_color_on_display(color):
    """Zeigt die Roboterfarbe auf der 5x5 LED-Matrix.
    Schwarz (2) = gefuellter Kreis, Weiss (1) = hohler Kreis.
    """
    hub.display.off()
    if color == 2:  # Schwarz = gefuellter Kreis (=schwarzer Reversi-Stein)
        pixels = [
            (0, 1), (0, 2), (0, 3),
            (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
            (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
            (3, 0), (3, 1), (3, 2), (3, 3), (3, 4),
            (4, 1), (4, 2), (4, 3)
        ]
    else:           # Weiss = hohler Kreis (=weisser Reversi-Stein)
        pixels = [
            (0, 1), (0, 2), (0, 3),
            (1, 0),                  (1, 4),
            (2, 0),                  (2, 4),
            (3, 0),                  (3, 4),
            (4, 1), (4, 2), (4, 3)
        ]
    for row, col in pixels:
        hub.display.pixel(row, col, 100)


def select_robot_color():
    """Farbe des Roboters per Hub-Buttons waehlen.
    Blinkendes Display = Auswahl laeuft.
    Rechter Button = Farbe wechseln.
    Linker Button  = Bestaetigen (Display bleibt dann dauerhaft an).
    """
    color = 2       # Standardfarbe: Schwarz
    blink_count = 0
    display_on = False

    while True:
        # Blinkmuster: 4 Zyklen an (400 ms), 2 Zyklen aus (200 ms)
        new_display_on = (blink_count % 6) < 4
        if new_display_on != display_on:
            if new_display_on:
                show_color_on_display(color)
            else:
                hub.display.off()
            display_on = new_display_on
        blink_count += 1

        pressed = hub.buttons.pressed()

        if Button.RIGHT in pressed:
            color = 1 if color == 2 else 2
            show_color_on_display(color)
            display_on = True
            blink_count = 0
            while Button.RIGHT in hub.buttons.pressed():
                wait(50)
            wait(200)

        elif Button.LEFT in pressed:
            # Bestaetigung: Display steady (kein Blinken mehr)
            show_color_on_display(color)
            while Button.LEFT in hub.buttons.pressed():
                wait(50)
            wait(200)
            break

        wait(100)

    return color


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
            elif val == 1:
                line += "W "
            elif val == 2:
                line += "S "
            else:
                line += "? "
        print(line)


def validate_start_position(board):
    """Prüft ob die 4 Anfangssteine korrekt erkannt wurden (D4/E4/D5/E5)."""
    start_fields = ["D4", "E4", "D5", "E5"]
    white = sum(1 for p in start_fields if board.get(p) == 1)
    black = sum(1 for p in start_fields if board.get(p) == 2)
    empty = sum(1 for p in start_fields if board.get(p) == 0)
    total = sum(1 for _, v in board.get_all_positions() if v != 0)

    print("Startcheck: Weiss=" + str(white) + " Schwarz=" + str(black) + " Leer=" + str(empty) + " Gesamt=" + str(total))

    if total == 0:
        print("FEHLER: Keine Steine erkannt. Sensorposition und Kalibrierung pruefen.")
        return False

    if empty > 0:
        print("WARNUNG: " + str(empty) + " Startfeld(er) in D4/E4/D5/E5 nicht erkannt. Sensorposition pruefen.")
        return False

    if white != 2 or black != 2:
        print("WARNUNG: Unerwartete Startaufstellung (erwartet W=2 S=2, erkannt W=" + str(white) + " S=" + str(black) + ")")
        return False

    print("Startposition korrekt.")
    return True


# ============================================
#         TURN INDICATOR (Chess Clock)
# ============================================

def goto_turn_indicator():
    motor_X2.run_target(velocity_X2, INDICATOR_X2)
    motor_Y2.run_target(velocity_Y2, INDICATOR_Y2)
    wait(300)


def is_indicator_red():
    wait(200)
    hsv = color_sensor.hsv(surface=False)
    h, s, v = hsv.h, hsv.s, hsv.v
    return 346 <= h <= 349 and 58 <= s <= 74 and 49 <= v <= 100


def wait_for_robot_turn():
    goto_turn_indicator()

    print("Warte: Gegner ist am Zug...")
    while is_indicator_red():
        wait(200)

    print("Warte: Gegner beendet Zug...")
    while not is_indicator_red():
        wait(200)

    print("Roboter ist am Zug.")
    default_position()


# ============================================
#          ROBOT MOVEMENT
# ============================================

def move_to_position(position):

    row = int(position[1])
    col = ord(position[0]) - ord('A')

    default_position()

    # X: absolut zum Zielfeld
    motor_X2.run_target(velocity_X2, move_distance_x * (9 - row))
    # Y: absolut zum Zielfeld + Stift-Versatz (Stift sitzt hinter dem Sensor)
    motor_Y2.run_target(velocity_Y2, -(move_distance_y * (col + 1)) - pen_offset_y)

    wait(500)
    Z2_tap()
    wait(500)

    default_position()


# function to calibrate actors
def calibration():
    print("Kalibrierung: Linken Button druecken")

    while Button.LEFT not in hub.buttons.pressed():
        wait(10)

    default_position()
    print("Kalibriert. Motorwinkel - X2:", motor_X2.angle(), "Y2:", motor_Y2.angle(), "Z2:", motor_Z2.angle())


# ============================================
#         FARBKALIBRIERUNG
# ============================================

def calibrate_colors():
    """Kalibriert HSV-Farbbereiche automatisch anhand bekannter Startpositionen.
    Ecken (A1/A8/H1/H8) sind beim Start garantiert leer -> Gruen-Referenz.
    Felder D4/E4/D5/E5 enthalten immer 2 weisse und 2 schwarze Steine.
    Erzeugt grosszuegige Bereiche, tolerant gegen Sensorpositionsschwankungen.
    """
    MARGIN_H = 25
    MARGIN_S = 20
    MARGIN_V = 20

    def scan_field(position):
        row = int(position[1])
        col = ord(position[0]) - ord('A')
        move_sensor_to(row, col)
        h_sum, s_sum, v_sum = 0, 0, 0
        num = 5
        for _ in range(num):
            wait(200)
            hsv = color_sensor.hsv(surface=False)
            h_sum += hsv.h
            s_sum += hsv.s
            v_sum += hsv.v
        h_avg = h_sum // num
        s_avg = s_sum // num
        v_avg = v_sum // num
        print("    avg H=" + str(h_avg) + " S=" + str(s_avg) + " V=" + str(v_avg))
        return h_avg, s_avg, v_avg

    def make_range(samples):
        h_min, h_max = 360, 0
        s_min, s_max = 100, 0
        v_min, v_max = 100, 0
        for h, s, v in samples:
            if h < h_min: h_min = h
            if h > h_max: h_max = h
            if s < s_min: s_min = s
            if s > s_max: s_max = s
            if v < v_min: v_min = v
            if v > v_max: v_max = v
        return (
            max(0,   h_min - MARGIN_H), min(360, h_max + MARGIN_H),
            max(0,   s_min - MARGIN_S), min(100, s_max + MARGIN_S),
            max(0,   v_min - MARGIN_V), min(100, v_max + MARGIN_V)
        )

    # Alle 4 Ecken scannen: im Startaufbau garantiert leere gruene Felder
    print("Kalibrierung: Ecken (Gruen)...")
    green_samples = []
    for pos in ["A1", "A8", "H1", "H8"]:
        h, s, v = scan_field(pos)
        green_samples.append((h, s, v))
        print("  " + pos + " H=" + str(h) + " S=" + str(s) + " V=" + str(v))

    # Startfelder mit je 2 weissen und 2 schwarzen Steinen
    print("Kalibrierung: Startfelder (Steine)...")
    piece_samples = []
    for pos in ["D4", "E4", "D5", "E5"]:
        h, s, v = scan_field(pos)
        piece_samples.append((h, s, v))
        print("  " + pos + " H=" + str(h) + " S=" + str(s) + " V=" + str(v))

    default_position()

    # Weiss = die 2 Steine mit hohem V (Helligkeit), Schwarz = die 2 mit niedrigem V
    piece_sorted = sorted(piece_samples, key=lambda x: x[2])
    black_samples = piece_sorted[:2]
    white_samples = piece_sorted[2:]

    # Sanity-Check: V-Abstand zwischen Weiss und Schwarz muss gross genug sein
    min_white_v = white_samples[0][2]
    max_black_v = black_samples[-1][2]
    for x in white_samples:
        if x[2] < min_white_v:
            min_white_v = x[2]
    for x in black_samples:
        if x[2] > max_black_v:
            max_black_v = x[2]

    if min_white_v < max_black_v + 10:
        print("WARNUNG: Weiss/Schwarz-Trennung unsicher (V-Abstand zu gering).")
        print("         Vorherige Farbwerte werden beibehalten.")
    else:
        _HSV_RANGES[1] = make_range(white_samples)
        _HSV_RANGES[2] = make_range(black_samples)

    _HSV_RANGES[0] = make_range(green_samples)

    print("Kalibrierung abgeschlossen:")
    print("  Gruen  : " + str(_HSV_RANGES[0]))
    print("  Weiss  : " + str(_HSV_RANGES[1]))
    print("  Schwarz: " + str(_HSV_RANGES[2]))


#### main program ####

def main():
    global ROBOT_COLOR, ENEMY_COLOR

    # Farbe des Roboters per Hub-Buttons auswaehlen (blinkendes Display)
    ROBOT_COLOR = select_robot_color()
    ENEMY_COLOR = 1 if ROBOT_COLOR == 2 else 2
    # Display zeigt die gewaehlte Farbe dauerhaft waehrend des Spiels
    show_color_on_display(ROBOT_COLOR)

    # creates the playground
    board = ReversiBoard()

    ######################################################
    #                    Playground Scan                 #
    ######################################################
    # scans each field on the playground for black and white tokens
    def playground_scan():

        default_position()

        going_down = True   # True = Zeile 8→1, False = Zeile 1→8

        for col_idx in range(8):
            col_letter = chr(ord('A') + col_idx)
            row_range = range(8, 0, -1) if going_down else range(1, 9)

            for row in row_range:
                move_sensor_to(row, col_idx)   # absolut – selbstkorrigierend
                field_scan(col_letter + str(row), board)

            going_down = not going_down

    ######################################################
    #                 REVERSI GAME LOOP                  #
    ######################################################

    def reversi_turn(skip_scan=False):

        print("===== NEUER ZUG =====")

        if not skip_scan:
            playground_scan()

        print("Spielfeld nach Scan:")
        print_board_debug(board)
        white = sum(1 for _, v in board.get_all_positions() if v == 1)
        black = sum(1 for _, v in board.get_all_positions() if v == 2)
        print("Weiss:", white, " Schwarz:", black)

        print("Berechne besten Zug (Tiefe=" + str(MINIMAX_DEPTH) + ")...")
        best_move = get_best_move(board, ROBOT_COLOR)

        if best_move is None:
            print("Kein gueltiger Zug moeglich - Zug wird uebersprungen.")
            return

        print("Bester Zug:", best_move)
        move_to_position(best_move)

        apply_move(board, best_move, ROBOT_COLOR)

        print("Spielfeld nach Roboterzug (erwartet):")
        print_board_debug(board)
        white = sum(1 for _, v in board.get_all_positions() if v == 1)
        black = sum(1 for _, v in board.get_all_positions() if v == 2)
        print("Weiss:", white, " Schwarz:", black)

        # warte bis Gegner Zug beendet hat (Uhr: rot -> schwarz -> rot)
        wait_for_robot_turn()

    calibration()
    wait_for_left_button()
    wait_for_left_button()

    # Pre-Game: Farben kalibrieren, dann nur die 4 Mittelfelder zur Verifikation scannen
    wait_for_left_button("Bereit fuer Farbkalibrierung und Pre-Game Scan")
    calibrate_colors()
    print("Scanne Startfelder (D4/E4/D5/E5)...")
    for _pos in ["D4", "E4", "D5", "E5"]:
        _row_num = int(_pos[1])
        _col_num = ord(_pos[0]) - ord('A')
        move_sensor_to(_row_num, _col_num)
        field_scan(_pos, board)
    default_position()
    print_board_debug(board)
    start_ok = validate_start_position(board)
    if not start_ok:
        wait_for_left_button("Startposition pruefen, dann fortfahren")

    first_turn = True
    while True:
        reversi_turn(skip_scan=first_turn)
        first_turn = False


main()
