# Item Routing System

Welcome to Item Routing System by Supa Carts!

Item Routing System is a text-based item gathering application used to provide store workers with directions to gather items around a warehouse.

# User Instructions
1. Download the [latest executable here](https://github.com/josephabero/ShoppingForCarts/releases) for the appropriate Operating System.
2. Run the application by double clicking the executable in downloaded folder location.

# Development Instructions
## Setup
```
make setup
make build
```

## Run Application
```
make run
```

## Delete Application
```
make clean
```

# Known Issues
1. Current Branch and Bound Implementation for Single Access does not guarantee optimal path due to limited number of path choices. This is intended, **only Multi Access Branch and Bound guarantees optimal path**.
2. On Windows, `SIGALRM` is an unknown signal, so any algorithm with a timeout exception will crash.
3. On Windows, some ASCII values in the menu may be unknown and appear as Question Blocks.

# Completed Tasks (For Beta Release 1: 1.3.0)

Justin Sung

	Repetitive Nearest Neighbor Algorithm
	Matrix Reduction


Wanbing Hua

	Localized Minimum Path Algorithm
	Dynamic Ending Position

Joseph Abero

	Branch and Bound Traversal
	Map Behavior
		Path to Order
		Create Order
			Individual
			Orders from File
	Menu Interface
	Settings
		Maximum Run Time
	 	Advanced Settings
	 		Test Cases
