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
    TSP_ACCESS_TYPE = 6
    WORKER_START_POSITION = 7
    WORKER_ENDING_POSITION = 8
    ITEM_POSITION = 9
    LOAD_PRODUCT_FILE = 10
    LOAD_TEST_CASE_FILE = 11

class AlgoMethod(Enum):
    """
    Constants for algorithms used to gather items.
    """
    ORDER_OF_INSERTION = "Order of Insertion"
    BRUTE_FORCE = "Brute Force"
    DIJKSTRA = "Dijkstra"
    BRANCH_AND_BOUND = "Branch and Bound"
    LOCALIZED_MIN_PATH = "Localized Minimum Path"
    REPETITIVE_NEAREST_NEIGHBOR = "Repetitive Nearest Neighbor"

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

class AccessType(Enum):
    """
    Constants to choose branch and bound access type.
    """
    SINGLE_ACCESS = "Single Access"
    MULTI_ACCESS = "Multi Access"

    def __str__(cls):
        return cls.value
