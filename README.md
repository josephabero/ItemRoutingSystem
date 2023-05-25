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
1. Current Branch and Bound Implementation is Single Access and always begins traversal from Start node
2. Current Branch and Bound Implementation may be slower than intended as size 7 and higher input sizes take longer than 15 seconds
3. Some invalid user inputs will crash the program due to unexpected values that are not handled.
4. On Windows, `SIGALRM` is an unknown signal, so any algorithm with a timeout exception will crash.

# Completed Tasks (For Beta Release 1: 1.2.0)

Joseph Abero

	Branch and Bound Traversal
	Map Behavior
		Path to Order
		Create Order
	Menu Interface
	Settings
		Maximum Run Time
	 	Advanced Settings
	 		Test Cases

Justin Sung
	Matrix Reduction

Wanbing Hua
	Localized Minimum Path Algorithm
	Dynamic Ending Position

