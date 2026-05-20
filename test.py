import runloop
import motor, distance_sensor, color_sensor, color
from hub import port, button

# Programm auf kleines Feld abgestimmt

# Hub Anschluss:
# Motor X1 = Port A
# Motor X2 = Port B
# Motor Y2 = Port C
# Motor Z2 = Port D
# Distance Sensor = Port E
# Color Sensor = Port F


######################################################
#                    DEBUG                           #
######################################################

DEBUG = True

def debug(text):
    if DEBUG:
        print("[DEBUG]", text)


######################################################
#               GLOBAL VARIABLES                     #
######################################################

velocity_X1 = 150
velocity_X2 = 90
velocity_Y2 = 100
velocity_Z2 = 50

Motor_X1 = port.A
Motor_X2 = port.C
Motor_Y2 = port.F
Motor_Z2 = port.B


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

    debug("DEFAULT POSITION START")

    await motor.run_to_absolute_position(
        Motor_X2,
        0,
        velocity_X2
    )

    debug("Motor_X2 -> 0")

    await motor.run_to_absolute_position(
        Motor_Y2,
        0,
        velocity_Y2
    )

    debug("Motor_Y2 -> 0")

    await motor.run_to_absolute_position(
        Motor_Z2,
        180,
        velocity_Z2
    )

    debug("Motor_Z2 -> 180")

    debug("DEFAULT POSITION END")


# defines the moving distance of the Motors
async def X2_relative(distance):    # [mm]

    debug("X2 MOVE")
    debug("distance = " + str(distance))

    await motor.run_for_degrees(
        Motor_X2,
        distance * 5,
        velocity_X2
    )

    debug("X2 MOVE FINISHED")


async def Y2_relative(distance):    # [mm]

    debug("Y2 MOVE")
    debug("distance = " + str(distance))

    await motor.run_for_degrees(
        Motor_Y2,
        -distance * 5,
        velocity_Y2
    )

    debug("Y2 MOVE FINISHED")

async def Z2_tap():

    debug("Z2 TAP START")

    await wait_for_left_button(
        "Vor Bildschirm-Tipp"
    )

    await motor.run_to_absolute_position(
        Motor_Z2,
        110,
        velocity_Z2
    )

    debug("Z2 DOWN")

    await runloop.sleep_ms(300)

    await motor.run_to_absolute_position(
        Motor_Z2,
        180,
        velocity_Z2
    )

    debug("Z2 UP")

    await runloop.sleep_ms(300)

    debug("Z2 TAP END")


# scan field for white or black token and save the data of the field
# scan field for white or black token and save the data of the field
async def field_scan(position, board):

    debug("SCAN FIELD -> " + position)
    debug("WAIT 500ms FOR STABLE COLOR DETECTION")

    # kurze Wartezeit für stabile Farberkennung
    await runloop.sleep_ms(500)

    detected_color = color_sensor.color(port.D)

    debug("Detected Color = " + str(detected_color))

    if detected_color is color.GREEN:
        board.set(position, 0)
        debug(position + " = GREEN")

    elif detected_color is color.WHITE:
        board.set(position, 1)
        debug(position + " = WHITE")

    elif detected_color is color.BLACK:
        board.set(position, 2)
        debug(position + " = BLACK")

    else:
        debug(position + " = UNKNOWN")


# ============================================
# Reversi Board - Game Field Management
# ============================================

class ReversiBoard:

    """Manages the 8x8 Reversi game board"""

    def __init__(self):

        debug("CREATE BOARD")

        self.board = []

        for row in range(8):

            new_row = []

            for col in range(8):
                new_row.append(0)

            self.board.append(new_row)

        debug("BOARD CREATED")

    def _parse_position(self, position):

        column_letter = position[0].upper()
        column_number = ord(column_letter) - ord('A')

        row_number = int(position[1])
        row_index = row_number - 1

        return row_index, column_number

    def set(self, position, value):

        debug("SET FIELD")
        debug("Position = " + position)
        debug("Value = " + str(value))

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
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1)
]

ROBOT_COLOR = 2
ENEMY_COLOR = 1


def is_on_board(row, col):

    return row >= 0 and row < 8 and col >= 0 and col < 8


def indices_to_position(row, col):

    column_letter = chr(ord('A') + col)
    row_number = str(row + 1)

    return column_letter + row_number


def get_flippable_tokens(board, position, player):

    debug("CHECK MOVE -> " + position)

    opponent = ENEMY_COLOR if player == ROBOT_COLOR else ROBOT_COLOR

    row, col = board._parse_position(position)

    # occupied
    if board.board[row][col] != 0:

        debug(position + " OCCUPIED")

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

    debug("FLIPPABLE = " + str(len(flippable)))

    return flippable


def get_valid_moves(board, player):

    debug("GET VALID MOVES")

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

                debug("VALID MOVE -> " + position)

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

    debug(position + " SCORE = " + str(score))

    return score


def get_best_move(board, player):

    debug("CALCULATE BEST MOVE")

    valid_moves = get_valid_moves(board, player)

    if len(valid_moves) == 0:

        debug("NO VALID MOVES")

        return None

    best_move = None
    best_score = -9999

    for position, flips in valid_moves:

        score = evaluate_move(position, flips)

        if score > best_score:

            best_score = score
            best_move = position

    debug("BEST MOVE = " + str(best_move))
    debug("BEST SCORE = " + str(best_score))

    return best_move


def apply_move(board, position, player):

    debug("APPLY MOVE -> " + position)

    flippable = get_flippable_tokens(
        board,
        position,
        player
    )

    board.set(position, player)

    for row, col in flippable:

        flip_position = indices_to_position(row, col)

        debug("FLIP -> " + flip_position)

        board.set(flip_position, player)

# ============================================
#          ROBOT MOVEMENT
# ============================================

async def move_to_position(position):

    debug("MOVE TO POSITION START")

    debug("TARGET = " + position)

    row = int(position[1])
    col = ord(position[0]) - ord('A')

    debug("ROW = " + str(row))
    debug("COL = " + str(col))

    x_distance = (8 - row) * 18
    y_distance = col * 20

    debug("X DISTANCE = " + str(x_distance))
    debug("Y DISTANCE = " + str(y_distance))

    await wait_for_left_button(
        "Vor Bewegung zum Spielzug"
    )

    await default_position()

    debug("MOVE X")

    await X2_relative(18 + x_distance)

    debug("MOVE Y")

    await Y2_relative(20 + y_distance)

    debug("TARGET REACHED")

    await wait_for_left_button(
        "Vor Touch-Eingabe"
    )

    await Z2_tap()

    debug("TOKEN PLACED")

    await wait_for_left_button(
        "Vor Rückfahrt"
    )

    await default_position()

    debug("MOVE TO POSITION END")


######################################################
#                    Start Sequence                  #
######################################################

async def start_sequence():

    debug("START SEQUENCE")

    motor.run(Motor_X1, velocity_X1)

    while True:

        distance = distance_sensor.distance(port.E)

        debug("Distance = " + str(distance))

        if distance <= 110:
            debug("TARGET DISTANCE REACHED")
            break

        await runloop.sleep_ms(10)

    await motor.run_for_degrees(
        Motor_X1,
        10,
        velocity_X1,
        stop=motor.HOLD
    )

    debug("START SEQUENCE END")


# function to calibrate actors
async def calibration():

    print("Drücke linken Button zum Kalibrieren")

    while not button.pressed(button.LEFT):
        await runloop.sleep_ms(10)

    debug("CALIBRATION START")

    await default_position()

    print("Kalibriert")

    print(
        motor.absolute_position(Motor_X2),
        motor.absolute_position(Motor_Y2),
        motor.absolute_position(Motor_Z2)
    )

    debug("CALIBRATION END")


######################################################
#                    MAIN PROGRAM                    #
######################################################

async def main():

    debug("PROGRAM START")

    # creates the playground
    board = ReversiBoard()


    ######################################################
    #                    Playground Scan                 #
    ######################################################

    async def playground_scan():

        debug("PLAYGROUND SCAN START")

        # default values
        row = 8
        column = 65

        debug("Start Position = A8")

        await default_position()

        await wait_for_left_button(
            "Default Position erreicht"
        )

        await X2_relative(18)

        await Y2_relative(10)

        debug("Moved to A8")

        await wait_for_left_button(
            "Vor erstem Feldscan"
        )

        # scan field for white or black token
        await field_scan("A8", board)

        # scan each column
        while column <= 72:

            debug("--------------------------------")
            debug("COLUMN = " + chr(column))
            debug("ROW = " + str(row))

            if row == 8:

                debug("SCAN DOWN")

                row = 7

                # scan each field of one column in positive x-direction
                while row >= 1:

                    column_letter = chr(column)
                    position = column_letter + str(row)

                    debug("NEXT POSITION -> " + position)

                    await wait_for_left_button(
                        "Vor Bewegung zu " + position
                    )

                    await X2_relative(18)

                    debug("POSITION REACHED -> " + position)

                    # scan field
                    await field_scan(position, board)

                    row = row - 1

            else:

                debug("SCAN UP")

                # scan each field of one column in negative x-direction
                while row <= 8:

                    column_letter = chr(column)
                    position = column_letter + str(row)

                    debug("NEXT POSITION -> " + position)

                    await wait_for_left_button(
                        "Vor Bewegung zu " + position
                    )

                    await X2_relative(-18)

                    debug("POSITION REACHED -> " + position)

                    # scan field
                    await field_scan(position, board)

                    row = row + 1

            # exclude out of range values
            if row == 0:
                row = 1

            elif row == 9:
                row = 8

            column = column + 1

            debug("NEXT COLUMN")

            if column > 72:

                debug("SCAN FINISHED")

                break

            debug("--------------------------------")
            debug("COLUMN TRANSITION")
            debug("LAST ROW IN COLUMN = " + str(row))
            debug("MOVE TO NEXT COLUMN -> " + chr(column + 1))
            debug("--------------------------------")

            await runloop.sleep_ms(2000) #testweise

            await Y2_relative(20)

            column_letter = chr(column)
            position = column_letter + str(row)

            debug("COLUMN CHANGED -> " + position)

            # scan field
            await field_scan(position, board)

            if column % 2 == 0:
                row = row + 1

        debug("PLAYGROUND SCAN END")

        ######################################################
    #                 REVERSI GAME LOOP                  #
    ######################################################

    async def reversi_turn():

        debug("================================")
        debug("REVERSI TURN START")
        debug("================================")

        await playground_scan()

        debug("SCAN FINISHED")

        print(board.get_all_positions())

        await wait_for_left_button(
            "Nach Spielfeldscan"
        )

        best_move = get_best_move(
            board,
            ROBOT_COLOR
        )

        if best_move is None:

            print("NO VALID MOVE")

            debug("NO VALID MOVE")

            return

        print("BEST MOVE:", best_move)

        debug("BEST MOVE = " + best_move)

        await wait_for_left_button(
            "Vor Roboterzug"
        )

        await move_to_position(best_move)

        debug("MOVE EXECUTED")

        apply_move(
            board,
            best_move,
            ROBOT_COLOR
        )

        debug("BOARD UPDATED")

        print(board.get_all_positions())

        await wait_for_left_button(
            "Gegner hat Zug ausgeführt"
        )

        debug("TURN FINISHED")
   
    await calibration()

    await wait_for_left_button(
        "Vor Startsequenz"
    )

    await start_sequence()

    await wait_for_left_button(
        "Vor Playground Scan"
    )

    while True:

        await reversi_turn()


runloop.run(main())