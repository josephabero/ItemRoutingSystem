"""
Welcome to Item Routing System!

Authors: Supa Dupa Logistics, ChatGPT

ItemRoutingSystem is a text-based application used to provide store workers with
directions to gather shopping items around a warehouse.
"""

from constants import *
from menu import Menu
from queue import PriorityQueue

from copy import deepcopy
import heapq
import itertools
from math import ceil
import os
import platform
import random
import signal
import sys
import time

def timeout_handler(signum, frame):
    raise TimeoutError

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
        self.order_file = None
        self.order_info = []
        self.order_number = 0

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
        self.maximum_items = 20
        self.items = self.get_item_positions()

        # Default algorithm
        self.gathering_algo = AlgoMethod.DIJKSTRA
        self.tsp_algorithm = AlgoMethod.REPETITIVE_NEAREST_NEIGHBOR
        self.maximum_routing_time = 60
        self.bnb_access_type = AccessType.MULTI_ACCESS

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
        reason = None

        original_starting_worker = self.starting_position
        original_ending_worker = self.ending_position

        try:
            self.product_file = product_file_name
            f = open(product_file_name, 'r')
            next(f)

            for line in f:
                fields = line.strip().split()
                self.product_info[int(fields[0])] = int(float(fields[1])), int(float(fields[2]))
            f.close()

            # Successfully loaded, reset worker positions
            self.log("Loaded product file, resetting worker positions!")
            self.starting_position = (0, 0)
            self.ending_position = (0, 0)

        except FileNotFoundError:
            reason = FileNotFoundError
            success = False

        except ValueError:
            reason = ValueError
            success = False

        except Exception as e:
            reason = e
            success = False

        return success, reason

    def load_order_file(self, order_file_name):
        success = True
        reason = None
        original_order_info = deepcopy(self.order_info)

        try:
            self.order_file = order_file_name
            self.order_info = []

            f = open(order_file_name, 'r')

            for line in f:
                formatted_line = [ int(l.lstrip()) for l in line.rstrip().split(",") ]
                self.order_info.append(formatted_line)
            f.close()

        except FileNotFoundError:
            reason = FileNotFoundError
            success = False

        except ValueError:
            reason = ValueError
            success = False

        except Exception as e:
            reason = e
            success = False

        if not success:
            self.order_file = None
            self.order_info = original_order_info

        return success, reason

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

        elif menu_type == MenuType.CREATE_ORDER:
            menu = Menu("Create Order")
            menu.add_option(1, "Individual Order")
            menu.add_option(2, "Multiple Orders From File")
            menu.add_option(3, "Back")

        elif menu_type == MenuType.MULTIPLE_ORDERS:
            menu = Menu("Multiple Orders")
            menu.add_option(1, "Load New Order File")
            menu.add_option(2, f"Continue to Next Order (Currently {self.order_number})")
            menu.add_option(3, "Choose Order")
            menu.add_option(4, "Back")

        elif menu_type == MenuType.SETTINGS:
            menu = Menu("Settings Menu")
            menu.add_option(1, "Load Product File")
            menu.add_option(2, "Set Worker Starting Position Mode")
            menu.add_option(3, "Set Worker Ending Position Mode")
            menu.add_option(4, "Set Maximum Items Ordered")
            menu.add_option(5, "Set Maximum Routing Time")
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
            menu.add_option(6, "Set TSP Access Type")
            menu.add_option(7, "Load Test Case File")
            menu.add_option(8, "Run Test Cases")
            menu.add_option(9, "Back")

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
                   f"  TSP Access Type: {self.bnb_access_type}\n" \
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
            menu.add_option(3, "Repetitive Nearest Neighbor")
            menu.add_option(4, "Back")

        elif menu_type == MenuType.TSP_ACCESS_TYPE:
            menu = Menu("Set TSP Access Type")
            menu.add_option(1, "Single Access Point")
            menu.add_option(2, "Multi Access Point")
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

    def display_map(self, map_layout=None, map_only=False):
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
              f"  Worker Settings:\n" \
                   f"   Starting Position: {self.starting_position}\n" \
                   f"   Ending Position: {self.ending_position}\n" \
              Ordered Item Maximum: 8
              Gathering Algorithm: Dijkstra
              Maximum Time To Process: 60
              Debug Mode: False
        """
        banner_length = 60
        banner = Menu("Warehouse Map Layout")
        banner.display()

        grid = []

        if map_layout is None:
            map_layout = self.map

        for y in reversed(range(len(map_layout[0]))):
            col = []
            for x in range(len(map_layout)):
                # Only display item if its position is within defined grid
                if x < self.map_x and y < self.map_y:
                    col.append(map_layout[x][y])
            grid.append(col)

        for i, col in zip(reversed(range(len(grid))), grid):
            row_string = f"{i:2} "

            for j, val in enumerate(col):
                row_string += val + " " * len(str(j))

            self.log(row_string.center(banner_length))

        left_spacing = len(str(i)) + 2
        self.log(f"{' ':{left_spacing}}" + " ".join(str(i) for i in range(len(map_layout))).center(banner_length))

        if not map_only:

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
                            f"  Worker Settings:\n" \
                            f"   Starting Position: {self.starting_position}\n" \
                            f"   Ending Position: {self.ending_position}\n" \
                            f"  Ordered Item Maximum: {self.maximum_items}\n" \
                            f"  Algorithm: {self.tsp_algorithm}\n" \
                            f"  Maximum Routing Time: {self.maximum_routing_time}\n" \
                            f"  Debug Mode: {self.debug}\n"

            if self.tsp_algorithm == AlgoMethod.BRANCH_AND_BOUND:
                settings_info = "Current Settings:\n" \
                            f"  Worker Settings:\n" \
                            f"   Starting Position: {self.starting_position}\n" \
                            f"   Ending Position: {self.ending_position}\n" \
                            f"  Ordered Item Maximum: {self.maximum_items}\n" \
                            f"  Algorithm: {self.tsp_algorithm}\n" \
                            f"    Item Access Type: {self.bnb_access_type}\n" \
                            f"  Maximum Routing Time: {self.maximum_routing_time}\n" \
                            f"  Debug Mode: {self.debug}\n"

            self.log(settings_info)

    def display_path_in_map(self, steps, map_layout=None, map_only=False):
        path = []

        if map_layout is None:
            map_layout = self.map

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

            elif step.startswith("Pickup item at"):
                parsed = step.split(" ")

                end_x = int(parsed[3][1:-1])
                end_y = int(parsed[4][:-2])

                step_values = {
                    "type": "pickup",
                    "end": (end_x, end_y)
                }

                path.append(step_values)

            elif step.startswith("Pickup item"):
                parsed = step.split(" ")


                end_x = int(parsed[4][1:-1])
                end_y = int(parsed[5][:-2])

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

                    if map_layout[x][y] == ItemRoutingSystem.WORKER_START_SYMBOL or \
                       map_layout[x][y] == ItemRoutingSystem.WORKER_END_SYMBOL:
                        continue

                    elif map_layout[x][y] == '_':
                        map_layout[x][y] = arrows[step["direction"]]

                    elif map_layout[x][y] in [arrows["up"], arrows["down"]]:
                        map_layout[x][y] = arrows["up_down"]

                    elif map_layout[x][y] in [arrows["left"], arrows["right"]]:
                        map_layout[x][y] = arrows["left_right"]

            elif step["type"] == "pickup":
                x, y = step["end"]
                map_layout[x][y] = ItemRoutingSystem.ORDERED_ITEM_SYMBOL

        self.display_map(map_layout=map_layout, map_only=map_only)

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

        # Initialize Graph with End -> Start node of cost 0
        graph = {
            ('End', 'Start', None): {
                None: {
                    'location': self.ending_position,
                    'cost': 0,
                    'path': [(self.ending_position), self.starting_position]
                }
            }
        }

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
                            end_dir = None  # Always set ending direction to None for 'End' node
                        else:
                            end_position = self.product_info[end]
                            x, y = end_position[0] + dx, end_position[1] + dy

                        # Don't add invalid position
                        if not is_valid_position(x, y):
                            self.log(f"Invalid access point position: {x, y}", print_type=PrintType.MINOR)
                            continue

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
        # self.log(print_matrix)
        return print_matrix

    def matrix_reduction(self, matrix, source=None, dest=None):
        """
        Performs the matrix reduction for branch-and-bound
        Returns a reduced matrix
        """
        global INCREMENT
        temp_matrix = deepcopy(matrix)
        reduction_cost = 0

        # when taking a path, set the corresponding row nad column to inf
        if source:
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
            zero_col_cost = INFINITY
			
            for k,v in temp_matrix.items():
                if (key[0] == k[0]):
                    for direc in v:
                        direc_cost = INFINITY if (v.get(direc).get('cost') is None) else v.get(direc).get('cost')
                        row_cost = min(row_cost, direc_cost)
                # minimum zero col
                elif ('End' == k[1]):
                    for direc in v:
                        zero_direc_cost = INFINITY if (v.get(direc).get('cost') is None) else v.get(direc).get('cost')
                        zero_col_cost = min(zero_col_cost, zero_direc_cost)
				
            if (row_cost == INFINITY):
                row_cost = 0;
            if (zero_col_cost == INFINITY):
                zero_col_cost = 0;

            # reduces the values in the matrix
            for k,v in temp_matrix.items():
                if (key[0] == k[0]):
                    for direc in v:
                        if (v.get(direc).get('cost') is None or v.get(direc).get('cost') == INFINITY):
                            v[direc]['cost'] = INFINITY
                        else:
                            v[direc]['cost'] = (v.get(direc).get('cost') - row_cost)
							
                # zero col zeroing
                elif ('End' == k[1]):
                    for direc in v:
                        if (v.get(direc).get('cost') is None or v.get(direc).get('cost') == INFINITY):
                            v[direc]['cost'] = INFINITY
                        else:
                            v[direc]['cost'] = (v.get(direc).get('cost') - zero_col_cost)

            if (row_cost != 0):
                self.log(f"Row: {row_cost}", print_type=PrintType.MINOR)

            reduction_cost += row_cost + zero_col_cost

        self.log("Final Child", print_type=PrintType.MINOR)
        self.log(f"Reduction Cost: {reduction_cost}", print_type=PrintType.MINOR)
        return reduction_cost, temp_matrix


    def branch_and_bound(self, graph, order):
        """
        Applies the branch and bound algorithm to generate a path
        """
        def binary_search(arr, low, high, target):
            # Check base case
            cost_index = 2

            if high >= low:

                mid = (high + low) // 2

                # If element is present at the middle itself
                if arr[mid][cost_index] == target:
                    return mid

                # If element is smaller than mid, then it can only
                # be present in left subarray
                elif arr[mid][cost_index] > target:
                    return binary_search(arr, low, mid - 1, target)

                # Else the element can only be present in right subarray
                else:
                    return binary_search(arr, mid + 1, high, target)

            else:
                # Element is not present in the array
                return -1

        # Setup timeout signal
        signal.signal(signal.SIGALRM, timeout_handler) # seconds
        signal.alarm(ceil(self.maximum_routing_time))

        queue = []
        final_path = []

        try:
            # 1. Create Matrix
            # 2. Reduction
            reduced_cost, parent_matrix = self.matrix_reduction(graph)
            child_matrix = deepcopy(parent_matrix)

            # 3. Choose Random Start
            start_node, dest_node, start_dir = random.choice( list(graph) )

            # 4. Set Upper Bound
            upper_bound = order

            # 5. Traversal
            # (source, source_direction, cost, matrix, path)

            # For first traversal, ignore start_dir, add all of surrounding access points to traverse
            for (start, dest, src_dir), values in parent_matrix.items():
                if start_node == start:
                    child_path = [(start, src_dir)]
                    queue.append( (start, src_dir, reduced_cost, child_matrix, child_path) )

            minimum_cost = INFINITY
            cached_matrices = {}
            while queue:

                # Get lowest cost node
                index = 0
                if len(queue) > 1:
                    lowest_cost_node = INFINITY
                    for i, (source, source_direction, cost, matrix, src_path) in enumerate(queue):
                        if cost < lowest_cost_node:
                            index = i

                source, source_direction, cost, matrix, src_path = queue.pop(index)

                # If cost is greater than minimum cost of already found path, ignore
                if cost > minimum_cost:
                    continue

                # If all nodes have been visited
                if len(src_path) == len(order):
                    final_node, final_dir = src_path[0]
                    path_cost = matrix[(source, final_node, source_direction)][final_dir]["cost"]
                    final_reduction, final_matrix = self.matrix_reduction(matrix)

                    total_final_reduction = cost + path_cost + final_reduction

                    # Store path if minimum path
                    if total_final_reduction <= minimum_cost:
                        final_path = src_path
                        minimum_cost = total_final_reduction

                for (start, dest, src_dir), access_points in matrix.items():
                    # Ignore other irrelevant entries
                    if source == start and source_direction == src_dir:

                        # Check if destination is already in path
                        found = False
                        for node in src_path:
                            if dest == node[0]:
                                found = True
                                break

                        if found:
                            continue

                        child_path = []

                        if self.bnb_access_type == AccessType.SINGLE_ACCESS:
                            highest_reduction = INFINITY
                            chosen_start = chosen_direc = None
                            chosen_matrix = None

                        for direc in access_points:
                            if access_points[direc].get('cost') is None or (access_points[direc].get('cost') == INFINITY):
                                continue

                            if (str(src_path), dest) in cached_matrices:
                                reduction, temp_matrix = cached_matrices[(str(src_path), dest)]

                            else:
                                reduction, temp_matrix = self.matrix_reduction( matrix, (start, dest, src_dir), direc )
                                cached_matrices[(str(src_path), dest)] = (reduction, temp_matrix)

                            total_reduction = cost + access_points[direc].get('cost') + reduction

                            if self.bnb_access_type == AccessType.SINGLE_ACCESS:
                                # Filter for minimum Single Access Point
                                if chosen_start is None or total_reduction < highest_reduction:
                                    chosen_start = dest
                                    chosen_direc = direc
                                    highest_reduction = total_reduction
                                    chosen_matrix = deepcopy(temp_matrix)

                                    child_path = src_path + [(dest, direc)]

                            elif self.bnb_access_type == AccessType.MULTI_ACCESS:
                                child_path = src_path + [(dest, direc)]
                                node_to_visit = (dest, direc, total_reduction, deepcopy(temp_matrix), child_path)

                                if (total_reduction) <= minimum_cost:

                                    index = binary_search(queue, 0, len(queue) - 1, total_reduction)
                                    queue.insert(index, node_to_visit)


                        if self.bnb_access_type == AccessType.SINGLE_ACCESS and child_path:
                            node_to_visit = (chosen_start, chosen_direc, total_reduction, chosen_matrix, child_path)

                            if (total_reduction) <= minimum_cost:
                                index = binary_search(queue, 0, len(queue) - 1, total_reduction)
                                queue.insert(index, node_to_visit)

        # Algorithm Timed out, return
        except TimeoutError as exc:
            # Algorithm timed out, return input order list
            self.log(exc)
            signal.alarm(0)

            if final_path:
                return minimum_cost, final_path
            else:
                return None, order

        return minimum_cost, final_path

    def localized_min_path(self, graph, order):
        """
        find the optimal path with multiple access points

        Args:
            order: an organized list of product ID

            graph: the distance graph using All-Pair-Shortest-Path

        Returns:
            path: a list of the locations
        """

        # Setup timeout signal
        signal.signal(signal.SIGALRM, timeout_handler) # seconds
        signal.alarm(ceil(self.maximum_routing_time))

        try:
            path = []
            total_cost = 0

            sorted_order = []

            for product_id in order:

                if product_id == 'Start':
                    continue

                if product_id == 'End':
                    break

                node_minimum_cost = float('inf')

                # calculate the node min cost in different directions
                for direction, values in graph[('Start', product_id, None)].items():
                    cost = values["cost"]
                    if cost is None:
                        break
                    if cost < node_minimum_cost:
                        node_minimum_cost = cost

                # sort the node minimum cost with bubble sort
                n = len(sorted_order)
                if n == 0:
                    sorted_order.append(product_id)
                else:
                    index = -1
                    for i in range(n):
                        compared_node = sorted_order[i]
                        compared_minimum_cost = float('inf')
                        # get the compared node minimum cost
                        for direction, values in graph[('Start', compared_node, None)].items():
                            cost = values["cost"]
                            if cost is None:
                                break
                            if cost < compared_minimum_cost:
                                compared_minimum_cost = cost
                        # if current node cost is less, insert
                        if node_minimum_cost < compared_minimum_cost:
                            index = i
                            break
                    sorted_order.insert(index, product_id)

            sorted_order.insert(0, 'Start')
            sorted_order.append('End')


            pre_node = None
            access_direction = None

            for product_id in sorted_order:
                # start position
                if product_id == 'Start':
                    pre_node = product_id
                    access_direction = None
                    path += [('Start', None)]
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
                        shortest_path = [(product_id, access_point)]

                if min_cost != float('inf'):
                    total_cost += min_cost
                path += shortest_path
                pre_node = product_id

            self.log(f"Minimum Path: {path}", print_type=PrintType.MINOR)

        # Algorithm Timed out, return
        except TimeoutError as exc:
            # Algorithm timed out, return input order list
            self.log(exc)
            signal.alarm(0)

            if path:
                return total_cost, path
            else:
                return None, order

        return total_cost, path

    def get_locations_for_path(self, graph, path):
        locations = []
        for left in range(len(path) - 1):
            left_item = path[left]
            right_item = path[left + 1]
            # Access points available
            if len(left_item) > 1:
                left_node, left_dir = left_item
                right_node, right_dir = right_item
                self.log(f"Getting Location for {left_node, left_dir} -> {right_node, right_dir}", print_type=PrintType.MINOR)
                locations += graph[(left_node, right_node, left_dir)][right_dir]["path"]

        return locations

    def rotate_path(self, path):
        start_node = ('Start', None)
        result = []
        try:
            start_index = path.index(start_node)

            # Path already begins at start node
            if start_index == 0:
                return path

            # Rotate Path
            for i in range(len(path)):
                result.append(path[(start_index + i) % len(path)])
            return result

        # Start node is not included in input path
        except ValueError:
            return path

    def run_tsp_algorithm(self, graph, order, algorithm=None, rerun=False):
        # If not specified, use length of order to determine algorithm to run
        if algorithm is None:
            if len(order) <= 5:
                algo_func = self.branch_and_bound
                self.tsp_algorithm = AlgoMethod.BRANCH_AND_BOUND
            else:
                algo_func = self.nearest_neighbor
                self.tsp_algorithm = AlgoMethod.REPETITIVE_NEAREST_NEIGHBOR

        # Choose algorithm to run
        if algorithm == AlgoMethod.BRANCH_AND_BOUND:
            algo_func = self.branch_and_bound

        elif algorithm == AlgoMethod.LOCALIZED_MIN_PATH:
            algo_func = self.localized_min_path

        elif algorithm == AlgoMethod.REPETITIVE_NEAREST_NEIGHBOR:
            algo_func = self.nearest_neighbor

        # Start Time for timing algorithm run time
        start_time = time.time()

        # Run Algorithm
        if not rerun:
            self.log("Getting path to your order...")
        cost, algo_path = algo_func(graph, order)
        rotated_path = self.rotate_path(algo_path)

        # Returned the default path, so choose an access point
        if rotated_path == order:
            rotated_path = []
            for node in order:
                if node == "Start" or node == "End":
                    rotated_path.append((node, None))
                else:
                    rotated_path.append((node, 'N'))

        path = self.get_locations_for_path(graph, rotated_path)

        # End Time for timing algorithm run time
        end_time = time.time()
        total_time = end_time - start_time
        self.log(f"Total Time: {(end_time - start_time):.4f}", print_type=PrintType.MINOR)

        if ceil(total_time) > self.maximum_routing_time:
            total_time = self.maximum_routing_time

        # Stop timeout signal
        signal.alarm(0)

        return cost, rotated_path, path, total_time

    def nearest_neighbor(self, graph, order):
        """
        Implements the Nearest Neightbor Heuristic for TSP.
        """
        final_path = None
        final_cost = INFINITY

        # Setup timeout signal
        signal.signal(signal.SIGALRM, timeout_handler) # seconds
        signal.alarm(ceil(self.maximum_routing_time))

        try:
            # create a path for every single starting node
            for key in graph.keys():
                first_time_thru = True
                queue = []
                item_list = order.copy()
                first_node = (key[0], key[2])
                queue.append(first_node)
                total_cost = 0;

                while item_list:
                    popped_node = queue[-1:]

                    # first time through, set the starting node as unvisited, used for cycling
                    if (first_time_thru):
                        first_time_thru = False
                        queue.pop()
                    min_cost = INFINITY
                    visited_min_cost = INFINITY
                    next_node = None
                    visited_next_node = None

                    for (curr_node, dest_node, curr_dir), values in graph.items():

                        # there exists an unvisited node, prioritize it
                        if ( popped_node[0][0] == curr_node and popped_node[0][1] == curr_dir and (dest_node in item_list) ):
                            for direc in values:
                                if (values[direc]['cost'] is None):
                                    continue
                                elif (min_cost > values[direc]['cost']):
                                    min_cost = values[direc]['cost']
                                    next_node = (dest_node, direc)

                        # all nodes are visited, choose the least cost of the visited nodes
                        elif ( popped_node[0][0] == curr_node and popped_node[0][1] == curr_dir ):
                            for direc in values:
                                if (values[direc]['cost'] is None):
                                    continue
                                elif (visited_min_cost > values[direc]['cost']):
                                    visited_min_cost = values[direc]['cost']
                                    visited_next_node = (dest_node, direc)

                    # is there exists a path to a unvisited node, prioritize by adding it
                    # else, add the least cost path to a visited node
                    if (next_node is not None):
                        total_cost += min_cost
                        queue.append(next_node)
                        if next_node[0] in item_list:
                            item_list.remove(next_node[0])
                    else:
                        total_cost += visited_min_cost
                        queue.append(visited_next_node)

                # adds the cost of the the last edge
                last_node = queue[-1]
                beginning_node = queue[0]
                if beginning_node[0] != "Start":
                    total_cost += graph[ ( last_node[0], beginning_node[0], last_node[1] ) ][ beginning_node[1] ][ 'cost' ]

                elif beginning_node[0] == "Start" and last_node[0] != "End":
                    total_cost += graph[ ( last_node[0], "End", last_node[1])][ beginning_node[1] ][ 'cost' ]

                else:
                    # Invalid path
                    total_cost = INFINITY

                # a path completed, save it as a path based on least cost
                if (final_cost > total_cost):
                    final_path = queue.copy()
                    final_cost = total_cost

        # Algorithm Timed out, return
        except TimeoutError as exc:
            # Algorithm timed out, return input order list
            self.log(exc)
            signal.alarm(0)

            if path:
                return final_cost, final_path
            else:
                return None, order

        # least cost path found, return
        return final_cost, final_path

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

    def get_descriptive_steps(self, positions, targets, products=[], collapse=True):
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

        if products:
            _products = deepcopy(products)
            if "Start" in _products:
                _products.remove("Start")
            if "End" in _products:
                _products.remove("End")

        _positions = deepcopy(positions)

        if collapse:
            updated_positions = self.collapse_directions(_positions)
        # Manually remove duplicates
        else:
            prev_position = None
            updated_positions = []
            for position in _positions:
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
                    if products:
                        for product in _products:
                            if self.product_info[product] == target:
                                path.append(f"Pickup item {product} at {self.product_info[product]}.")
                    else:
                        path.append(f"Pickup item at {target}.")
                    break

        back_to_start, steps = self.move_to_target(current_position, end)
        total_steps += steps
        path.append(back_to_start)
        path.append("Pickup completed.")
        path.append(f"Total Steps: {total_steps}")

        self.log(f"Total Steps: {total_steps}", print_type=PrintType.MINOR)

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

    def verify_settings_range(self, value, minimum, maximum, expected_type=int):
        """
        Helper function to validate the value is within the specified range.

        Args:
            value   (int, float): Value to validate
            minimum (int, float): Smallest value allowed
            maximum (int, float): Largest value allowed

        Returns:
            True if value falls within minimum and maximum value.
            False otherwise.
        """
        def cast_data_type(value, expected_type):
            success = False

            try:
                result = expected_type(value)
                success = True
            except TypeError:
                self.log(f"Invalid value {value}, could not cast to '{expected_type}'!", print_type= PrintType.DEBUG)
                return False, value

            return success, result

        input_success, casted_value = cast_data_type(value, expected_type)

        # Failed to cast the value
        if not input_success:
            return False

        try:
            if minimum <= casted_value <= maximum:
                return True
            elif casted_value < minimum:
                self.log(f"Try again! {casted_value} is too small, must be minimum {minimum}.")
            elif casted_value > maximum:
                self.log(f"Try again! {casted_value} is too large, must be maximum {maximum}.")
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

        try:
            x = input(f"Set Map X Size (Currently {self.map_x}, Minimum {minimum_x}, Max {maximum_x}): ")
            y = input(f"Set Map Y Size (Currently {self.map_y}, Minimum {minimum_y}, Max {maximum_y}): ")

            x_success = self.verify_settings_range(x, minimum_x, maximum_x)
            y_success = self.verify_settings_range(y, minimum_y, maximum_y)

            if x_success and y_success:
                self.map_x = int(x)
                self.map_y = int(y)
                success = True

        except ValueError:
            self.log("Invalid map size values, please try again.")

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

                try:
                    x_success = self.verify_settings_range(x, 0, self.map_x - 1)
                    y_success = self.verify_settings_range(y, 0, self.map_y - 1)

                    if x_success and y_success:

                        # Overlapping Item and Worker Positions
                        if (int(x), int(y)) in self.items:
                            self.log("Worker position is the same as a item position! Please Try Again.\n")

                        else:
                            self.starting_position = (int(x), int(y))
                            success = True

                    else:
                        self.log("") # Newline for readability

                except ValueError:
                    self.log("Invalid worker positions, please try again!\n")

                self.log(f"\nCurrent Worker Starting Position: {self.starting_position}")
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
                try:
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
                except ValueError:
                    self.log("Invalid worker positions, please try again!\n")

                self.log(f"\nCurrent Worker Ending Position: {self.ending_position}")
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

            item_success = False

            try:
                number_of_items = input(f"Set number of items (Up to {self.maximum_items}): ")

                item_success = self.verify_settings_range(number_of_items, self.minimum_items, self.maximum_items)

            except ValueError:
                self.log(f"Invalid value '{number_of_items}'!")

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
            try:
                user_max = input(f"Set Maximum Items (Currently {self.maximum_items}, Maximum {max_items}): ")

                max_success = self.verify_settings_range(user_max, self.minimum_items, max_items)

                self.log(f"Item Max Success: {max_success}", print_type=PrintType.DEBUG)

                if max_success:
                    self.maximum_items = int(user_max)
                    success = True

                else:
                    self.log("Invalid values, please try again!")

            except ValueError:
                self.log(f"Invalid value {user_max}, please try again!")

        self.log(f"Maximum Items: {self.maximum_items}")

        return success

    def set_maximum_routing_time(self):

        banner = Menu("Set Maximum Routing Time")
        banner.display()

        success = False

        while not success:
            try:
                routing_time = input(f"Set Maximum Routing Time in Seconds (Currently {self.maximum_routing_time:.2f}): ")

                max_success = self.verify_settings_range(routing_time, 0, 1440, float)
                if max_success:
                    success = True
                    if float(routing_time) == 0:
                        routing_time = 1

                    self.maximum_routing_time = ceil(float(routing_time))
                else:
                    self.log("Invalid value, please try again!")

            except ValueError:
                self.log(f"Invalid value {routing_time}, please try again!")

        self.log(f"Maximum Routing Time in Seconds: {self.maximum_routing_time:.2f}")

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

                    success, reason = self.load_product_file(product_file.rstrip())

                    if success:
                        self.item_mode = GenerateMode.LOADED_FILE
                        self.items = self.get_item_positions()
                        self.map, self.inserted_order = self.generate_map()

                    elif reason == FileNotFoundError:
                        self.log(f"File '{product_file}' was not found, please try entering full path to file!\n")
                    elif reason == ValueError:
                        self.log(f"File '{product_file}' is the incorrect format, please try changing the format or try a new file!\n")
                    else:
                        self.log(f"Something went wrong with '{product_file}', please try again!\n")

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

                    if self.order:
                        order = []
                        for product in self.order:
                            if product == "Start" or product == "End":
                                continue
                            else:
                                order.append(str(product))

                        self.log(f"Current Order is: {', '.join(order)}")
                else:
                    update = True
                    clear = True

                # Handle menu options
                suboption = input("> ")

                # Create Order
                if suboption == '1':
                    clear = True
                    order_success = True

                    while True:
                        if update:
                            self.display_menu(MenuType.CREATE_ORDER, clear=clear)
                        else:
                            update = True
                            clear = True

                        # Handle menu options
                        order_option = input("> ")

                        order = []
                        product_ids = []
                        item_positions = []

                        if self.debug:
                            self.log("Product IDs:")
                            for i, product in enumerate(self.product_info, 1):
                                self.log(f"{i}. {product}")

                        # Individual Order
                        if order_option == "1":
                            self.log("Order uses comma-separated Product IDs.\n" \
                                     "Example:\n" \
                                     "  1, 34, 50"
                                    )

                            success = False
                            while not success:
                                order = input("Enter Order ('c' to cancel): ").rstrip()

                                if "c" in order:
                                    success = True

                                    self.log(f"Cancelled Order!")
                                    if self.order:
                                        self.log(f"  Using current order:")
                                        for i, product in enumerate(self.order):
                                            self.log(f"  {i}. {product}")


                                    continue
                                    # Do Nothing

                                elif order:
                                    try:
                                        if "," in order:
                                            order_list = order.split(", ")
                                        else:
                                            order_list = [int(order)]

                                        # More items than maximum allowed
                                        if len(order_list) > self.maximum_items:
                                            self.log(f"{len(order_list)} is more than the maximum number of items allowed of {self.maximum_items}!\n")
                                            success = False
                                            clear = False

                                        # Valid list, get IDs
                                        else:
                                            for product_id in order_list:
                                                if int(product_id) in self.product_info:
                                                    product_ids.append(int(product_id))
                                                    success = True

                                                else:
                                                    success = False
                                                    clear = False
                                                    product_ids = []
                                                    self.log(f"Product '{product_id}' is not within inventory. Not including in path.")

                                    except ValueError:
                                        self.log(f"Invalid order '{order}'! Please use the specified order format.")


                        # Multiple Orders from File
                        elif order_option == "2":
                            if self.order_file is None:
                                # Set Order File Name
                                success = False
                                while not success:
                                    order_file = input("Enter order filename: ")

                                    success, reason = self.load_order_file(order_file)

                                    if success:
                                        self.log(f"Successfully loaded orders from file '{order_file}'!")
                                        self.order_number = 0
                                        product_ids = self.order_info[self.order_number]
                                        self.log(f"Loaded Order #{self.order_number}!")

                                    elif reason == FileNotFoundError:
                                        self.log(f"File '{order_file}' was not found, please try entering full path to file!\n")
                                    elif reason == ValueError:
                                        self.log(f"File '{order_file}' is the incorrect format, please try changing the format or try a new file!\n")
                                    else:
                                        self.log(f"Something went wrong with '{order_file}', please try again!\n")

                            self.display_menu(MenuType.MULTIPLE_ORDERS, clear=clear)

                            ordering = True
                            while ordering:
                                mult_option = input("> ")

                                ordering = False

                                if mult_option == "1":
                                    # Set Order File Name
                                    success = False
                                    while not success:
                                        order_file = input("Enter order filename: ")

                                        success, reason = self.load_order_file(order_file)

                                        if success:
                                            self.log(f"Successfully loaded orders from file '{order_file}'!")
                                            self.order_number = 0
                                            product_ids = self.order_info[self.order_number]
                                            self.log(f"Loaded Order #{self.order_number}!")

                                        elif reason == FileNotFoundError:
                                            self.log(f"File '{order_file}' was not found, please try entering full path to file!\n")
                                        elif reason == ValueError:
                                            self.log(f"File '{order_file}' is the incorrect format, please try changing the format or try a new file!\n")
                                        else:
                                            self.log(f"Something went wrong with '{order_file}', please try again!\n")

                                elif mult_option == "2":
                                    self.log(f"Current Order is #{self.order_number}, continuing to next order.")
                                    if len(self.order_info) > 0 and self.order_number < len(self.order_info):
                                        self.order_number  = (self.order_number + 1) % len(self.order_info)
                                        product_ids = self.order_info[self.order_number]
                                        self.log(f"Using Order #{self.order_number}!")

                                elif mult_option == "3":
                                    success = False
                                    while not success:
                                        order_number = input(f"Enter order number (0 - {len(self.order_info) - 1}): ")

                                        try:
                                            order_number = int(order_number)
                                            if len(self.order_info) > 0 and order_number < len(self.order_info):
                                                product_ids = self.order_info[order_number]
                                                self.order_number  = order_number
                                                success = True
                                            else:
                                                self.log(f"Invalid order number '{order_number}'. Please try entering a number under {len(self.order_info)}.")

                                        except ValueError:
                                            self.log(f"Invalid order number '{order_number}'. Please try entering a number under {len(self.order_info)}.")

                                elif mult_option == "4":
                                    continue

                                else:
                                    self.log(f"Invalid option '{mult_option}'! Please try again.\n")
                                    ordering = True

                        # Back
                        elif order_option == "3":
                            clear = True
                            break

                        else:
                            self.log(f"Invalid option '{order_option}'. Please try again.\n")
                            order_success = False
                            clear = False

                        if product_ids:
                            items = "items" if len(product_ids) > 1 else "item"
                            self.log(f"\n",
                                     f"You completed your order of {len(product_ids)} {items}!\n",
                                     f"You ordered:")

                            for i, product in enumerate(product_ids, 1):
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

                            self.order = self.process_order(product_ids)
                            self.graph = self.build_graph_for_order(self.order)

                        # Go back to View Map Menu
                        clear = False

                        if order_success:
                            break

                # Get Path for Order
                elif suboption == '2':
                    if self.order:
                        if self.graph is None:
                            self.graph = self.build_graph_for_order(self.order)

                        cost, id_path, path, run_time = self.run_tsp_algorithm(self.graph, self.order)

                        # Algo Timed Out
                        if run_time == self.maximum_routing_time:
                            cost, id_path, path, run_time = self.run_tsp_algorithm(self.graph, self.order, AlgoMethod.REPETITIVE_NEAREST_NEIGHBOR, rerun=True)


                        target_locations = []
                        for product in self.order:
                            if product == 'Start' or product == 'End':
                                continue

                            location = self.product_info.get(product)
                            if location:
                                target_locations.append(location)

                        steps = self.get_descriptive_steps(path, target_locations, products=self.order, collapse=False)

                        if steps:
                            self.display_path_in_map(steps)

                            self.log("Directions:")
                            self.log("-----------")
                            for step, action in enumerate(steps, 1):
                                if "Total Steps" in action:
                                    self.log(action)
                                else:
                                    self.log(f"{step}. {action}")

                        else:
                            self.log(f"Path to {product_id} was not found!")

                    else:
                        self.log("No existing order! Please create an order first!")
                        clear = False

                # Get Path to Product
                elif suboption == '3':
                    self.log("Get Path to Product")

                    # Request Product ID to find path for
                    complete = False
                    success = True
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
                            self.log(f"Invalid Product ID '{product_id}', please try again!\n")

                        except KeyError:
                            self.log("Product was not found!\n")
                            success = False
                            complete = True

                    if success:
                        steps = self.get_items(self.gathering_algo, item_position)

                        if steps:
                            self.display_path_in_map(steps)

                            self.log("Directions:")
                            self.log("-----------")
                            for step, action in enumerate(steps, 1):
                                    if "Total Steps" in action:
                                        self.log(action)
                                    else:
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
                            self.log(f"Invalid Product ID '{product_id}', please try again!\n")

                        except KeyError:
                            self.log("Product was not found!\n")
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

                        success, reason = self.load_product_file(product_file)

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

                        elif reason == FileNotFoundError:
                            self.log(f"File '{product_file}' was not found, please try entering full path to file!\n")
                        elif reason == ValueError:
                            self.log(f"File '{product_file}' is the incorrect format, please try changing the format or try a new file!\n")
                        else:
                            self.log(f"Something went wrong with '{product_file}', please try again!\n")

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

                    clear = False

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

                    clear = False


                # Set Maximum Items Ordered Amount
                elif suboption == '4':
                    self.set_maximum_items_ordered()
                    self.items = self.get_item_positions()

                    clear = False

                elif suboption == '5':
                    self.set_maximum_routing_time()

                    clear = False

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

                                    # Repetitive Nearest Neighbor
                                    elif algo_option == '3':
                                        self.tsp_algorithm = AlgoMethod.REPETITIVE_NEAREST_NEIGHBOR
                                        break

                                    # Back
                                    elif algo_option == '4':
                                        break

                                    else:
                                        self.log("Invalid choice. Try again.")
                                        update = False
                                        clear = False

                            # Set TSP Access Type
                            elif adv_option == '6':
                                while True:
                                    if update:
                                        self.display_menu(MenuType.TSP_ACCESS_TYPE, clear=clear)
                                    else:
                                        update = True
                                        clear = True

                                    algo_option = input("> ")

                                    # Branch and Bound
                                    if algo_option == '1':
                                        self.bnb_access_type = AccessType.SINGLE_ACCESS
                                        break

                                    # Custom Algorithm
                                    elif algo_option == '2':
                                        self.bnb_access_type = AccessType.MULTI_ACCESS
                                        break

                                    # Back
                                    elif algo_option == '3':
                                        break

                                    else:
                                        self.log("Invalid choice. Try again.")
                                        update = False
                                        clear = False

                            # Load Test Case File
                            elif adv_option == '7':
                                if update:
                                    self.display_menu(MenuType.LOAD_TEST_CASE_FILE, clear=clear)
                                else:
                                    update = True
                                    clear = True

                                # Set Product File Name
                                success = False
                                while not success:
                                    test_case_file = input("Enter test case filename: ")

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
                            elif adv_option == '8':
                                if self.test_case_file and self.test_product_file:
                                    success, reason = self.load_product_file(self.test_product_file)

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

                                            # Test Algorithms to Get Paths
                                            self.log(f"Test Case: Size {size}\n"    \
                                                      "----------------------")
                                            grouped_items = self.process_order(product_ids)
                                            graph = self.build_graph_for_order(grouped_items)


                                            # Run Test Case against desired algorithms
                                            algorithms_to_test = [
                                                # AlgoMethod.LOCALIZED_MIN_PATH,
                                                AlgoMethod.REPETITIVE_NEAREST_NEIGHBOR,
                                                AlgoMethod.BRANCH_AND_BOUND
                                            ]

                                            for algo in algorithms_to_test:

                                                algo_str = f"Running {algo}....."
                                                if algo == AlgoMethod.BRANCH_AND_BOUND:
                                                    algo_str = f"Running {self.bnb_access_type} {algo}....."

                                                # Run Algorithm
                                                self.log("-------------------" + ('-' * len(algo_str)))
                                                self.log(algo_str)
                                                self.log("-------------------" + ('-' * len(algo_str)))
                                                cost, id_path, path, run_time = self.run_tsp_algorithm(graph, grouped_items, algo)

                                                # Algorithm Timed Out
                                                if run_time == self.maximum_routing_time:
                                                    failed += 1
                                                    cases_failed[size][str(algo)] = f"Timeout: {path}"
                                                    self.log(f"Failed {algo}!")

                                                else:
                                                    # Test Case Finished
                                                    test_map = deepcopy(self.map)

                                                    target_locations = []
                                                    for product in grouped_items:
                                                        if product == 'Start' or product == 'End':
                                                            continue

                                                        location = self.product_info.get(product)
                                                        if location:
                                                            target_locations.append(location)

                                                    steps = self.get_descriptive_steps(path, target_locations, products=grouped_items, collapse=False)

                                                    if steps:
                                                        self.display_path_in_map(steps, map_layout=test_map, map_only=True)

                                                        self.log("Directions:")
                                                        self.log("-----------")
                                                        for step, action in enumerate(steps, 1):
                                                            if "Total Steps" in action:
                                                                self.log(action)
                                                            else:
                                                                self.log(f"{step}. {action}")

                                                    passed += 1

                                                    self.log("-------------------" + ('-' * len(str(algo))))
                                                    self.log(f"Completed {algo}!")
                                                    self.log("-------------------" + ('-' * len(str(algo))))

                                                self.log(f"    Time: {run_time:.6f}")
                                                self.log(f"    Cost: {cost}")
                                                self.log(f"     IDs: {id_path}")
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
                                                        self.log(f"    {case}:")
                                                        self.log(f"        {reason}")

                                else:
                                    self.log("No test cases to run! Must load test case file first!")

                                update = True
                                clear = False

                            # Back
                            elif adv_option == '9':
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
