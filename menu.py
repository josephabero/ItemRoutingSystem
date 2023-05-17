import os

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

        Args:
            index  (int): Position of menu to insert option to.
            option (str): Option name or description.

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
