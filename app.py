"""
Welcome to Item Routing System!

Authors: Joseph Abero, ChatGPT

ItemRoutingSystem is a text-based application used to provide store workers with
directions to gather shopping items around a warehouse.
"""

from constants import *
from menu import Menu
from queue import PriorityQueue

import heapq
import itertools
import os
import random
import sys
import time

class ItemRoutingSystem:
    """
    Main application for providing directions for a single worker to gather items.

    Handles user inputs, generation of the map, and settings.
    """
    WORKER_SYMBOL = 'S'
    ITEM_SYMBOL = chr(9641) # ▩

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

        # Default worker settings
        self.worker_mode = GenerateMode.MANUAL
        self.starting_position = (0, 0)

        # Default item settings
        self.item_mode = GenerateMode.RANDOM
        self.minimum_items = 0
        self.maximum_items = 8
        self.maximum_routing_time = 60
        self.items = self.get_item_positions()

        # Default algorithm
        self.gathering_algo = AlgoMethod.DIJKSTRA

        # Generate initial map from default settings
        self.map, self.inserted_order = self.generate_map()

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
                self.product_info[ int( fields[0] ) ] = int(float( fields[1] )) , int(float( fields[2] ))
            f.close()
        except FileNotFoundError:
            success = False

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
            menu.add_option(1, "Get Path to Product")
            menu.add_option(2, "Get Location of Product")

            # Only expose advanced setting option in debug mode
            if self.debug:
                menu.add_option(3, "Generate New Map")
                menu.add_option(4, "Back")
            else:
                menu.add_option(3, "Back")

        elif menu_type == MenuType.SETTINGS:
            menu = Menu("Settings Menu")
            menu.add_option(1, "Load Product File")
            menu.add_option(2, "Set Worker Starting Position Mode")
            menu.add_option(3, "Set Maximum Items Ordered")
            menu.add_option(4, "Set Routine Time Maximum")
            menu.add_option(5, "Toggle Debug Mode")

            if self.debug:
                menu.add_option(6, "Advanced Settings")
                menu.add_option(7, "Back")

            else:
                menu.add_option(6, "Back")

            info = "Current Settings:\n"                                   \
            f"  Loaded Product File: {self.product_file}\n"                \
            f"  Worker Settings:\n"                                        \
            f"    Position: {self.starting_position}\n"                    \
            f"  Maximum Routing Time: {self.maximum_routing_time}\n"       \
            f"  Debug Mode: {self.debug}\n"

            menu.set_misc_info(info)

        elif menu_type == MenuType.ADVANCED_SETTINGS:
            menu = Menu("Advanced Settings Menu")
            menu.add_option(1, "Set Map Size")
            menu.add_option(2, "Set Item Position Mode")
            menu.add_option(3, "Set Map Orientation")
            menu.add_option(4, "Set Algorithm")
            menu.add_option(5, "Back")

            position_str = ' '.join(str(p) for p in self.items)
            if len(self.items) > 10:
                file = "positions.txt"

                # Write positions to file if too many to print to screen
                with open(file, "w+") as f:
                    for position in self.items:
                        x, y = position
                        f.write(f"({x}, {y})\n")

                position_str = f"See '{file}' for list of item positions."

            info = "Current Advanced Settings:\n"                          \
            f"Map Size: {self.map_x}x{self.map_y}\n"                       \
            f"\n"                                                          \
            f"Worker Settings:\n"                                          \
            f"  Mode: {self.worker_mode}\n"                                \
            f"  Gathering Algorithm: {self.gathering_algo}\n"              \
            f"Item Settings:\n"                                            \
            f"  Mode: {self.item_mode}\n"                                  \
            f"  Number of Items: {len(self.items)}\n"                      \
            f"  Positions: {position_str}\n"                               \
            f"Debug Mode: {self.debug}\n"

            menu.set_misc_info(info)

        elif menu_type == MenuType.LOAD_PRODUCT_FILE:
            menu = Menu("Load Product File Menu")

        elif menu_type == MenuType.ALGO_METHOD:
            menu = Menu("Set Gathering Algorithm")
            menu.add_option(1, "Use Order of Insertion")
            menu.add_option(2, "Brute Force")
            menu.add_option(3, "Dijkstra")
            menu.add_option(4, "Back")

        elif menu_type == MenuType.WORKER_POSITION:
            menu = Menu("Set Starting Worker Position Mode")

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
        grid[self.starting_position[0]][self.starting_position[1]] = ItemRoutingSystem.WORKER_SYMBOL

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
        self.log(f"{ItemRoutingSystem.WORKER_SYMBOL}: Worker Starting Spot".center(banner_length))
        self.log(f"{ItemRoutingSystem.ITEM_SYMBOL}: Item".center(banner_length))
        self.log("Positions are labeled as (X, Y)".center(banner_length))
        self.log("X is the horizontal axis, Y is the vertical axis".center(banner_length))
        self.log("")

        settings_info = "Current Settings:\n"                                \
            f"  Worker Position: {self.starting_position}\n"                 \
            f"  Ordered Item Maximum: {self.maximum_items}\n"                \
            f"  Gathering Algorithm: {self.gathering_algo}\n"                \
            f"  Maximum Time To Process: {self.maximum_routing_time}\n"      \
            f"  Debug Mode: {self.debug}\n"

        self.log(settings_info)

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

    def dijkstra(self, grid, target):
        """
        Performs dijkstra’s algorithm to gather shortest path to a desired position within the given grid.

        Args:
            grid(list of lists): Positions of items within the grid.

            target (tuples): Position of item to search for.

        Returns:
            path (list of tuples): List of item positions to traverse in order.
        """
        def is_valid_position(x, y):
            return 0 <= x < self.map_x  and \
                   0 <= y < self.map_y

        start = None

        x, y = target
        if not is_valid_position(x, y):
            self.log(f"Invalid target position: {target}", print_type=PrintType.DEBUG)
            return []
        
        # Find the starting position
        for i in range(self.map_x):
            for j in range(self.map_y):
                if grid[j][i] == ItemRoutingSystem.WORKER_SYMBOL:
                    start = (i, j)
                    break
            if start: break
        
        if not start:
            raise ValueError("Starting position ItemRoutingSystem.WORKER_SYMBOL not found in grid.")
        
        # Initialize the distance to all positions to infinity and to the starting position to 0
        dist = {(i, j): float('inf') for i in range(self.map_x) for j in range(self.map_y)}
        dist[start] = 0
        
        # Initialize the priority queue with the starting position
        pq = [(0, start)]
        
        # Initialize the previous position dictionary
        prev = {}
        
        while pq:
            # Get the position with the smallest distance from the priority queue
            (cost, position) = heapq.heappop(pq)
            
            # If we've found the target, we're done
            if position == target:
                self.log(f"Found path to target {target}!", print_type=PrintType.DEBUG)
                break
            
            # Check the neighbors of the current position
            for (dx, dy) in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                x, y = position[0] + dx, position[1] + dy

                self.log(position, (x, y), print_type=PrintType.DEBUG)

                if not is_valid_position(x, y):
                    self.log(f"Skipping {(x, y)}: Invalid Position", print_type=PrintType.DEBUG)
                    continue

                if grid[x][y] == ItemRoutingSystem.ITEM_SYMBOL:
                    self.log(f"Skipping {(x, y)}: Item", print_type=PrintType.DEBUG)
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
            self.log(f"Path found: {path}", print_type=PrintType.DEBUG)
            return path
        else:
            self.log("Path not found", print_type=PrintType.DEBUG)
            return []

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
            targets.append(self.starting_position)

        if self.debug:
            end_time = time.time()
            self.log(f"Total Time: {(end_time - start_time):.4f}")

        return targets


    def get_descriptive_steps(self, positions, target):
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
        path = []
        start = positions.pop(0)
        end = positions.pop()
        prev_target = []
        direc = None
        updated_positions = []

        path.append(f"Start at position {start}!")
        current_position = start
        total_steps = 0

        # Preprocessing
        for position in positions:
            # initial direction setup
            if ( direc == None ):
                if ( start[1] == position[1] ):
                    direc = "LR"
                else:
                    direc = "DU"
                prev_position = position
                continue

            # if moving in same direction, ignore and continue
            if ( prev_position[0] == position[0] and direc == "DU"):
                prev_position = position
                continue
            elif ( prev_position[1] == position[1] and direc == "LR"):
                prev_position = position
                continue
            # change of direction means you add the position int othe list
            else:
                updated_positions.append(prev_position)
                if (direc == "DU"):
                    direc = "LR"
                else:
                    direc = "DU"
            prev_position = position
        # dds the last position
        updated_positions.append(positions[-1])

        for position in updated_positions:
            prev_position = current_position
            move, steps = self.move_to_target(current_position, position)
            current_position = position
            total_steps += steps
            path.append(move)
        back_to_start, steps = self.move_to_target(current_position, end)
        total_steps += steps
        path.append(f"Pickup item at {target}.")
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
            targets = [self.starting_position, target, self.starting_position]
            result = self.get_descriptive_steps(targets, target)
            return result

        elif option == AlgoMethod.BRUTE_FORCE:
            # targets = self.get_targets()
            targets = [self.starting_position, target, self.starting_position]
            path = self.gather_brute_force(targets)
            result = self.get_descriptive_steps(path, target)
            return result

        elif option == AlgoMethod.DIJKSTRA:
            shortest_path = []

            # Maximum Routing Time Setup
            timeout = False
            t_temp = 0.0
            t_thresh = self.maximum_routing_time * 60 # minute to second conversion
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

                path = self.dijkstra(self.map, (x, y))

                if path:
                    if len(path) < len(shortest_path) or not shortest_path:
                        shortest_path = path

                self.log(f"Shortest Path for {(x, y)}: {shortest_path}", print_type=PrintType.DEBUG)

            result = []
            if shortest_path:
                self.log(f"Path to product is: {shortest_path}", print_type=PrintType.DEBUG)
                path = shortest_path + [self.starting_position]
                result = self.get_descriptive_steps(path, target)
            elif timeout:
                path = [ self.starting_position, target, self.starting_position ]
                result = self.get_descriptive_steps(path, target)
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
            self.map_x  = int(x)
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
                x = input(f"Set starting X position (Currently {self.starting_position[0]}, Maximum {self.map_x - 1}): ")
                y = input(f"Set starting Y position (Currently {self.starting_position[1]}, Maximum {self.map_y - 1}): ")

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
                        self.log("Item position is the same as the worker position! Please Try Again.\n", print_type=PrintType.DEBUG)

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
                            self.log("Item position is the same as the worker position! Please Try Again.\n")

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

        minutes = input(f"Set Maximum Routing Time in Minutes (Currently {self.maximum_routing_time}): ")

        max_success = self.verify_settings_range(minutes, 0, 1440)
        if (max_success):
            success = True
            self.maximum_routing_time = int(minutes)
        else:
            self.log("Invalid value, please try again!")

        self.log(f"Maximum Routing Time in Minutes: {self.maximum_routing_time}")

        return success



# justin
    def matrix_reduction(self, matrix, source=None, dest=None):
        """
        Performs the matrix reduction for branch-and-bound
        Returns a reduced matrix
        """
        temp_matrix = matrix.copy()
        reduction_cost = 0

        # when taking a path, set the corresponding row nad column to inf
        if source:
            reduction_cost += temp_matrix[ (source[0], source[1], source[2]) ][dest].get('cost')

            for k,v in temp_matrix.items():
                if (source[0] == k[0]):
                    for direc in v:
                        v[direc]['cost'] = INFINITY
                if (source[1] == k[1]):
                    for direc in v:
                        v[direc]['cost'] = INFINITY


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
            reduction_cost += row_cost
        
        # Finds the minimum value to make the column have a zero
        for key in temp_matrix.keys():
            col_cost = INFINITY
            
            for k,v in temp_matrix.items():
                if (key[0] == k[1]):
                    for direc in v:
                        direc_cost = INFINITY if (v.get(direc).get('cost') is None) else v.get(direc).get('cost')
                        col_cost = min(col_cost, direc_cost)
            if (col_cost == INFINITY):
                col_cost = 0;
            # reduces the values in the matrix
            for k,v in temp_matrix.items():
                if (key[0] == k[1]):
                    for direc in v:
                        if (v.get(direc).get('cost') is None or v.get(direc).get('cost') == INFINITY):
                            v[direc]['cost'] = INFINITY
                        else:
                            v[direc]['cost'] = (v.get(direc).get('cost') - col_cost)
            reduction_cost += col_cost
       
        return reduction_cost, temp_matrix
    

    def branch_and_bound(self, graph, order):
        """
        Applies the branch and bound algorithm to generate a path
        """
        pq = PriorityQueue()
        path = []
        
        # 1. Create Matrix

        # 2. Reduction
        reduced_cost, parent_matrix = matrix_reduction(graph)
        child_matrix = parent_matrix.copy()

        # 3. Choose Random Start
        starting_node = random.choice( list(graph) )

        # 4. Set Upper Bound
        upper_bound = order

        # 5. Traversal 
        # (source, source_direction, level, cost, matrix, path)
        # path_entry = (starting_node[0], starting_node[2])
        pq.put( (starting_node[0], starting_node[2], 0, reduced_cost, child_matrix, path) )

        while( not pq.empty() ):
            
            source, source_direction, level, cost, matrix, path = pq.get()
            
            # If all items have been picked up
            if ( level == len(order) ):
                return path

            for (start, dest, src_dir), values in matrix.items():
                if (source == start and source_direction == src_dir):
                    for direc in values:
                        if ( (values.get(direc).get('cost') is None) or ( values.get(direc).get('cost') is INFINITY) ):
                            continue
                        else:
                            reduction, temp_matrix = matrix_reduction( matrix, (start, dest, src_dir), direc )
                            pq.put( (start, direc, level + 1, cost + reduction, temp_matrix, path.append(values.get(direc).get('path'))) )
                    
            


        
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

                # Get Path to Product
                if suboption == '1':
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
                        self.log("Directions:")
                        self.log("-----------")
                        for step, action in enumerate(steps, 1):
                            self.log(f"{step}. {action}")
                    else:
                        self.log(f"Path to {product_id} was not found!")

                    clear = False

                # Get Location of Product
                elif suboption == '2':
                    self.log("Get Location of Product")

                    complete = False
                    while not complete:
                        try:
                            if self.debug:
                                self.log("Product IDs:")
                                for i, product in enumerate(self.product_info, 1):
                                    self.log(f"{i}. {product}")

                            product_id = input("Enter Product ID: ")

                            self.log(f"Product `{product_id}` is located at position {self.product_info[int(product_id)]}.")
                            complete = True

                        except ValueError:
                            self.log(f"Invalid Product ID '{product_id}', please try again!")

                        except KeyError:
                            self.log("Product was not found!")
                            complete = True

                # Back
                elif suboption == '3':
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
                elif suboption == '4' and self.debug:
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
                            self.display_menu(MenuType.WORKER_POSITION, clear=clear)
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

                # Set Maximum Items Ordered Amount
                elif suboption == '3':
                    self.set_maximum_items_ordered()
                    self.items = self.get_item_positions()

                elif suboption == '4':
                    self.set_routing_time_maximum()

                # Toggle Debug
                elif suboption == '5':
                    self.debug = not self.debug

                # Debug Mode:       Advanced Settings
                # Non-Debug Mode:   Back
                elif suboption == '6':
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

                            # Set Algorithm Method
                            elif adv_option == '4':
                                while True:
                                    if update:
                                        self.display_menu(MenuType.ALGO_METHOD, clear=clear)
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

                            # Back
                            elif adv_option == '5':
                                break

                            else:
                                self.log("Invalid choice. Try again.")
                                update = False
                                clear = False

                    # Non-Debug Mode: Back
                    else:
                        break

                # Debug Mode: Back
                elif suboption == '7' and self.debug:
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
