"""
Welcome to Item Routing System!

Authors: Joseph Abero, ChatGPT

ItemRoutingSystem is a text-based application used to provide store workers with
directions to gather shopping items around a warehouse.
"""

from constants import *
from menu import Menu

from copy import deepcopy
import heapq
import itertools
import os
import platform
import random
import signal
import sys
import time

class ItemRoutingSystem:
    """
    Main application for providing directions for a single worker to gather items.

    Handles user inputs, generation of the map, and settings.
    """
    WORKER_START_SYMBOL = 'S'
    WORKER_END_SYMBOL   = 'E'
    ITEM_SYMBOL         = chr(ord("▣"))
    ORDERED_ITEM_SYMBOL = '‼'

    def __init__(self):
        """
        Initializes ItemRoutingSystem application class.

        Defaults a map with a worker starting position of (0, 0).
        """
        # Default debug mode
        self.debug = False

        # Default map size
        self.map_x = 40
        self.map_y = 21

        # Default product info list
        self.product_info = {}
        self.product_file = None

        # Default order list
        self.order = []

        # Default test case filename
        self.test_case_file = None
        self.test_product_file = None
        self.test_cases = []

        # Default worker settings
        self.worker_mode = GenerateMode.MANUAL
        self.starting_position = (0, 0)
        self.ending_position = (0, 0)

        # Default item settings
        self.item_mode = GenerateMode.RANDOM
        self.minimum_items = 0
        self.maximum_items = 8
        self.items = self.get_item_positions()

        # Default algorithm
        self.gathering_algo = AlgoMethod.DIJKSTRA
        self.tsp_algorithm = AlgoMethod.BRANCH_AND_BOUND
        self.maximum_routing_time = 15

        # Generate initial map from default settings
        self.map, self.inserted_order = self.generate_map()
        self.graph = None

        # Display welcome banner
        banner = "------------------------------------------------------------"
        self.log(banner)
        self.log("")
        self.log("")
        self.log(f'{"Welcome to Item Routing System!".center(len(banner))}')
        self.log("")
        self.log("")
        self.log(banner)

    def log(self, *args, print_type=PrintType.NORMAL):
        """
        Logs information to screen depending on application's debug mode.

        Args:
            *args: Arguments to be printed to screen.

            print_type (PrintType): Type of log to determine when log should be printed to screen.
        """
        if print_type == PrintType.NORMAL:
            print(*args)

        elif print_type == PrintType.DEBUG:
            if self.debug:
                print(*args)

    def load_product_file(self, product_file_name):
        """
        Opens product file, parses information from the file, and stores the information
        as a dictionary of tuples within the product_file_info member variable.

        Args:
            product_file_name (str): Absolute or relative file path to text file with
                                     warehouse product location details.

        Returns:
            success (bool): Status of whether opening and parsing of file was successful.
        """
        success = True

        try:
            self.product_file = product_file_name
            f = open(product_file_name, 'r')
            next(f)

            for line in f:
                fields = line.strip().split()
                self.product_info[int(fields[0])] = int(float(fields[1])), int(float(fields[2]))
            f.close()
        except FileNotFoundError:
            success = False

        return success

    def load_test_case_file(self, test_case_filename):
        cases = []
        success = True

        try:
            with open(test_case_filename, "r") as f:

                # Read in each line from the file
                for i, line in enumerate(f.readlines()):

                    # First line of the file is the product filename
                    if i == 0:
                        filename = line.rstrip()
                        continue

                    # Parse the line info
                    size, products = line.split(": ")

                    # Strip newline & convert ids to list
                    product_ids = products.rstrip().split(", ")

                    # Convert each id to integer
                    product_ids = [int(p_id) for p_id in product_ids]

                    cases.append((size, product_ids))
        except FileNotFoundError:
            success = False

        if success:
            self.test_cases = cases
            self.test_product_file = filename

        return success

    def display_menu(self, menu_type, clear=True):
        """
        Creates and displays the appropriate menu.

        Args:
            menu_type (MenuType): Type of menu to display.
            clear (bool): Option to clear screen.

        Examples:
            >>> ItemRoutingSystem.display(MenuType.MAIN_MENU)
            ------------------------------------------------------------
                                     Main Menu
            ------------------------------------------------------------

            1. View Map
            2. Settings
            3. Exit

        """
        menu = None

        if menu_type == MenuType.MAIN_MENU:
            menu = Menu("Main Menu")
            menu.add_option(1, "View Map")
            menu.add_option(2, "Settings")
            menu.add_option(3, "Exit")

        elif menu_type == MenuType.VIEW_MAP:
            menu = Menu("View Map Menu")
            menu.add_option(1, "Create Order")
            menu.add_option(2, "Get Path for Order")
            menu.add_option(3, "Get Path to Product")
            menu.add_option(4, "Get Location of Product")

            # Only expose advanced setting option in debug mode
            if self.debug:
                menu.add_option(5, "Generate New Map")
                menu.add_option(6, "Back")
            else:
                menu.add_option(5, "Back")

        elif menu_type == MenuType.SETTINGS:
            menu = Menu("Settings Menu")
            menu.add_option(1, "Load Product File")
            menu.add_option(2, "Set Worker Starting Position Mode")
            menu.add_option(3, "Set Worker Ending Position Mode")
            menu.add_option(4, "Set Maximum Items Ordered")
            menu.add_option(5, "Set Routing Time Maximum")
            menu.add_option(6, "Toggle Debug Mode")

            if self.debug:
                menu.add_option(7, "Advanced Settings")
                menu.add_option(8, "Back")

            else:
                menu.add_option(7, "Back")

            info = "Current Settings:\n" \
                   f"  Loaded Product File: {self.product_file}\n" \
                   f"  Worker Settings:\n" \
                   f"   Starting Position: {self.starting_position}\n" \
                   f"   Ending Position: {self.ending_position}\n" \
                   f"  Maximum Routing Time: {self.maximum_routing_time}\n" \
                   f"  Debug Mode: {self.debug}\n"

            menu.set_misc_info(info)

        elif menu_type == MenuType.ADVANCED_SETTINGS:
            menu = Menu("Advanced Settings Menu")
            menu.add_option(1, "Set Map Size")
            menu.add_option(2, "Set Item Position Mode")
            menu.add_option(3, "Set Map Orientation")
            menu.add_option(4, "Set Gathering Algorithm")
            menu.add_option(5, "Set TSP Algorithm")
            menu.add_option(6, "Load Test Case File")
            menu.add_option(7, "Run Test Cases")
            menu.add_option(8, "Back")

            position_str = ' '.join(str(p) for p in self.items)
            if len(self.items) > 10:
                file = "positions.txt"

                # Write positions to file if too many to print to screen
                with open(file, "w+") as f:
                    for position in self.items:
                        x, y = position
                        f.write(f"({x}, {y})\n")

                position_str = f"See '{file}' for list of item positions."

            info = "Current Advanced Settings:\n" \
                   f"Map Size: {self.map_x}x{self.map_y}\n" \
                   f"\n" \
                   f"Worker Settings:\n" \
                   f"  Mode: {self.worker_mode}\n" \
                   f"  Gathering Algorithm: {self.gathering_algo}\n" \
                   f"  TSP Algorithm: {self.tsp_algorithm}\n" \
                   f"Item Settings:\n" \
                   f"  Mode: {self.item_mode}\n" \
                   f"  Number of Items: {len(self.items)}\n" \
                   f"  Positions: {position_str}\n" \
                   f"Debug Mode: {self.debug}\n"

            menu.set_misc_info(info)

        elif menu_type == MenuType.LOAD_PRODUCT_FILE:
            menu = Menu("Load Product File Menu")

        elif menu_type == MenuType.LOAD_TEST_CASE_FILE:
            menu = Menu("Load Test Case File Menu")

        elif menu_type == MenuType.GATHER_ALGO_METHOD:
            menu = Menu("Set Gathering Algorithm")
            menu.add_option(1, "Use Order of Insertion")
            menu.add_option(2, "Brute Force")
            menu.add_option(3, "Dijkstra")
            menu.add_option(4, "Back")

        elif menu_type == MenuType.TSP_ALGO_METHOD:
            menu = Menu("Set TSP Algorithm")
            menu.add_option(1, "Branch and Bound")
            menu.add_option(2, "Localized Minimum Path")
            menu.add_option(3, "Back")

        elif menu_type == MenuType.WORKER_START_POSITION:
            menu = Menu("Set Starting Worker Position Mode")

            if self.debug:
                menu.add_option(1, "Randomly Set Position")
                menu.add_option(2, "Manually Set Position")
                menu.add_option(3, "Back")

        elif menu_type == MenuType.WORKER_ENDING_POSITION:
            menu = Menu("Set Ending Worker Position Mode")

            if self.debug:
                menu.add_option(1, "Randomly Set Position")
                menu.add_option(2, "Manually Set Position")
                menu.add_option(3, "Back")

        elif menu_type == MenuType.ITEM_POSITION:
            menu = Menu("Set Item Position Mode")
            menu.add_option(1, "Randomly Set Position")
            menu.add_option(2, "Manually Set Position")
            menu.add_option(3, "Back")

        if menu:
            menu.display(clear=clear)

    def generate_map(self, positions=None):
        """
        Generates a list of lists to represent a map of items.

        The starting worker position will be placed as specified by the internal
        starting position.
        Items will be placed depending on positions passed in or previously determined positions.

        For debugging purposes, instead of logging all item positions to screen, it
        creates a `positions.txt` file in the directory where the application is running
        if there are more than 10 items within the list.

        Args:
            positions (list of tuples): List of item positions to be placed within the grid.

        Returns:
            grid (list of lists): Map which contains worker starting position
                                  and randomly placed items.

            inserted_order (list of tuples): Positions of items in order of when
                                             inserted to grid.
        """
        # Create list of lists to generate map
        # x is number of columns, y is number of rows
        grid = []
        for _ in range(self.map_x):
            grid.append(['_' for _ in range(self.map_y)])

        # Get order of list of items inserted
        inserted_order = []

        # Set the starting position (Defaults to (0, 0))
        grid[self.starting_position[0]][self.starting_position[1]] = ItemRoutingSystem.WORKER_START_SYMBOL

        if self.starting_position != self.ending_position:
            grid[self.ending_position[0]][self.ending_position[1]] = ItemRoutingSystem.WORKER_END_SYMBOL

        # Insert item positions
        if positions is None:
            if self.debug:
                if len(self.items) > 10:
                    file = "positions.txt"

                    # Write positions to file if too many to print to screen
                    with open(file, "w+") as f:
                        for position in self.items:
                            x, y = position
                            f.write(f"({x}, {y})\n")

                    self.log(f"See '{file}' for list of item positions.", print_type=PrintType.DEBUG)
                else:
                    self.log(self.items, print_type=PrintType.DEBUG)

            positions = self.items

        for position in positions:
            # Set position in grid
            x, y = position

            # Only set item if its position is within defined grid
            if x < self.map_x and y < self.map_y:
                grid[x][y] = ItemRoutingSystem.ITEM_SYMBOL
                inserted_order.append((x, y))

        return grid, inserted_order

    def display_map(self):
        """
        Prints map to screen with a legend. Map will be centered within the
        banner.

        Examples:
            >>> ItemRoutingSystem.display_map()
            ------------------------------------------------------------
                              Warehouse Map Layout
            ------------------------------------------------------------
                                    0 S _ ▩ _ _
                                    1 _ ▩ _ ▩ _
                                    2 _ _ _ _ _
                                    3 ▩ _ ▩ ▩ ▩
                                    4 _ _ _ ▩ _
                                      0 1 2 3 4

                                      LEGEND:
                             'S': Worker Starting Spot
                                 '▩': Item
                          Positions are labeled as (X, Y)

            Current Settings:
              Worker Position: (0, 0)
              Ordered Item Maximum: 8
              Gathering Algorithm: Dijkstra
              Maximum Time To Process: 60
              Debug Mode: False
        """
        banner_length = 60
        banner = Menu("Warehouse Map Layout")
        banner.display()

        grid = []
        for y in reversed(range(len(self.map[0]))):
            col = []
            for x in range(len(self.map)):
                # Only display item if its position is within defined grid
                if x < self.map_x and y < self.map_y:
                    col.append(self.map[x][y])
            grid.append(col)

        for i, col in zip(reversed(range(len(grid))), grid):
            row_string = f"{i:2} "

            for j, val in enumerate(col):
                row_string += val + " " * len(str(j))

            self.log(row_string.center(banner_length))

        left_spacing = len(str(i)) + 2
        self.log(f"{' ':{left_spacing}}" + " ".join(str(i) for i in range(len(self.map))).center(banner_length))

        self.log("")
        self.log("LEGEND:".center(banner_length))
        self.log(f"{ItemRoutingSystem.WORKER_START_SYMBOL}: Worker Starting Spot".center(banner_length))
        self.log(f"{ItemRoutingSystem.WORKER_END_SYMBOL}: Worker Ending Spot".center(banner_length))
        self.log(f"{ItemRoutingSystem.ITEM_SYMBOL}: Item".center(banner_length))
        self.log(f"{ItemRoutingSystem.ORDERED_ITEM_SYMBOL}: Ordered Item".center(banner_length))
        self.log("Positions are labeled as (X, Y)".center(banner_length))
        self.log("X is the horizontal axis, Y is the vertical axis".center(banner_length))
        self.log("")
        self.log("Missing Worker Ending Spot means it overlaps with Starting Spot")
        self.log("")

        settings_info = "Current Settings:\n" \
                        f"  Worker Position: {self.starting_position}\n" \
                        f"  Ordered Item Maximum: {self.maximum_items}\n" \
                        f"  Algorithm: {self.tsp_algorithm}\n" \
                        f"  Maximum Routing Time: {self.maximum_routing_time}\n" \
                        f"  Debug Mode: {self.debug}\n"

        self.log(settings_info)

    def display_path_in_map(self, steps):
        path = []
        original_map = deepcopy(self.map)

        for step in steps:
            # From (0, 5), move right 10 to (10, 5).
            if step.startswith("From"):
                for direction in ["right", "left", "up", "down"]:
                    if direction in step:
                        parsed = step.split(" ")

                        start_x = int(parsed[1][1:-1])  # Parse '(0,'
                        start_y = int(parsed[2][:-2])   # Parse ' 5)'

                        dir_index = parsed.index(direction)
                        step_magnitude = int(parsed[dir_index + 1])  # Parse 'right 10'


                        end_x = int(parsed[dir_index + 3][1:-1])  # Parse '(10,'
                        end_y = int(parsed[dir_index + 4][:-2])   # Parse '5).'

                        step_values = {
                            "type": "move",
                            "start": (start_x, start_y),
                            "direction": direction,
                            "step_magnitude": step_magnitude,
                            "end": (end_x, end_y)
                        }

                        path.append(step_values)

            elif step.startswith("Pickup item"):
                parsed = step.split(" ")

                end_x = int(parsed[3][1:-1])
                end_y = int(parsed[4][:-2])

                step_values = {
                    "type": "pickup",
                    "end": (end_x, end_y)
                }

                path.append(step_values)

        arrows = {
            "left": chr(ord('←')),
            "right": chr(ord('→')),
            "up": chr(ord('↑')),
            "down": chr(ord('↓')),
            "up_down": chr(ord('⇅')),
            "left_right": chr(ord('⇄'))
        }

        for step in path:

            if step["type"] == "move":
                start = step["start"]
                for i in range(step["step_magnitude"]):
                    x, y = start
                    if step["direction"] == "up":
                        y += i

                    elif step["direction"] == "down":
                        y -= i

                    elif step["direction"] == "left":
                        x -= i

                    elif step["direction"] == "right":
                        x += i

                    if self.map[x][y] == ItemRoutingSystem.WORKER_START_SYMBOL or \
                       self.map[x][y] == ItemRoutingSystem.WORKER_END_SYMBOL:
                        continue

                    elif self.map[x][y] == '_':
                        self.map[x][y] = arrows[step["direction"]]

                    elif self.map[x][y] in [arrows["up"], arrows["down"]]:
                        self.map[x][y] = arrows["up_down"]

                    elif self.map[x][y] in [arrows["left"], arrows["right"]]:
                        self.map[x][y] = arrows["left_right"]

            elif step["type"] == "pickup":
                x, y = step["end"]
                self.map[x][y] = ItemRoutingSystem.ORDERED_ITEM_SYMBOL

        self.display_map()

        # Restore Original Map
        self.map = deepcopy(original_map)

    def move_to_target(self, start, end):
        """
        Helper function to evaluate moves to make between a start and end
        position.

        Args:
            start (tuple): Starting position specified as (X, Y) position.
            end   (tuple): End position to move to specified as (X, Y) position.

        Returns:
            move (str): String describing move to make to reach position.
            total_steps (int): Total number of steps taken.

        Examples:
            >>> ItemRoutingSystem.move_to_target((0, 0), (2, 0))
            "From (0, 0), move right 2 to (2, 0).", (2, 0)
        """
        current_position = start
        x_done = y_done = False
        x_direction = y_direction = None
        x_diff = y_diff = 0

        # Move X position
        if current_position[0] != end[0]:
            x_diff = end[0] - current_position[0]

            # Move Left
            if x_diff < 0:
                x_position = (current_position[0] - x_diff, current_position[1])
                x_direction = "left"

            # Move Right
            elif x_diff > 0:
                x_position = (current_position[0] + x_diff, current_position[1])
                x_direction = "right"

        # Move Y position
        if current_position[1] != end[1]:
            y_diff = end[1] - current_position[1]

            # Move Up
            if y_diff < 0:
                y_position = (current_position[0], current_position[1] - y_diff)
                y_direction = "down"

            # Move Down
            elif y_diff > 0:
                y_position = (current_position[0], current_position[1] + y_diff)
                y_direction = "up"

        move = f"From {start}"
        if x_direction and y_direction:
            move += f", move {x_direction} {abs(x_diff)} and move {y_direction} {abs(y_diff)}"
        elif x_direction:
            move += f", move {x_direction} {abs(x_diff)}"
        elif y_direction:
            move += f", move {y_direction} {abs(y_diff)}"
        move += f" to {end}."

        total_steps = abs(x_diff) + abs(y_diff)

        return move, total_steps

    def process_order(self, product_ids):
        shelves = {}

        for product_id in product_ids:
            if product_id in self.product_info:
                # Get Location
                location = self.product_info[product_id]

                # Group Product ID in Shelf location
                if location not in shelves:
                    shelves[location] = []
                shelves[location].append(product_id)

        grouped_items = []
        for shelf in shelves:
            grouped_items += shelves[shelf]

        # Add starting and ending nodes
        return ['Start'] + grouped_items + ['End']

    def build_graph_for_order(self, product_ids):

        def is_valid_position(x, y):
            is_in_bounds = 0 <= x < self.map_x and \
                           0 <= y < self.map_y

            is_open_position = self.map[x][y] != ItemRoutingSystem.ITEM_SYMBOL

            return is_in_bounds and is_open_position

        graph = {}

        directions = {
            "N": (0, 1),
            "S": (0, -1),
            "E": (1, 0),
            "W": (-1, 0)
        }

        for start in product_ids:
            for end in product_ids:

                # Skip for invalid pairs
                if start == end   or \
                   start == "End" or \
                   end == "Start" or \
                   start == "Start" and end == "End":
                    self.log(f"Skipping pair: {start, end}", print_type=PrintType.MINOR)
                    continue

                for start_dir in directions:
                    # Set to None if 'Start' node
                    start_dir = None if start == 'Start' else start_dir

                    # Calculate access point locations
                    valid_directions = {}
                    for end_dir, (dx, dy) in directions.items():

                        # Get target end position
                        if end == "End":
                            x, y = self.ending_position
                        else:
                            end_position = self.product_info[end]
                            x, y = end_position[0] + dx, end_position[1] + dy

                        # Don't add invalid position
                        if not is_valid_position(x, y):
                            self.log(f"Invalid access point position: {x, y}", print_type=PrintType.MINOR)
                            valid_directions[end_dir] = {
                                "location": None,
                                "cost": None,
                                "path": []
                            }

                        # Add valid positions & get path
                        else:
                            # Get starting position
                            if start == "Start":
                                start_position = self.starting_position
                            else:
                                start_x = self.product_info[start][0] + directions[start_dir][0]
                                start_y = self.product_info[start][1] + directions[start_dir][1]

                                if not is_valid_position(start_x, start_y):
                                    self.log(f"({start_x}, {start_y}) Not a VALID STARTING POSITION", print_type=PrintType.MINOR)
                                    continue

                                start_position = (start_x, start_y)


                            # Get path from starting position to target position
                            path, cost = self.dijkstra(self.map, start_position, (x, y))
                            updated_path = self.collapse_directions(path)

                            valid_directions[end_dir] = {
                                "location": (x, y),
                                "cost": cost,
                                "path": updated_path
                            }

                    if valid_directions:
                        graph[(start, end, start_dir)] = valid_directions

        return graph

    def print_matrix(self, matrix):
        print_matrix = {}

        for key, val in matrix.items():
            temp_val = deepcopy(val)
            for k, v in temp_val.items():
                if "path" in v:
                    v.pop("location")
                    v.pop("path")
                # v.pop()
            print_matrix[str(key)] = temp_val
        self.log(print_matrix)

    def matrix_reduction(self, matrix, source=None, dest=None):
        """
        Performs the matrix reduction for branch-and-bound
        Returns a reduced matrix
        """
        temp_matrix = deepcopy(matrix)
        reduction_cost = 0

        # when taking a path, set the corresponding row nad column to inf
        if source:
            reduction_cost += temp_matrix[ (source[0], source[1], source[2]) ][dest].get('cost')

            if (reduction_cost == INFINITY):
                return 0, temp_matrix

            for k,v in temp_matrix.items():
                if (source[0] == k[0]):
                    for direc in v:
                        v[direc]['cost'] = INFINITY
                if (source[1] == k[1]):
                    for direc in v:
                        v[direc]['cost'] = INFINITY

                self.log("Source set to Infinity", print_type=PrintType.MINOR)
                # print_matrix(temp_matrix)


        # Finds the minimum value to make a row have a zero
        for key in temp_matrix.keys():
            row_cost = INFINITY

            for k,v in temp_matrix.items():
                if (key[0] == k[0]):
                    for direc in v:
                        direc_cost = INFINITY if (v.get(direc).get('cost') is None) else v.get(direc).get('cost')
                        row_cost = min(row_cost, direc_cost)

            if (row_cost == INFINITY):
                row_cost = 0;

            # reduces the values in the matrix
            for k,v in temp_matrix.items():
                if (key[0] == k[0]):
                    for direc in v:
                        if (v.get(direc).get('cost') is None or v.get(direc).get('cost') == INFINITY):
                            v[direc]['cost'] = INFINITY
                        else:
                            v[direc]['cost'] = (v.get(direc).get('cost') - row_cost)

            if (row_cost != 0):
                self.log(f"Row: {row_cost}", print_type=PrintType.MINOR)

            reduction_cost += row_cost

        self.log("Final Child", print_type=PrintType.MINOR)
        # print_matrix(temp_matrix)
        self.log(f"Reduction Cost: {reduction_cost}", print_type=PrintType.MINOR)
        return reduction_cost, temp_matrix

    def branch_and_bound(self, graph, order):
        """
        Applies the branch and bound algorithm to generate a path
        """
        queue = []
        path = []

        # 1. Create Matrix

        # 2. Reduction
        self.log("Parent Matrix", print_type=PrintType.MINOR)
        reduced_cost, parent_matrix = self.matrix_reduction(graph)
        child_matrix = deepcopy(parent_matrix)

        # 3. Choose Random Start
        # start_node, dest_node, start_dir = random.choice( list(graph) )
        start_node, dest_node, start_dir = ('Start', 108335, None)

        # 4. Set Upper Bound
        upper_bound = order

        # 5. Traversal
        # (source, source_direction, level, cost, matrix, path)
        queue.append( (start_node, start_dir, 0, reduced_cost, child_matrix, path) )

        minimum_cost = INFINITY
        while queue:

            # Get lowest cost node
            index = 0
            if len(queue) > 1:
                lowest_cost_node = INFINITY
                for i, (source, source_direction, level, cost, matrix, src_path) in enumerate(queue):
                    if cost < lowest_cost_node:
                        index = i

            source, source_direction, level, cost, matrix, src_path = queue.pop(index)
            self.log(f"New Source: {source}", print_type=PrintType.MINOR)
            self.log(f"New Source Path: {cost} {src_path}", print_type=PrintType.MINOR)

            # If cost is greater than minimum cost of already found path, ignore
            if cost > minimum_cost:
                continue

            # If all items have been picked up
            if ( level == len(order) - 2 ):
                level_path = src_path + matrix[(source, "End", source_direction)]["N"]["path"]
                self.log(f"Reached Level: {level_path}", print_type=PrintType.MINOR)

                cost += matrix[(source, "End", source_direction)]["N"]["cost"]

                # Store path if minimum path
                if cost < minimum_cost:
                    final_path = level_path
                    minimum_cost = cost

            for (start, dest, src_dir), values in matrix.items():

                # Ignore "End" destination and other irrelevant entries
                if (source == start and source_direction == src_dir and dest != "End"):
                    highest_reduction = INFINITY
                    chosen_start = chosen_direc = None
                    chosen_matrix = None
                    child_path = []

                    for direc in values:
                        if values.get(direc).get('cost') is None or (values.get(direc).get('cost') == INFINITY):
                            self.log("Cost is None or Infinity", print_type=PrintType.MINOR)
                            continue

                        reduction, temp_matrix = self.matrix_reduction( matrix, (start, dest, src_dir), direc )

                        # Filter for minimum Single Access Point
                        if chosen_start is None or reduction + cost < highest_reduction:
                            chosen_start = dest
                            chosen_direc = direc
                            highest_reduction = reduction + cost
                            chosen_matrix = deepcopy(temp_matrix)
                            self.log(f"Before Child Path: {child_path}", print_type=PrintType.MINOR)
                            child_path = src_path + values[chosen_direc].get('path')
                            self.log(f"After Child Path: {child_path}", print_type=PrintType.MINOR)

                    if child_path:
                        self.log(f"Will Visit: {start}, {chosen_start}, {chosen_direc}", print_type=PrintType.MINOR)
                        queue.append( (chosen_start, chosen_direc, level + 1, cost + reduction, chosen_matrix, child_path) )

        return minimum_cost, final_path

    def localized_min_path(self, graph, order):
        """
        find the optimal path with multiple access points

        Args:
            ordered_list: an organized list of product ID

            graph: the distance graph using All-Pair-Shortest-Path

        Returns:
            path: a list of the locations
        """
        pre_node = None
        access_direction = None

        path = []
        total_cost = 0

        for product_id in order:
            # start position
            if product_id == 'Start':
                pre_node = product_id
                access_direction = None
                continue

            min_cost = float('inf')
            shortest_path = []

            # Choose one of the access points, and get the shortest path
            for access_point, val in graph[(pre_node, product_id, access_direction)].items():
                if val['cost'] is None:
                    break
                if min_cost is None or val['cost'] < min_cost:
                    min_cost = val['cost']
                    access_direction = access_point
                    shortest_path = val['path']

            if min_cost != float('inf'):
                total_cost += min_cost
            path += shortest_path
            pre_node = product_id

        self.log(f"Minimum Path: {path}", print_type=PrintType.MINOR)

        return total_cost, path

    def run_tsp_algorithm(self, graph, order, algorithm=None):
        def timeout_handler(signum, frame):
            self.log("Function timed out!")
            raise Exception("Function Timeout")

        # Setup timeout signal
        signal.signal(signal.SIGALRM, timeout_handler) # seconds
        signal.alarm(self.maximum_routing_time)

        if algorithm is None:
            algorithm = self.tsp_algorithm

        # Choose algorithm to run
        if algorithm == AlgoMethod.BRANCH_AND_BOUND:
            algo_func = self.branch_and_bound

        elif algorithm == AlgoMethod.LOCALIZED_MIN_PATH:
            algo_func = self.localized_min_path

        # Start Time for timing algorithm run time
        start_time = time.time()

        # Run Algorithm
        try:
            cost, path = algo_func(graph, order)

        except Exception as exc:
            # Algorithm timed out, return input order list
            self.log(exc)
            return None, order, self.maximum_routing_time

        # End Time for timing algorithm run time
        end_time = time.time()
        total_time = end_time - start_time
        self.log(f"Total Time: {(end_time - start_time):.4f}", print_type=PrintType.MINOR)

        # Stop timeout signal
        signal.alarm(0)

        return cost, path, total_time

    def gather_brute_force(self, targets):
        """
        Performs brute force algorithm to gather all valid permutations of desired path then
        finds shortest path.

        Args:
            targets (list of tuples): Positions of item.

        Returns:
            min_path (list of tuples): List of item positions to traverse in order.
        """
        if self.debug:
            start_time = time.time()

        smallest = None
        min_path = None

        result = []
        nodes = targets.copy()
        start = nodes.pop(0)
        end = nodes.pop()

        paths = []
        for node in itertools.permutations(nodes):
            temp_path = list(node)
            temp_path.insert(0, start)
            temp_path.append(end)
            paths.append(temp_path)

        for path in paths:
            distance = 0
            for i in range(len(path)):
                j = i + 1

                if j < len(path):
                    distance += abs(path[i][0] - path[j][0])
                    distance += abs(path[i][1] - path[j][1])

                    self.log(f"Path[i]: {path[i]} " \
                             f"Path[j]: {path[j]} " \
                             f"X Diff: {abs(path[i][0] - path[j][0])} " \
                             f"Y Diff: {abs(path[i][1] - path[j][1])} " \
                             f"Distance: {distance}",
                             print_type=PrintType.DEBUG)

            self.log(path, distance, print_type=PrintType.DEBUG)

            if smallest is None or distance < smallest:
                smallest = distance
                min_path = list(path).copy()

        if self.debug:
            end_time = time.time()
            self.log(f"Total Time: {(end_time - start_time):.4f}")
            self.log(f"Minimum Path: {min_path}")
            self.log(f"Shortest Number of Steps: {smallest}")

        return min_path

    def dijkstra(self, grid, start, target):
        """
        Performs dijkstra’s algorithm to gather shortest path to a desired position within the given grid.

        Args:
            grid(list of lists): Positions of items within the grid.

            target (tuples): Position of item to search for.

        Returns:
            path (list of tuples): List of item positions to traverse in order.
        """

        def is_valid_position(x, y):
            return 0 <= x < self.map_x and \
                   0 <= y < self.map_y

        x, y = target
        if not is_valid_position(x, y):
            self.log(f"Invalid target position: {target}", print_type=PrintType.MINOR)
            return [], None

        # Initialize the distance to all positions to infinity and to the starting position to 0
        dist = {(i, j): float('inf') for i in range(self.map_x) for j in range(self.map_y)}
        dist[start] = 0

        # Initialize the priority queue with the starting position
        pq = [(0, start)]

        # Initialize the previous position dictionary
        prev = {}
        total_cost = 0
        
        while pq:
            # Get the position with the smallest distance from the priority queue
            (cost, position) = heapq.heappop(pq)

            # If we've found the target, we're done
            if position == target:
                self.log(f"Found path to target {target} with cost {cost}!", print_type=PrintType.MINOR)
                total_cost = cost
                break

            # Check the neighbors of the current position
            for (dx, dy) in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                x, y = position[0] + dx, position[1] + dy

                self.log(position, (x, y), print_type=PrintType.MINOR)

                if not is_valid_position(x, y):
                    self.log(f"Skipping {(x, y)}: Invalid Position", print_type=PrintType.MINOR)
                    continue

                if grid[x][y] == ItemRoutingSystem.ITEM_SYMBOL:
                    self.log(f"Skipping {(x, y)}: Item", print_type=PrintType.MINOR)
                    continue

                # Compute the distance to the neighbor
                neighbor_cost = cost + 1

                # Update the distance and previous position if we've found a shorter path
                if neighbor_cost < dist[(x, y)]:
                    dist[(x, y)] = neighbor_cost
                    prev[(x, y)] = position
                    heapq.heappush(pq, (neighbor_cost, (x, y)))

        # Reconstruct the path
        path = []
        while position != start:
            path.append(position)
            position = prev[position]
        path.append(start)
        path.reverse()

        if target in path:
            self.log(f"Path found with cost {total_cost}: {path}", print_type=PrintType.MINOR)
            return path, total_cost
        else:
            self.log("Path not found", print_type=PrintType.DEBUG)
            return [], None

    def get_targets(self):
        """
        Gets a full list of targets. Uses stored worker starting position as first and last
        indices.

        Returns:
            targets (list of tuples): Positions of the worker and items.
        """
        if self.debug:
            start_time = time.time()

        targets = []

        if self.inserted_order:
            targets = self.inserted_order.copy()
            targets.insert(0, self.starting_position)
            targets.append(self.ending_position)

        if self.debug:
            end_time = time.time()
            self.log(f"Total Time: {(end_time - start_time):.4f}")

        return targets

    def collapse_directions(self, positions, skip_duplicate=True):
        result = []
        prev_x = prev_y = None
        prev_dir = direction = None

        for position in positions:
            x, y = position

            # Skip first position
            if prev_x is None:
                result.append(position)
                prev_x, prev_y = position
                continue

            # Determine Direction
            if prev_x != x:
                if prev_x > x:
                    direction = 'x+'
                else:
                    direction = 'x-'

            elif prev_y != y:
                if prev_y > y:
                    direction = 'y+'
                else:
                    direction = 'y-'

            if skip_duplicate:
                #  Skip second position
                if prev_dir is None:
                    prev_dir = direction
                    prev_x, prev_y = position
                    continue

            # Evaluate if direction changed
            if prev_dir != direction:
                prev_dir = direction
                result.append((prev_x, prev_y))

            prev_x, prev_y = position

        result.append(positions[-1])

        return result

    def get_descriptive_steps(self, positions, targets, collapse=True):
        """
        Gets a list of directions to gather all items beginning from the
        internal starting position and returning to the starting position.

        Algorithm gathers list of target items by prioritizing top rows and
        moves down to the last row.

        Items are then gathered in order by list of positions. The worker may only
        move in directions up, down, left, or right.

        Args:
            positions (list of tuples): List of item positions and in the order
                                to be traveled through.

            target (tuple): Target item to pick up

        Returns:
            path (list of str): List of English directions worker should take to gather
                                all items from starting position.
        """
        def is_at_access_point_to_target(position, target):
            is_right = (position[0] + 1) == target[0] and (position[1] == target[1])
            is_left  = (position[0] - 1) == target[0] and (position[1] == target[1])
            is_above = (position[0]) == target[0] and (position[1] + 1 == target[1])
            is_below = (position[0]) == target[0] and (position[1] - 1 == target[1])

            return is_right or is_left or is_above or is_below

        if collapse:
            updated_positions = self.collapse_directions(positions)

        # Manually remove duplicates
        else:
            prev_position = None
            updated_positions = []
            for position in positions:
                if prev_position == position:
                    continue

                prev_position = position
                updated_positions.append(position)

        start = updated_positions.pop(0)
        end = updated_positions.pop()

        path = []
        path.append(f"Start at position {start}!")
        current_position = start
        total_steps = 0

        # Preprocessing
        for position in updated_positions:
            prev_position = current_position
            move, steps = self.move_to_target(current_position, position)
            current_position = position
            total_steps += steps
            path.append(move)

            # At Access Point for target position
            for target in targets:
                if is_at_access_point_to_target(position, target):
                    path.append(f"Pickup item at {target}.")
                    break

        back_to_start, steps = self.move_to_target(current_position, end)
        total_steps += steps
        path.append(back_to_start)
        path.append("Pickup completed.")

        self.log(f"Total Steps: {total_steps}", print_type=PrintType.DEBUG)

        return path

    def get_items(self, option, target):
        """
        Helper function to retrieve list of directions depending on the
        gathering algorithm setting.

        Args:
            option (AlgoMethod): Gathering algorithm to be used.

        Returns:
            result (list of str): List of directions worker should take to gather
                                  all items from starting position.

        """
        path = []

        self.log(f"Inserted Item Order: {self.inserted_order}", print_type=PrintType.DEBUG)

        if option == AlgoMethod.ORDER_OF_INSERTION:
            # targets = self.get_targets()
            targets = [self.starting_position, target, self.ending_position]
            result = self.get_descriptive_steps(targets, [target])
            return result

        elif option == AlgoMethod.BRUTE_FORCE:
            # targets = self.get_targets()
            targets = [self.starting_position, target, self.ending_position]
            path = self.gather_brute_force(targets)
            result = self.get_descriptive_steps(path, [target])
            return result

        elif option == AlgoMethod.DIJKSTRA:
            shortest_path = []

            # Maximum Routing Time Setup
            timeout = False
            t_temp = 0.0
            t_thresh = self.maximum_routing_time
            t_start = time.time()

            # Run Dijkstra's for every position next to the target item
            for (dx, dy) in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                # Maximum Routing Time Check
                t_temp += time.time() - t_start
                if (t_temp >= t_thresh):
                    timeout = True
                    shortest_path = path
                    break

                x, y = target[0] + dx, target[1] + dy

                path, _ = self.dijkstra(self.map, self.starting_position, (x, y))

                if path:
                    if len(path) < len(shortest_path) or not shortest_path:
                        shortest_path = path

                self.log(f"Shortest Path for {(x, y)}: {shortest_path}", print_type=PrintType.DEBUG)

            result = []
            if shortest_path:
                self.log(f"Path to product is: {shortest_path}", print_type=PrintType.DEBUG)
                path, _ = self.dijkstra(self.map, shortest_path[-1], self.ending_position)
                shortest_path = shortest_path + path[1:]
                result = self.get_descriptive_steps(shortest_path, [target])
            elif timeout:
                path = [self.starting_position, target, self.ending_position]
                result = self.get_descriptive_steps(path, [target])
            return result

    def verify_settings_range(self, value, minimum, maximum):
        """
        Helper function to validate the value is within the specified range.

        Args:
            value   (int): Integer value to validate
            minimum (int): Smallest integer value allowed
            maximum (int): Largest integer value allowed

        Returns:
            True if value falls within minimum and maximum value.
            False otherwise.
        """
        try:
            if minimum <= int(value) <= maximum:
                return True
            elif int(value) < minimum:
                self.log(f"Try again! {value} is too small, must be minimum {minimum}.")
            elif int(value) > maximum:
                self.log(f"Try again! {value} is too large, must be maximum {maximum}.")
            else:
                self.log(f"Invalid option: {value}")
        except Exception as e:
            self.log(f"Invalid option: {value}")

        return False

    def set_map_size(self):
        """
        Sets internal map size to be generated.

        Requires user input to be within allowable range.

        Returns:
            success (bool): Successfully updated map size
        """
        banner = Menu("Set Map Size")
        banner.display()

        minimum_x = 5
        minimum_y = 5
        maximum_x = 40
        maximum_y = 40

        success = False

        x = input(f"Set Map X Size (Currently {self.map_x}, Minimum {minimum_x}, Max {maximum_x}): ")
        y = input(f"Set Map Y Size (Currently {self.map_y}, Minimum {minimum_y}, Max {maximum_y}): ")

        x_success = self.verify_settings_range(x, minimum_x, maximum_x)
        y_success = self.verify_settings_range(y, minimum_y, maximum_y)

        if x_success and y_success:
            self.map_x = int(x)
            self.map_y = int(y)
            success = True

        self.log(f"Current Map Size: {self.map_x}x{self.map_y}")
        return success

    def set_worker_starting_position(self):
        """
        Sets an internal starting position for the worker.

        Requires user input to be within limits of map size.

        Returns:
            success (bool): Status to indicate if worker position set successfully
        """
        success = False

        if self.worker_mode == GenerateMode.RANDOM:
            while not success:
                x = random.randint(0, self.map_x - 1)
                y = random.randint(0, self.map_y - 1)

                # Verify Item and Worker Positions do not overlap
                if (x, y) not in self.items:
                    self.starting_position = (x, y)
                    success = True

        elif self.worker_mode == GenerateMode.MANUAL:
            banner = Menu("Set Worker Starting Position")
            banner.display()

            while not success:
                x = input(
                    f"Set starting X position (Currently {self.starting_position[0]}, Maximum {self.map_x - 1}): ")
                y = input(
                    f"Set starting Y position (Currently {self.starting_position[1]}, Maximum {self.map_y - 1}): ")

                x_success = self.verify_settings_range(x, 0, self.map_x - 1)
                y_success = self.verify_settings_range(y, 0, self.map_y - 1)

                if x_success and y_success:

                    # Overlapping Item and Worker Positions
                    if (int(x), int(y)) in self.items:
                        self.log("Worker position is the same as a item position! Please Try Again.\n")

                    else:
                        self.starting_position = (int(x), int(y))
                        success = True

                self.log(f"Current Worker Starting Position: {self.starting_position}")
        return success


    def set_worker_ending_position(self):
        """
        Sets an internal starting position for the worker.

        Requires user input to be within limits of map size.

        Returns:
            success (bool): Status to indicate if worker position set successfully
        """
        success = False

        if self.worker_mode == GenerateMode.RANDOM:
            while not success:
                x = random.randint(0, self.map_x - 1)
                y = random.randint(0, self.map_y - 1)

                # Verify Item and Worker Positions do not overlap
                if (x, y) not in self.items:
                    self.ending_position = (x, y)
                    success = True

        elif self.worker_mode == GenerateMode.MANUAL:
            banner = Menu("Set Worker Ending Position")
            banner.display()

            while not success:
                x = input(
                    f"Set ending X position (Currently {self.ending_position[0]}, Maximum {self.map_x - 1}): ")
                y = input(
                    f"Set ending Y position (Currently {self.ending_position[1]}, Maximum {self.map_y - 1}): ")

                x_success = self.verify_settings_range(x, 0, self.map_x - 1)
                y_success = self.verify_settings_range(y, 0, self.map_y - 1)

                if x_success and y_success:

                    # Overlapping Item and Worker Positions
                    if (int(x), int(y)) in self.items:
                        self.log("Worker position is the same as a item position! Please Try Again.\n")

                    else:
                        self.ending_position = (int(x), int(y))
                        success = True

                self.log(f"Current Worker Ending Position: {self.ending_position}")
        return success


    def get_item_positions(self):
        """
        Gets item positions depending on current item position mode.

            Item Modes:
            1. Manual Mode
                A. Choose number of items
                B. Set positions for each item (cannot repeat position)

            2. Random Mode
                A. Set minimum number of items
                B. Set maximum number of items


        Returns:
            item_positions (list of tuples): Positions of items on the map.
        """
        item_positions = []

        if self.item_mode == GenerateMode.LOADED_FILE:
            if self.product_file:
                for product, position in self.product_info.items():
                    item_positions.append(position)

        elif self.item_mode == GenerateMode.RANDOM:
            number_of_items = random.randint(self.minimum_items, self.maximum_items)

            for _ in range(number_of_items):
                success = False
                while not success:
                    x = random.randint(0, self.map_x - 1)
                    y = random.randint(0, self.map_y - 1)

                    position = (x, y)

                    # Repeat Item Position
                    if position in item_positions:
                        self.log("Repeat item position! Please Try Again.\n", print_type=PrintType.DEBUG)

                    # Overlapping Item and Worker Positions
                    elif position == self.starting_position:
                        self.log("Item position is the same as the starting worker position! Please Try Again.\n",
                                 print_type=PrintType.DEBUG)

                    elif position == self.ending_position:
                        self.log("Item position is the same as the ending worker position! Please Try Again.\n",
                                 print_type=PrintType.DEBUG)

                    else:
                        item_positions.append(position)
                        success = True

        elif self.item_mode == GenerateMode.MANUAL:
            banner = Menu("Set Item Starting Position")
            banner.display()

            number_of_items = input(f"Set number of items (Up to {self.maximum_items}): ")

            item_success = self.verify_settings_range(number_of_items, self.minimum_items, self.maximum_items)

            if not item_success:
                self.log("Failed to set number of items in range.")
                return []

            for item in range(int(number_of_items)):
                x_success = False
                y_success = False

                while not x_success or not y_success:

                    self.log(f"\nFor Item #{item + 1}:")
                    x = input(f"Set X position (0 - {self.map_x - 1}): ")
                    y = input(f"Set Y position (0 - {self.map_y - 1}): ")

                    x_success = self.verify_settings_range(x, 0, self.map_x - 1)
                    y_success = self.verify_settings_range(y, 0, self.map_y - 1)

                    position = (int(x), int(y))
                    # Within Valid Range
                    if x_success and y_success:

                        # Repeat Item Position
                        if position in item_positions:
                            self.log("Repeat item position! Please Try Again.\n")

                        # Overlapping Item and Worker Positions
                        elif position == self.starting_position:
                            self.log("Item position is the same as the starting worker position! Please Try Again.\n")
                        elif position == self.ending_position:
                            self.log("Item position is the same as the ending worker position! Please Try Again.\n")

                        else:
                            item_positions.append(position)

                    else:
                        self.log("Invalid position! Please Try Again!\n")

        return item_positions

    def set_maximum_items_ordered(self):
        """
        Changes the setting for maximum number of items within a route.

        Returns:
            success (bool): Status whether settings were changed successfully.
        """
        banner = Menu("Set Maximum Items Ordered:")
        banner.display()

        success = False

        max_items = (self.map_x) * (self.map_y) - 1

        while not success:
            user_max = input(f"Set Maximum Items (Currently {self.maximum_items}, Maximum {max_items}): ")

            max_success = self.verify_settings_range(user_max, self.minimum_items, max_items)

            self.log(f"Item Max Success: {max_success}", print_type=PrintType.DEBUG)

            if max_success:
                self.maximum_items = int(user_max)
                success = True

            else:
                self.log("Invalid values, please try again!")

        self.log(f"Maximum Items: {self.maximum_items}")

        return success

    def set_routing_time_maximum(self):

        banner = Menu("Set Routing Time Maximum")
        banner.display()

        success = False

        routing_time = input(f"Set Maximum Routing Time in Seconds (Currently {self.maximum_routing_time}): ")

        max_success = self.verify_settings_range(routing_time, 0, 1440)
        if (max_success):
            success = True
            self.maximum_routing_time = int(routing_time)
        else:
            self.log("Invalid value, please try again!")

        self.log(f"Maximum Routing Time in Seconds: {self.maximum_routing_time}")

        return success

    def handle_option(self, option):
        """
        Handles menu options for main application and corresponding submenus.

        Args:
            option (str): Choice user chooses from main menu.
        """
        # View Map
        update = True
        clear = True

        if option == '1':
            # Load product file if one hasn't been loaded yet
            if self.product_file is None:
                if update:
                    self.display_menu(MenuType.LOAD_PRODUCT_FILE, clear=clear)
                else:
                    update = True
                    clear = True

                # Set Product File Name
                success = False
                while not success:
                    product_file = input("Enter product filename: ")

                    success = self.load_product_file(product_file.rstrip())

                    if success:
                        self.item_mode = GenerateMode.LOADED_FILE
                        self.items = self.get_item_positions()
                        self.map, self.inserted_order = self.generate_map()

                    else:
                        self.log(f"File '{product_file}' was not found, please try entering full path to file!")

            # Display map after file is loaded
            if update:
                self.display_map()
            else:
                update = True

            # Don't clear for first View Map Menu
            clear = False

            while True:
                # Create View Map menu
                if update:
                    self.display_menu(MenuType.VIEW_MAP, clear=clear)
                else:
                    update = True
                    clear = True

                # Handle menu options
                suboption = input("> ")

                # Create Order
                if suboption == '1':
                    product_id = None
                    order = []
                    item_positions = []

                    if self.debug:
                        self.log("Product IDs:")
                        for i, product in enumerate(self.product_info, 1):
                            self.log(f"{i}. {product}")

                    while product_id != "f":
                        product_id = input("Enter Product ID ('f' to finish order): ").rstrip()

                        if product_id == "f":
                            break

                        elif product_id and int(product_id) in self.product_info:
                            order.append(int(product_id))

                        else:
                            self.log(f"Product ID '{product_id}' was not found, please try again!")

                    if order:
                        items = "items" if len(order) > 1 else "item"
                        self.log(f"\n",
                                 f"You completed your order of {len(order)} {items}!\n",
                                 f"You ordered:")

                        for i, product in enumerate(order, 1):
                            self.log(f"  {i}. {product}")
                            item_positions.append(self.product_info[product])

                    original_map = deepcopy(self.map)

                    # Label ordered items
                    for position in item_positions:
                        x, y = position
                        self.map[x][y] = ItemRoutingSystem.ORDERED_ITEM_SYMBOL

                    self.display_map()

                    # Restore Original Map
                    self.map = deepcopy(original_map)

                    self.order = self.process_order(order)
                    self.graph = self.build_graph_for_order(self.order)

                # Get Path for Order
                elif suboption == '2':
                    if self.order:
                        if self.graph is None:
                            self.graph = self.build_graph_for_order(self.order)

                        cost, path, run_time = self.run_tsp_algorithm(self.graph, self.order)

                        # Algo Timed Out
                        if run_time == self.maximum_routing_time:
                            cost, path, run_time = self.run_tsp_algorithm(self.graph, self.order, AlgoMethod.LOCALIZED_MIN_PATH)


                        target_locations = []
                        for product in self.order:
                            if product == 'Start' or product == 'End':
                                continue

                            location = self.product_info.get(product)
                            if location:
                                target_locations.append(location)

                        steps = self.get_descriptive_steps(path, target_locations, collapse=False)

                        if steps:
                            self.display_path_in_map(steps)

                            self.log("Directions:")
                            self.log("-----------")
                            for step, action in enumerate(steps, 1):
                                self.log(f"{step}. {action}")

                        else:
                            self.log(f"Path to {product_id} was not found!")

                    else:
                        self.log("No existing order! Please create an order first!")
                # Get Path to Product
                elif suboption == '3':
                    self.log("Get Path to Product")

                    # Request Product ID to find path for
                    complete = False
                    while not complete:
                        try:
                            if self.debug:
                                self.log("Product IDs:")
                                for i, product in enumerate(self.product_info, 1):
                                    self.log(f"{i}. {product}")

                            product_id = input("Enter Product ID: ")
                            item_position = self.product_info[int(product_id)]

                            complete = True

                        except ValueError:
                            self.log(f"Invalid Product ID '{product_id}', please try again!")

                        except KeyError:
                            self.log("Product was not found!")
                            complete = False

                    steps = self.get_items(self.gathering_algo, item_position)

                    if steps:
                        self.display_path_in_map(steps)

                        self.log("Directions:")
                        self.log("-----------")
                        for step, action in enumerate(steps, 1):
                            self.log(f"{step}. {action}")
                    else:
                        self.log(f"Path to {product_id} was not found!")

                    clear = False

                # Get Location of Product
                elif suboption == '4':
                    self.log("Get Location of Product")

                    complete = False
                    while not complete:
                        try:
                            if self.debug:
                                self.log("Product IDs:")
                                for i, product in enumerate(self.product_info, 1):
                                    self.log(f"{i}. {product}")

                            product_id = input("Enter Product ID: ")

                            self.log(
                                f"Product `{product_id}` is located at position {self.product_info[int(product_id)]}.")
                            complete = True

                        except ValueError:
                            self.log(f"Invalid Product ID '{product_id}', please try again!")

                        except KeyError:
                            self.log("Product was not found!")
                            complete = True

                # Back
                elif suboption == '5':
                    # Debug Mode: Generate New Map
                    if self.debug:
                        self.log("Generate New Map")
                        self.items = self.get_item_positions()
                        self.map, self.inserted_order = self.generate_map()
                        self.display_map()

                        clear = False

                    # Normal Mode: Back
                    else:
                        break

                # Debug Mode: Back
                elif suboption == '6' and self.debug:
                    break

                else:
                    self.log("Invalid choice. Try again.")
                    update = False

        # Settings
        elif option == '2':
            clear = True

            while True:
                # Create Settings Menu
                if update:
                    self.display_menu(MenuType.SETTINGS, clear=clear)
                    clear = True
                else:
                    update = True

                # Handle Settings Menu Options
                suboption = input("> ")

                # Load Product File
                if suboption == '1':
                    if update:
                        self.display_menu(MenuType.LOAD_PRODUCT_FILE, clear=clear)
                    else:
                        update = True
                        clear = True

                    # Set Product File Name
                    success = False
                    while not success:
                        product_file = input("Enter product filename: ")

                        success = self.load_product_file(product_file)

                        if success:
                            self.item_mode = GenerateMode.LOADED_FILE
                            self.items = self.get_item_positions()

                            # Set new map parameters
                            max_x = self.map_x
                            max_y = self.map_y

                            for item in self.items:
                                x, y = item
                                if x > max_x:
                                    max_x = x
                                if y > max_y:
                                    max_y = y

                            self.map_x = max_x + 1
                            self.map_y = max_y + 1

                            self.map, self.inserted_order = self.generate_map()

                        else:
                            self.log(f"File '{product_file}' was not found, please try entering full path to file!")

                # Set Worker Starting Position
                elif suboption == '2':
                    while True:
                        if update:
                            self.display_menu(MenuType.WORKER_START_POSITION, clear=clear)
                        else:
                            update = True
                            clear = True

                        # Give Worker Mode options in debug mode
                        if self.debug:
                            mode_option = input(f"Set Worker Position Mode (Currently {self.worker_mode}): ")

                            # Set random starting position
                            if mode_option == '1':
                                self.worker_mode = GenerateMode.RANDOM

                                self.set_worker_starting_position()

                                # Generate map with new starting position
                                self.map, self.inserted_order = self.generate_map()
                                break

                            # Set manual starting position
                            elif mode_option == '2':
                                self.worker_mode = GenerateMode.MANUAL

                                self.set_worker_starting_position()

                                # Generate map with new starting position
                                self.map, self.inserted_order = self.generate_map()
                                break

                            # Back
                            elif mode_option == '3':
                                break

                            else:
                                self.log("Invalid choice. Try again.")
                                update = False
                                clear = False

                        # Normal case, always request user input
                        else:
                            self.worker_mode = GenerateMode.MANUAL

                            self.set_worker_starting_position()

                            # Generate map with new starting position
                            self.map, self.inserted_order = self.generate_map()

                            # Go back to Settings menu
                            break

                # Set Worker Ending Position
                elif suboption == '3':
                    while True:
                        if update:
                            self.display_menu(MenuType.WORKER_ENDING_POSITION, clear=clear)
                        else:
                            update = True
                            clear = True

                        # Give Worker Mode options in debug mode
                        if self.debug:
                            mode_option = input(f"Set Worker Position Mode (Currently {self.worker_mode}): ")

                            # Set random starting position
                            if mode_option == '1':
                                self.worker_mode = GenerateMode.RANDOM

                                self.set_worker_ending_position()

                                # Generate map with new starting position
                                self.map, self.inserted_order = self.generate_map()
                                break

                            # Set manual starting position
                            elif mode_option == '2':
                                self.worker_mode = GenerateMode.MANUAL

                                self.set_worker_ending_position()

                                # Generate map with new starting position
                                self.map, self.inserted_order = self.generate_map()
                                break

                            # Back
                            elif mode_option == '3':
                                break

                            else:
                                self.log("Invalid choice. Try again.")
                                update = False
                                clear = False

                        # Normal case, always request user input
                        else:
                            self.worker_mode = GenerateMode.MANUAL

                            self.set_worker_ending_position()

                            # Generate map with new starting position
                            self.map, self.inserted_order = self.generate_map()

                            # Go back to Settings menu
                            break


                # Set Maximum Items Ordered Amount
                elif suboption == '4':
                    self.set_maximum_items_ordered()
                    self.items = self.get_item_positions()

                elif suboption == '5':
                    self.set_routing_time_maximum()

                # Toggle Debug
                elif suboption == '6':
                    self.debug = not self.debug

                # Debug Mode:       Advanced Settings
                # Non-Debug Mode:   Back
                elif suboption == '7':
                    # Debug Mode: Advanced Settings
                    if self.debug:
                        while True:
                            if update:
                                self.display_menu(MenuType.ADVANCED_SETTINGS, clear=clear)
                            else:
                                update = True
                                clear = True

                            adv_option = input("> ")

                            # Set Map Size
                            if adv_option == '1':
                                clear = self.set_map_size()
                                self.map, self.inserted_order = self.generate_map()

                            # Set Item Position Mode
                            elif adv_option == '2':
                                while True:
                                    if update:
                                        self.display_menu(MenuType.ITEM_POSITION, clear=clear)
                                    else:
                                        update = True
                                        clear = True

                                    mode_option = input(f"Set Item Position Mode (Currently {self.item_mode}): ")

                                    # Set random starting position
                                    if mode_option == '1':
                                        self.item_mode = GenerateMode.RANDOM

                                        self.items = self.get_item_positions()

                                        # Generate map with new item positions
                                        self.map, self.inserted_order = self.generate_map()
                                        break

                                    # Set manual starting position
                                    elif mode_option == '2':
                                        self.item_mode = GenerateMode.MANUAL

                                        self.items = self.get_item_positions()

                                        # Generate map with new item positions
                                        self.map, self.inserted_order = self.generate_map()
                                        break

                                    # Back
                                    elif mode_option == '3':
                                        break

                                    else:
                                        self.log("Invalid choice. Try again.")
                                        update = False
                                        clear = False

                            # Set Map Orientation
                            elif adv_option == '3':
                                print("Set Map Orientation is currently under development!")
                                update = False
                                clear = False

                            # Set Gather Algorithm Method
                            elif adv_option == '4':
                                while True:
                                    if update:
                                        self.display_menu(MenuType.GATHER_ALGO_METHOD, clear=clear)
                                    else:
                                        update = True
                                        clear = True

                                    algo_option = input("> ")

                                    # Order of Insertion
                                    if algo_option == '1':
                                        self.gathering_algo = AlgoMethod.ORDER_OF_INSERTION
                                        break

                                    # Brute Force
                                    elif algo_option == '2':
                                        self.gathering_algo = AlgoMethod.BRUTE_FORCE
                                        break

                                    # Dijkstra
                                    elif algo_option == '3':
                                        self.gathering_algo = AlgoMethod.DIJKSTRA
                                        break

                                    # Back
                                    elif algo_option == '4':
                                        break

                                    else:
                                        self.log("Invalid choice. Try again.")
                                        update = False
                                        clear = False

                            # Set TSP Algorithm Method
                            elif adv_option == '5':
                                while True:
                                    if update:
                                        self.display_menu(MenuType.TSP_ALGO_METHOD, clear=clear)
                                    else:
                                        update = True
                                        clear = True

                                    algo_option = input("> ")

                                    # Branch and Bound
                                    if algo_option == '1':
                                        self.tsp_algorithm = AlgoMethod.BRANCH_AND_BOUND
                                        break

                                    # Custom Algorithm
                                    elif algo_option == '2':
                                        self.tsp_algorithm = AlgoMethod.LOCALIZED_MIN_PATH
                                        break

                                    # Back
                                    elif algo_option == '3':
                                        break

                                    else:
                                        self.log("Invalid choice. Try again.")
                                        update = False
                                        clear = False

                            # Load Test Case File
                            elif adv_option == '6':
                                if update:
                                    self.display_menu(MenuType.LOAD_TEST_CASE_FILE, clear=clear)
                                else:
                                    update = True
                                    clear = True

                                # Set Product File Name
                                success = False
                                while not success:
                                    test_case_file = input("Enter product filename: ")

                                    success = self.load_test_case_file(test_case_file)

                                    if success:
                                        self.test_case_file = test_case_file

                                        if self.debug:
                                            for test_case in self.test_cases:
                                                size, ids = test_case
                                                self.log(size, ids, print_type=PrintType.MINOR)

                                    else:
                                        self.log(f"File '{test_case_file}' was not found, please try entering full path to file!")

                            # Run Test Cases
                            elif adv_option == '7':
                                if self.test_case_file and self.test_product_file:
                                    success = self.load_product_file(self.test_product_file)

                                    if not success:
                                        self.log(f"Failed to load test case product file {self.test_product_file}!\n" \
                                                 f"Check if product file exists in correct location.\n"               \
                                                 f"Change path in loaded test case file as needed.\n")

                                    else:
                                        # Generate Test Map
                                        self.item_mode = GenerateMode.LOADED_FILE
                                        self.items = self.get_item_positions()

                                        # Set new map parameters
                                        max_x = self.map_x
                                        max_y = self.map_y

                                        for item in self.items:
                                            x, y = item
                                            if x > max_x:
                                                max_x = x
                                            if y > max_y:
                                                max_y = y

                                        self.map_x = max_x + 1
                                        self.map_y = max_y + 1

                                        self.map, self.inserted_order = self.generate_map()

                                        # Setup Test Case
                                        passed = 0
                                        failed = 0
                                        cases_failed = {}

                                        # Get Test System Information
                                        system_info = {
                                            "Machine": platform.machine(),
                                            "Platform": platform.platform(),
                                            "System": platform.system(),
                                            "Kernel Version": platform.release()
                                        }

                                        self.log("\nSystem Information\n"\
                                                 "------------------")
                                        for k, v in system_info.items():
                                            self.log(f"{k}: \n\t{v}")
                                        self.log("")

                                        # Run All Test Cases
                                        for test_case in self.test_cases:
                                            size, product_ids = test_case
                                            cases_failed[size] = {}

                                            # Get Locations
                                            for product_id in product_ids:
                                                location = self.product_info.get(product_id)

                                                if location is None:
                                                    if "Location" not in cases_failed:
                                                        cases_failed["Location"] = []

                                                    failed += 1
                                                    cases_failed[size]["Location"].append(product_id)

                                                    self.log(f"Failed to get location for Product '{product_id}'.")

                                                else:
                                                    passed += 1

                                            # Test Algorithms to Get Paths
                                            self.log(f"Test Case: Size {size}\n"    \
                                                      "----------------------")
                                            grouped_items = self.process_order(product_ids)
                                            graph = self.build_graph_for_order(grouped_items)

                                            # Run Branch and Bound
                                            cost, path, run_time = self.run_tsp_algorithm(graph, grouped_items, AlgoMethod.BRANCH_AND_BOUND)

                                            # Algorithm Timed Out
                                            if cost is None:
                                                failed += 1
                                                cases_failed[size]["Branch and Bound"] = "Timeout"
                                                self.log("Failed Branch and Bound")

                                            else:
                                                self.log("Completed Branch and Bound!")

                                            self.log(f"    Time: {run_time:.6f}")
                                            self.log(f"    Cost: {cost}")
                                            self.log(f"    Path: {path}")
                                            self.log("")


                                            # Run Custom Algorithm
                                            cost, path, run_time = self.run_tsp_algorithm(graph, grouped_items, AlgoMethod.LOCALIZED_MIN_PATH)

                                            # Algorithm Timed Out
                                            if cost is None:
                                                failed += 1
                                                cases_failed[size]["Localized Minimum Path"] = "Timeout"
                                                self.log("Failed Localized Minimum Path")

                                            else:
                                                self.log("Completed Localized Minimum Path!")

                                            self.log(f"    Time: {run_time:.6f}")
                                            self.log(f"    Cost: {cost}")
                                            self.log(f"    Path: {path}")
                                            self.log("")

                                        self.log(f"Results\n"             \
                                                 f"---------\n"           \
                                                 f"Passed: {passed}\n"    \
                                                 f"Failed: {failed}\n"    \
                                                 f"Total:  {passed + failed}")
                                        self.log("")

                                        # Display Failures
                                        if failed:
                                            self.log("Failures\n" \
                                                     "---------")
                                            for size, fails in cases_failed.items():
                                                if fails:
                                                    self.log(f"{size}: ")
                                                    for case, reason in fails.items():
                                                        self.log(f"    {case}: {reason}")

                                else:
                                    self.log("No test cases to run! Must load test case file first!")

                                update = True
                                clear = False

                            # Back
                            elif adv_option == '8':
                                break

                            else:
                                self.log("Invalid choice. Try again.")
                                update = False
                                clear = False

                    # Non-Debug Mode: Back
                    else:
                        break

                # Debug Mode: Back
                elif suboption == '8' and self.debug:
                    break

                else:
                    self.log("Invalid choice. Try again.")
                    update = False

        # Exit
        elif option == '3':
            self.log("Exiting...")
            sys.exit()
        else:
            self.log("Invalid choice. Try again.")
            update = False

    def run(self):
        """
        Helper function to run the application. Loops the main menu until the user
        chooses to exit.
        """
        while True:
            self.display_menu(MenuType.MAIN_MENU)

            choice = input("> ")
            self.handle_option(choice)


def main():
    """
    Main application code to run the ItemRoutingSystem application.
    """
    app = ItemRoutingSystem()
    app.run()


if __name__ == "__main__":
    main()
