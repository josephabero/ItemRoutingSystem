"""
Welcome to Shopping For Carts!

Authors: Joseph Abero, ChatGPT

Shopping For Carts is a text-based shopping cart gathering application used to
provide store workers with directions to gather shopping carts around a
store parking lot.
"""

from enum import Enum
import itertools
import os
import random

class MenuType(Enum):
    """
    Constants for menu types.
    """
    MAIN_MENU = 0
    GO_GET_CARTS = 1
    SETTINGS = 2
    ALGO_METHOD = 3
    WORKER_POSITION = 4
    CART_POSITION = 5

class AlgoMethod(Enum):
    """
    Constants for algorithms used to gather carts 
    """
    ORDER_OF_INSERTION = "Order of Insertion"
    BRUTE_FORCE = "Brute Force"

    def __str__(cls):
        return cls.value

class GenerateMode(Enum):
    """
    Constants for modes of generating settings
    """
    MANUAL = "Manual"
    RANDOM = "Random"

    def __str__(cls):
        return cls.value

class Menu:
    """
    Displays menu options to screen.
    """

    def __init__(self, menu_name):
        """
        Initializes menu with a name and defaults to no options.

        Args:
            menu_name (str): name of menu
        """
        self.menu_name = menu_name
        self.options = []
        self.misc_info = None

    def print_banner(self):
        """
        Prints a menu header as a banner.

        Args:
            menu_name (str): Name to be displayed in the header

        Examples:
            >>> Menu.print_banner()
            ------------------------------------------------------------
                                        Menu
            ------------------------------------------------------------
        """
        banner = "------------------------------------------------------------"
        print(banner)
        print(f"{self.menu_name.center(len(banner))}")
        print(banner)

    def display(self, clear=True):
        """
        Prints banner with menu name and menu options to choose from.

        Args:
            clear (bool): Option to clear screen

        Examples:
            >>> Menu.display()
            ------------------------------------------------------------
                                        Menu
            ------------------------------------------------------------

            1. Option 1
            2. Option 2

        """
        if clear:
            # Windows
            if os.name == 'nt':
                os.system('cls')
         
            # Mac/Linus
            else:
                os.system('clear')

        self.print_banner()

        if self.misc_info:
            print(self.misc_info)

        if self.options:
            print("")
            for i, option in enumerate(self.options):
                print(f"{i+1}. {option}")
            print("")

    def add_option(self, index, option):
        """
        Inserts option to existing option list.
        """
        self.options.insert(index, option)

    def set_misc_info(self, info):
        """
        Sets miscellaneous information for the menu.

        Args:
            info (str): Information relevant to the menu.
        """
        if isinstance(info, str):
            self.misc_info = info


class ShoppingForCarts:
    def __init__(self):
        """
        Initializes Menu class.

        Defaults a 5x5 map with a worker starting position of (0, 0).
        """
        # Default 5x5 map size
        self.map_x = 5
        self.map_y = 5

        # Default worker settings
        self.worker_mode = GenerateMode.MANUAL
        self.starting_position = (0, 0)

        # Default cart settings
        self.cart_mode = GenerateMode.RANDOM
        self.minimum_carts = 3
        self.maximum_carts = 8
        self.carts = self.get_cart_positions()

        # Default debug mode
        self.debug = False

        # Default algorithm
        self.gathering_algo = AlgoMethod.BRUTE_FORCE

        # Generate initial map from default settings
        self.map, self.inserted_order = self.generate_map()

        # Display welcome banner
        banner = "------------------------------------------------------------"
        print(banner)
        print("")
        print("")
        print(f'{"Welcome to Shopping For Carts!".center(len(banner))}')
        print("")
        print("")
        print(banner)

    def display_menu(self, menu_type, clear=True):
        """
        Creates and displays appropriate menu.

        Args:
            menu_type (MenuType): type of menu to display

        Examples:
            >>> ShoppingForCarts.display(MenuType.MAIN_MENU)
            ------------------------------------------------------------
                                     Main Menu
            ------------------------------------------------------------

            1. Go Get Carts
            2. Settings
            3. Exit

        """
        menu = None

        if menu_type == MenuType.MAIN_MENU:
            menu = Menu("Main Menu")
            menu.add_option(1, "Go Get Carts")
            menu.add_option(2, "Settings")
            menu.add_option(3, "Exit")

        elif menu_type == MenuType.GO_GET_CARTS:
            menu = Menu("Go Get Carts Menu")
            menu.add_option(1, "Generate New Map")
            menu.add_option(2, "Back")

        elif menu_type == MenuType.SETTINGS:
            menu = Menu("Settings Menu")
            menu.add_option(1, "Set Map Size")
            menu.add_option(2, "Set Worker Starting Position Mode")
            menu.add_option(3, "Set Cart Position Mode")
            menu.add_option(4, "Set Cart Minimum and Maximum Amount")
            menu.add_option(5, "Set Gathering Algorithm")
            menu.add_option(6, "Toggle Debug Mode")
            menu.add_option(7, "Back")

            info = "Current Settings:\n"                                   \
            f"Map Size: {self.map_x}x{self.map_y}\n"                       \
            f"\n"                                                          \
            f"Worker Settings:\n"                                          \
            f"  Mode: {self.worker_mode}\n"                                \
            f"  Position: {self.starting_position}\n"                      \
            f"Cart Settings:\n"                                            \
            f"  Mode: {self.cart_mode}\n"                                  \
            f"  Positions: {' '.join(str(p) for p in self.carts)}\n"       \
            f"Gathering Algorithm: {self.gathering_algo}\n"                \
            f"Debug Mode: {self.debug}\n"

            menu.set_misc_info(info)

        elif menu_type == MenuType.ALGO_METHOD:
            menu = Menu("Set Gathering Algorithm")
            menu.add_option(1, "Use Order of Insertion")
            menu.add_option(2, "Brute Force")
            menu.add_option(3, "Back")

        elif menu_type == MenuType.WORKER_POSITION:
            menu = Menu("Set Starting Worker Position Mode")
            menu.add_option(1, "Randomly Set Position")
            menu.add_option(2, "Manually Set Position")
            menu.add_option(3, "Back")

        elif menu_type == MenuType.CART_POSITION:
            menu = Menu("Set Cart Position Mode")
            menu.add_option(1, "Randomly Set Position")
            menu.add_option(2, "Manually Set Position")
            menu.add_option(3, "Back")

        if menu:
            menu.display(clear=clear)


    def generate_map(self, positions=None):
        """
        Generates list of lists to represent a map of carts.

        'S' character represents starting worker position.
        'C' characters represent carts.

        The starting worker position will be placed as specified by the internal
        starting position.
        Carts will be randomly placed in other places on the map. A random
        number of carts will be placed between a minimum and maximum number of
        carts.

        Returns:
            grid (list of lists): Map which contains worker starting position
                                  and randomly placed carts.

            inserted_order (list of tuples): positions of carts in order of when
                                             inserted to grid
        """
        # Create list of lists to generate map
        # x is number of columns, y is number of rows
        grid = [['_' for _ in range(self.map_x)] for _ in range(self.map_y)]

        # Get order of list of carts inserted
        inserted_order = []

        # Set the starting position (Defaults to (0, 0))
        grid[self.starting_position[1]][self.starting_position[0]] = 'S'

        # Insert cart positions
        if positions is None:
            if self.debug:
                print(self.carts)

            positions = self.carts

        if self.debug:
            print(positions)

        for position in positions:
            # Set position in grid
            x, y = position
            grid[y][x] = 'C'
            inserted_order.append((x, y))

        return grid, inserted_order

    def display_map(self):
        """
        Prints map to screen with a legend. Map will be centered within the
        banner.

        Examples:
            >>> ShoppingForCarts.display_map()
            ------------------------------------------------------------
                              Shopping Cart Map Layout
            ------------------------------------------------------------
                                    0 S _ C _ _
                                    1 _ C _ C _
                                    2 _ _ _ _ _
                                    3 C _ C C C
                                    4 _ _ _ C _
                                      0 1 2 3 4

                                      LEGEND:
                             'S': Worker Starting Spot
                                 'C': Shopping Cart
                          Positions are labeled as (X, Y)
        """
        banner_length = 60
        banner = Menu("Shopping Cart Map Layout")
        banner.display()

        for i, row in enumerate(self.map):
            row_string = f"{i} " + " ".join(val for val in row)
            print(row_string.center(banner_length))

        print(" " + " ".join(str(i) for i in range(len(self.map[0]))).center(banner_length))

        print("")
        print("LEGEND:".center(banner_length))
        print("'S': Worker Starting Spot".center(banner_length))
        print("'C': Shopping Cart".center(banner_length))
        print("Positions are labeled as (X, Y)".center(banner_length))
        print("")

    def move_to_target(self, start, end):
        """
        Helper function to evaluate move to make between a start and end
        position.

        Args:
            start (tuple): starting position specified as (X, Y) position
            end (tuple): end position to move to specified as (X, Y) position

        Returns:
            move (str): string describing move to make to reach position

        Examples:
            >>> ShoppingForCarts.move_to_target((0, 0), (2, 0))
            "From (0, 0), move right 2 to (2, 0).", (2, 0)
        """
        current_position = start
        x_done = y_done = False
        x_direction = y_direction = None

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
                y_direction = "up"

            # Move Down
            elif y_diff > 0:
                y_position = (current_position[0], current_position[1] + y_diff)
                y_direction = "down"

        move = f"From {start}"
        if x_direction and y_direction:
            move += f", move {x_direction} {abs(x_diff)} and move {y_direction} {abs(y_diff)}"
        elif x_direction:
            move += f", move {x_direction} {abs(x_diff)}"
        elif y_direction:
            move += f", move {y_direction} {abs(y_diff)}"
        move += f" to {end}."

        return move, end

    def gather_brute_force(self, targets):
        """
        Performs brute force algorithm to gather all valid permutations of desired path then 
        finds smallest path.

        Args:
            targets (list of tuples): positions of carts

        Returns:
            min_path (list of tuples): list of cart positions to traverse in order
        """

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

                    if self.debug:
                        print(path[i], path[j], abs(path[i][0] - path[j][0]), abs(path[i][1] - path[j][1]))

            if self.debug:
                print(path, distance)

            if smallest is None or distance < smallest:
                smallest = distance
                min_path = list(path).copy()

        if self.debug:
            print(min_path, smallest)

        return min_path

    def get_targets(self):
        """
        Gets full list of targets. Uses stored worker starting position as first and last
        indices.

        Returns:
            targets (list of tuples): positions of worker and carts
        """
        targets = []

        if self.inserted_order:
            targets = self.inserted_order.copy()
            targets.insert(0, self.starting_position)
            targets.append(self.starting_position)

        return targets


    def get_descriptive_steps(self, targets):
        """
        Gets list of directions to gather all carts beginning from internal
        starting position and returning to starting position.

        Algorithm gathers list of target carts by prioritizing top rows and
        moves down to the last row.

        Carts are then gathered in order by list of targets. Worker may only
        move in directions up, down, left, or right.

        Returns:
            path (list of str): list of directions worker should take to gather
                                all carts from starting position
        """
        path = []
        start = targets.pop(0)
        end = targets.pop()

        path.append(f"Start at position {start}!")
        current_position = start

        for target in targets:
            move, current_position = self.move_to_target(current_position, target)
            path.append(move)
            path.append("Pick up cart.")

        back_to_start, _ = self.move_to_target(current_position, end)
        path.append(back_to_start)
        path.append("Pickup completed.")

        return path

    def get_carts(self, option):
        path = []

        if option == AlgoMethod.ORDER_OF_INSERTION:
            targets = self.get_targets()
            result = self.get_descriptive_steps(targets)
            return result

        elif option == AlgoMethod.BRUTE_FORCE:
            targets = self.get_targets()
            path = self.gather_brute_force(targets)
            return self.get_descriptive_steps(path)

    def verify_settings_range(self, value, minimum, maximum):
        """
        Helper function to validate integer is within specified range.

        Args:
            value (int): integer value to validate
            minimum (int): smallest integer value allowed
            maximum (int): largest integer value allowed

        Returns:
            True if value falls within minimum and maximum value.
            False otherwise.
        """
        try:
            if minimum <= int(value) <= maximum:
                return True
            elif int(value) < minimum:
                print(f"Try again! {value} is too small, must be minimum {minimum}.")
            elif int(value) > maximum:
                print(f"Try again! {value} is too large, must be maximum {maximum}.")
            else:
                print(f"Invalid option: {value}")
        except Exception as e:
            print(f"Invalid option: {value}")

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
        maximum_x = 20
        maximum_y = 20

        success = False

        x = input(f"Set Map X Size (Currently {self.map_x}, Minimum {minimum_x}, Max {maximum_x}): ")
        y = input(f"Set Map Y Size (Currently {self.map_y}, Minimum {minimum_y}, Max {maximum_y}): ")

        x_success = self.verify_settings_range(x, minimum_x, maximum_x)
        y_success = self.verify_settings_range(y, minimum_y, maximum_y)

        if x_success and y_success:
            self.map_x  = int(x)
            self.map_y = int(y)
            success = True

        print(f"Current Map Size: {self.map_x}x{self.map_y}")
        return success

    def set_worker_starting_position(self):
        """
        Sets internal starting position for worker.

        Requires user input to be within limits of map size.

        Returns:
            success (bool): Status to indicate if worker position set successfully 
        """
        success = False

        if self.worker_mode == GenerateMode.RANDOM:
            while not success:
                x = random.randint(0, self.map_x - 1)
                y = random.randint(0, self.map_y - 1)

                # Verify Cart and Worker Positions do not overlap
                if (x, y) not in self.carts:
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

                    # Overlapping Cart and Worker Positions
                    if (int(x), int(y)) in self.carts:
                        print("Worker position is the same as a cart position! Please Try Again.\n")

                    else:
                        self.starting_position = (int(x), int(y))
                        success = True

                print(f"Current Worker Starting Position: {self.starting_position}")
        return success

    def get_cart_positions(self):
        """
        Gets cart positions depending on cart position mode.

            Cart Modes:
            1. Manual Mode
                A. Choose number of carts
                B. Set positions for each cart (cannot repeat position)

            2. Random Mode
                A. Set minimum number of carts
                B. Set maximum number of carts


        Returns:
            cart_positions (list of tuples): positions of carts on the map
        """
        cart_positions = []

        if self.cart_mode == GenerateMode.RANDOM:
            number_of_carts = random.randint(self.minimum_carts, self.maximum_carts)

            for _ in range(number_of_carts):
                success = False
                while not success:
                    x = random.randint(0, self.map_x - 1)
                    y = random.randint(0, self.map_y - 1)

                    position = (x, y)
                    # Repeat Cart Position
                    if position in cart_positions:
                        print("Repeat cart position! Please Try Again.\n")

                    # Overlapping Cart and Worker Positions
                    elif position == self.starting_position:
                        print("Cart position is the same as the worker position! Please Try Again.\n")

                    else:
                        cart_positions.append(position)
                        success = True

        elif self.cart_mode == GenerateMode.MANUAL:
            banner = Menu("Set Cart Starting Position")
            banner.display()

            number_of_carts = input(f"Set number of carts (Range {self.minimum_carts} to {self.maximum_carts}): ")

            cart_success = self.verify_settings_range(number_of_carts, self.minimum_carts, self.maximum_carts)

            if not cart_success:
                print("Failed to set number of carts in range.")
                return []

            for cart in range(int(number_of_carts)):
                x_success = False
                y_success = False

                while not x_success or not y_success:

                    print(f"\nFor Cart #{cart + 1}:")
                    x = input(f"Set X position (0 - {self.map_x - 1}): ")
                    y = input(f"Set Y position (0 - {self.map_y - 1}): ")

                    x_success = self.verify_settings_range(x, 0, self.map_x)
                    y_success = self.verify_settings_range(y, 0, self.map_y)

                    position = (int(x), int(y))
                    # Within Valid Range
                    if x_success and y_success:

                        # Repeat Cart Position
                        if position in cart_positions:
                            print("Repeat cart position! Please Try Again.\n")

                        # Overlapping Cart and Worker Positions
                        elif position == self.starting_position:
                            print("Cart position is the same as the worker position! Please Try Again.\n")

                        else:
                            cart_positions.append(position)
                            
                    else:
                        print("Invalid position! Please Try Again!\n")

        return cart_positions

    def set_cart_minimum_maximum(self):
        """
        """
        banner = Menu("Set Cart Minimum and Maximum Amount")
        banner.display()

        success = False

        max_carts = (self.map_x) * (self.map_y) - 1

        while not success:
            user_max = input(f"Set Maximum Amount (Currently {self.maximum_carts}, Maximum {max_carts}): ")
            user_min = input(f"Set Minimum Amount (Currently {self.minimum_carts}): ")

            max_success = self.verify_settings_range(user_max, int(user_min), max_carts)
            min_success = self.verify_settings_range(user_min, 0, int(user_max) - 1)

            if self.debug:
                print(f"Cart Min Success & Max Success: {max_success}, {min_success}")

            if max_success and min_success:
                self.minimum_carts = int(user_min)
                self.maximum_carts = int(user_max)
                success = True

            else:
                print("Invalid values, please try again!")

        print(f"Minimum Carts: {self.minimum_carts}")
        print(f"Maximum Carts: {self.maximum_carts}")
        return success

    def handle_option(self, option):
        """
        Handles menu options for main application and corresponding submenus.

        Args:
            option (str): choice user chooses from main menu
        """
        # Go Get Carts
        update = True
        clear = True

        if option == '1':
            # Display map at start of menu
            if update:
                self.display_map()

                # Evaluate directions to gather carts
                path = self.get_carts(self.gathering_algo)

                # Display directions
                print("Directions:")
                print("-----------")
                for step, action in enumerate(path):
                    print(f"{step}. {action}")

            else:
                update = True

            # Don't clear for first Go Get Carts Menu
            clear = False

            while True:
                # Create carts menu
                if update:
                    self.display_menu(MenuType.GO_GET_CARTS, clear=clear)
                else:
                    update = True
                    clear = True

                # Handle menu options
                suboption = input("> ")

                # Generate New Map
                if suboption == '1':
                    print("Generate New Map")
                    self.carts = self.get_cart_positions()
                    self.map, self.inserted_order = self.generate_map()
                    self.display_map()

                    # Evaluate directions to gather carts
                    path = self.get_carts(self.gathering_algo)

                    # Display directions
                    print("Directions:")
                    print("-----------")
                    for step, action in enumerate(path):
                        print(f"{step}. {action}")

                    clear = False

                # Back
                elif suboption == '2':
                    break
                else:
                    print("Invalid choice. Try again.")
                    update = False

        # Generate Map
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

                # Set Map Size
                if suboption == '1':
                    clear = self.set_map_size()
                    self.map, self.inserted_order = self.generate_map()

                # Set Worker Starting Position
                elif suboption == '2':
                    while True:
                        if update:
                            self.display_menu(MenuType.WORKER_POSITION, clear=clear)
                        else:
                            update = True
                            clear = True

                        mode_option = input(f"Set Worker Position Mode (Currently {self.worker_mode}): ")

                        # Set random starting position
                        if mode_option == '1':
                            self.worker_mode = GenerateMode.RANDOM

                            self.set_worker_starting_position()
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
                            print("Invalid choice. Try again.")
                            update = False
                            clear = False

                # Set Cart Position Mode
                elif suboption == '3':
                    while True:
                        if update:
                            self.display_menu(MenuType.CART_POSITION, clear=clear)
                        else:
                            update = True
                            clear = True

                        mode_option = input(f"Set Cart Position Mode (Currently {self.cart_mode}): ")

                        # Set random starting position
                        if mode_option == '1':
                            self.cart_mode = GenerateMode.RANDOM

                            self.carts = self.get_cart_positions()
                            break
                        
                        # Set manual starting position
                        elif mode_option == '2':
                            self.cart_mode = GenerateMode.MANUAL

                            self.carts = self.get_cart_positions()

                            # Generate map with new cart positions
                            self.map, self.inserted_order = self.generate_map()
                            break

                        # Back
                        elif algo_option == '3':
                            break

                        else:
                            print("Invalid choice. Try again.")
                            update = False
                            clear = False

                # Set Cart Minimum and Maximum Amount
                elif suboption == '4':
                    self.set_cart_minimum_maximum()
                    self.carts = self.get_cart_positions()


                # Set Algorithm Method
                elif suboption == '5':
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

                        # Back
                        elif algo_option == '3':
                            break

                        else:
                            print("Invalid choice. Try again.")
                            update = False
                            clear = False

                # Toggle Debug
                elif suboption == '6':
                    self.debug = not self.debug

                # Back
                elif suboption == '7':
                    break
                else:
                    print("Invalid choice. Try again.")
                    update = False

        # Exit
        elif option == '3':
            print("Exiting...")
            exit()
        else:
            print("Invalid choice. Try again.")
            update = False

    def run(self):
        """
        Helper function to run application. Loops main menu until user chooses
        to exit.
        """
        while True:
            self.display_menu(MenuType.MAIN_MENU)

            choice = input("> ")
            self.handle_option(choice)

def main():
    app = ShoppingForCarts()
    app.run()

if __name__ == "__main__":
    main()
