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
        110,
        velocity_Z2
    )

    # short press time
    await runloop.sleep_ms(300)

    # move back up
    await motor.run_to_absolute_position(
        Motor_Z2,
        180,
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


def evaluate_move(position, flips):

    score = flips

    # corners are extremely valuable
    if position in ["A1", "A8", "H1", "H8"]:
        score += 100

    # edges are strong
    elif (
        position[0] in ["A", "H"]
        or
        position[1] in ["1", "8"]
    ):
        score += 20

    # avoid dangerous fields near corners
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

    # place token
    board.set(position, player)

    # flip enemy tokens
    for row, col in flippable:

        flip_position = indices_to_position(row, col)

        board.set(flip_position, player)
    
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

######################################################
#                    Start Sequence                  #
######################################################
async def start_sequence():
    # start sequence to move the base platform over the tablet
    motor.run(Motor_X1, velocity_X1)

    while True:
        distance = distance_sensor.distance(port.E)

        if distance <= 110:
            break

        await runloop.sleep_ms(10)

    await motor.run_for_degrees(Motor_X1, 10, velocity_X1, stop=motor.HOLD)


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

        # default values
        row = 8
        column = 65         # first column on the board in ASCII format

        await default_position()            # move to the default coordinate system position
        await wait_for_left_button()        # wait for the left button to be pressed to start the scan
        await X2_relative(18)                # move to the first field (A8) in x-direction
        await Y2_relative(20)                # move to the first field (A8) in y-direction

        await wait_for_left_button()        # wait for the left button to be pressed to start the scan

        # scan field for white or black token
        await field_scan("A8", board)

        # scan each column
        while column <= 72:

            if row == 8:
                row = 7
                # scan each field of one column in positive x-direction
                while row >= 1:

                    await X2_relative(18)                                # move to the next field
                    column_letter = chr(column)                         # convert the column number in the right letter (e.g. 65 to "A")
                    position = column_letter + str(row)                 # connects the column letter with the row number

                    # scan field for white or black token and save the data of the field
                    await field_scan(position, board)
                    row = row - 1

            else:
                # scan each field of one column in negative x-direction
                while row <= 8:
                    await X2_relative(-18)                                # move to the next field
                    column_letter = chr(column)                        # convert the column number in the right letter (e.g. 65 to "A")
                    position = column_letter + str(row)                # connects the column letter with the row number

                    # scan field for white or black token and save the data of the field
                    await field_scan(position, board)
                    row = row + 1

                # exclude out of range values for the next iteration
            if row == 0:
                row = 1
            elif row == 9:
                row = 8
            
            column = column + 1                            # count up the column
            if column > 72:                                # end of the board reached
                break

            await runloop.sleep_ms(2000) #testweise


            await Y2_relative(20)                               # move the robot to the next column (one field in positive Y2-direction)
            column_letter = chr(column)                        # convert the column number in the right letter (e.g. 65 to "A")
            position = column_letter + str(row)                # connects the column letter with the row number

            # scan field for white or black token and save the data of the field
            await field_scan(position, board)

            if column % 2 == 0:                                # even column
                row = row + 1
    
    ######################################################
    #                 REVERSI GAME LOOP                  #
    ######################################################

    async def reversi_turn():

        print("SCAN PLAYGROUND")

        await playground_scan()

        print(board.get_all_positions())

        # calculate best move
        best_move = get_best_move(
            board,
            ROBOT_COLOR
        )

        if best_move is None:

            print("NO VALID MOVE")
            return

        print("BEST MOVE:", best_move)

        # move robot
        await move_to_position(best_move)

        # update board
        apply_move(
            board,
            best_move,
            ROBOT_COLOR
        )

        print("BOARD UPDATED")

        print(board.get_all_positions())

        # wait for enemy move
        await wait_for_left_button(
            "Gegner hat Zug ausgeführt"
        )

    await calibration()
    await wait_for_left_button()
    await start_sequence()
    await wait_for_left_button()
    
    while True:

        await reversi_turn()

runloop.run(main())