from enum import Enum

INFINITY = float('inf');

class MenuType(Enum):
    """
    Constants for menu types.
    """
    MAIN_MENU = 0
    VIEW_MAP = 1
    SETTINGS = 2
    ADVANCED_SETTINGS = 3
    ALGO_METHOD = 4
    WORKER_POSITION = 5
    ITEM_POSITION = 6
    LOAD_PRODUCT_FILE = 7
    LOAD_TEST_CASE_FILE = 8

class AlgoMethod(Enum):
    """
    Constants for algorithms used to gather items.
    """
    ORDER_OF_INSERTION = "Order of Insertion"
    BRUTE_FORCE = "Brute Force"
    DIJKSTRA = "Dijkstra"

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
