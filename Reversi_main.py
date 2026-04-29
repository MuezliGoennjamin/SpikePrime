import runloop
import motor, distance_sensor, color_sensor, color
from hub import port, button

# Programm auf kleines Feld agestimmt

# Hub Anschluss: Motor X1 = Port A, Motor X2 = Port B, Motor Y2 = Port C, Motor Z2 = Port D, Distance Sensor = Port E, Color Sensor = Port F

#global variables
velocity_X1 = 90
velocity_X2 = 90
velocity_Y2 = 90
velocity_Z2 = 30
Motor_X1 = port.A           # Hub Port A
Motor_X2 = port.B           # Hub Port B
Motor_Y2 = port.C           # Hub Port C
Motor_Z2 = port.D           # Hub Port D
height_tablet = 15          # [mm]


###################################################### 
#                    Functions                       #
######################################################

# sets the default position of the Coordinate System
async def default_position():
   await motor.run_to_absolute_position(Motor_X2, 0, velocity_X2, acceleration= velocity_X2, deceleration= velocity_X2)
   await motor.run_to_absolute_position(Motor_Y2, 0, velocity_X2, acceleration= velocity_Y2, deceleration= velocity_Y2)
   await motor.run_to_absolute_position(Motor_Z2, 0, velocity_Z2, acceleration= velocity_Z2, deceleration= velocity_Z2)

# defines the moving distance of the Motors
async def X2_relative(distance):    # [cm]
    motor.run_for_degrees(Motor_X2, distance *90, velocity_X2)
async def Y2_relative(distance):    # [cm]
    motor.run_for_degrees(Motor_Y2, -distance *90, velocity_Y2)

# scan field for white or black token and save the data of the field
def field_scan(position, board):
    if color_sensor.color(port.F) is color.GREEN:
        board.set(position, 0)
    elif color_sensor.color(port.F) is color.WHITE:
        board.set(position, 1)
    elif color_sensor.color(port.F) is color.BLACK:
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
    


######################################################
#                    Start Sequence                  #
######################################################
async def start_sequence():
    # start sequence to move the base platform over the tablet
    motor.run(Motor_X1, velocity_X1)

    while True:
        distance = distance_sensor.distance(port.E)

        if distance <= 90:
            break

        await runloop.sleep_ms(10)

    await motor.run_for_degrees(Motor_X1, 90, velocity_X1, stop=motor.HOLD)


# function to calibrate actors
async def calibration():
    # set the default Coordinate System position manually
    while button.pressed(button.LEFT):
        await default_position()
runloop.run(calibration())


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
        await X2_relative(4)                # move to the first field (A8) in x-direction
        await Y2_relative(2)                # move to the first field (A8) in y-direction

        # scan field for white or black token
        field_scan("A8", board)

        # scan each column
        while column <= 72:

            if row == 8:
                row = 7
                # scan each field of one column in positive x-direction
                while row >= 1:
                    await X2_relative(2)                                # move to the next field
                    column_letter = chr(column)                         # convert the column number in the right letter (e.g. 65 to "A")
                    position = column_letter + str(row)                 # connects the column letter with the row number

                    # scan field for white or black token and save the data of the field
                    field_scan(position, board)
                    row = row - 1

            else:
                # scan each field of one column in negative x-direction
                while row <= 8:
                    await X2_relative(-2)                                # move to the next field
                    column_letter = chr(column)                        # convert the column number in the right letter (e.g. 65 to "A")
                    position = column_letter + str(row)                # connects the column letter with the row number

                    # scan field for white or black token and save the data of the field
                    field_scan(position, board)
                    row = row + 1

                # exclude out of range values for the next iteration
            if row == 0:
                row = 1
            elif row == 9:
                row = 8
            
            column = column + 1                            # count up the column
            if column > 72:                                # end of the board reached
                break

            await Y2_relative(2)                               # move the robot to the next column (one field in positive Y2-direction)
            column_letter = chr(column)                        # convert the column number in the right letter (e.g. 65 to "A")
            position = column_letter + str(row)                # connects the column letter with the row number

            # scan field for white or black token and save the data of the field
            field_scan(position, board)

            if column % 2 == 0:                                # even column
                row = row + 1

    await start_sequence()
    await playground_scan()

runloop.run(main())