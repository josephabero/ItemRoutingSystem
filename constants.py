from enum import Enum

INFINITY = float('inf')

class MenuType(Enum):
    """
    Constants for menu types.
    """
    MAIN_MENU = 0
    VIEW_MAP = 1
    SETTINGS = 2
    ADVANCED_SETTINGS = 3
    GATHER_ALGO_METHOD = 4
    TSP_ALGO_METHOD = 5
    WORKER_START_POSITION = 6
    WORKER_ENDING_POSITION = 7
    ITEM_POSITION = 8
    LOAD_PRODUCT_FILE = 9
    LOAD_TEST_CASE_FILE = 10

class AlgoMethod(Enum):
    """
    Constants for algorithms used to gather items.
    """
    ORDER_OF_INSERTION = "Order of Insertion"
    BRUTE_FORCE = "Brute Force"
    DIJKSTRA = "Dijkstra"
    BRANCH_AND_BOUND = "Branch and Bound"
    LOCALIZED_MIN_PATH = "Localized Minimum Path"

    def __str__(cls):
        return cls.value

class GenerateMode(Enum):
    """
    Constants for modes of generating settings.
    """
    MANUAL = "Manual"
    RANDOM = "Random"
    LOADED_FILE = "Loaded File"

    def __str__(cls):
        return cls.value

class PrintType(Enum):
    """
    Constants to choose logging mode.
    """
    NORMAL = 0
    DEBUG = 1
    MINOR = 2
