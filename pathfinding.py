"""
This module will create a tkinter UI and allow for searching with various startpoints,
endpoints, barriers and search algorithms. The module contains the Pathfinder class which
will setup the UI and logic for two pathfinding algorithms, breadth first search and A* search.
The module also contains the MyButton class which inherits from a tkinter button and is used in
the Pathfinder class.
"""

from tkinter import *
from queue import Queue, PriorityQueue
import sys
import math

# Define colors used in pathfinding/searching.
STARTCOLOR = "yellow"
ENDCOLOR = "blue"
BACKGROUNDCOLOR = "black"
SEARCHCOLOR = "cyan"
PATHCOLOR = "green"
BARRIERCOLOR = "red"

# Variable used to create a SIZE * SIZE area to search.
SIZE = 50

# Set time delay to color squares on screen. This is required to prevent pressing miltiple buttons at once.
TIME_DELAY = 100

# Define max value for a float. This is used in aStar search.
FLOAT_MAX = sys.float_info.max

"""
The Pathfinder class will setup the UI and logic for searching using two algorithms, breadth first search
and A* search. It will also allow let the user pick different start and end points, create a barrier, and
show the search area.
"""
class Pathfinder():
	def __init__(self, frame, x, y):
		"""
		This creates a UI and search area to use the searching algorithms. 

		:param frame: The mainframe that will appear on screen and contain all other widgets.

		:param x: The height of the search area.

		:param y: The width of the search area.
		"""

		self.frame = frame
		self.uiframe = Frame(self.frame)
		self.gridframe = Frame(self.frame)

		self.uiframe.grid(row=0, column=0)
		self.gridframe.grid(row=1, column=0)

		self.__initiate_buttons_for_ui()

		self.buttons = []
		self.buttonImage = PhotoImage(width=8, height=8)
		self.startPoint = None
		self.endPoint = None

		for a in range(y):
			self.buttons.append([])
			for b in range(x):
				button = MyButton(self.gridframe)
				button.grid(column=b, row=a)
				button.configure(image=self.buttonImage)
				button.configure(bg=BACKGROUNDCOLOR)
				self.buttons[a].append(button)

		self.__set_buttons_for_start_point()

	def __initiate_buttons_for_ui(self):
		"""
		Create and setup the UI buttons to control the searching.
		"""

		self.label = Label(self.uiframe, text="Select a start point.")
		self.label.grid(row=0, column=0)

		self.nextButton = Button(self.uiframe, text="Next", command=self.__set_buttons_for_start_point)
		self.nextButton.grid(row=0, column=5)

		self.resetButton = Button(self.uiframe, text="Reset")
		self.resetButton.grid(row=0, column=6)

		self.searchType = StringVar()
		self.breadth = Radiobutton(self.uiframe, text='Breadth First Search', variable=self.searchType, value='Breadth')
		self.aStar = Radiobutton(self.uiframe, text='A*', variable=self.searchType, value='A*')
		self.breadth.select()

		self.visibleSearch = StringVar()
		self.visible = Checkbutton(self.uiframe, text='Visible search', variable=self.visibleSearch, onvalue='True', offvalue='False')
		self.visible.deselect()

	def __reset_background_color(self, square):
		"""
		Changes the color of the provided point to BACKGROUNDCOLOR.

		:param square: This is a list containing the row and column of the square in the buttons array to reset to
					   BACKGROUNDCOLOR.
		"""

		if square is not None:
			self.buttons[square[0]][square[1]].color_change(BACKGROUNDCOLOR)

	def __remove_start_point(self):
		"""
		Changes the background of the current start point and clears the start point variable.
		"""
		self.__reset_background_color(self.startPoint)
		self.startPoint = None

	def __remove_end_point(self):
		"""
		Changes the background of the current end point and clears the end point variable.
		"""

		self.__reset_background_color(self.endPoint)
		self.endPoint = None

	def __reset_UI(self):
		"""
		Clear the colors from any of the search area, remove the start and end points,
		and reset the UI options.
		"""
		self.__remove_start_point()
		self.__remove_end_point()
		self.frame.after(TIME_DELAY*2, self.__clear_colors, [BARRIERCOLOR, PATHCOLOR, SEARCHCOLOR])

		self.breadth.grid_forget()
		self.aStar.grid_forget()
		self.visible.grid_forget()

		self.visible.deselect()
		self.breadth.select()

		self.__set_buttons_for_start_point()

	def __heuristic(self, point):
		"""
		This function takes a point and returns the heuristic value from the point
		to the end point. This is to be used in the A* search algorithm. 
		The heuristic is the Diagonal Distance heuristic as described here:
		https://theory.stanford.edu/~amitp/GameProgramming/Heuristics.html

		:param point: This is a list containing the row and column of the point to calculate
					  the diagonal distance to the self.endPoint variable.

		:return: The diagonal distance heuristic value from the point to the self.endPoint.
		"""

		dx = abs(point[0] - self.endPoint[0])
		dy = abs(point[1] - self.endPoint[1])

		val = (dx + dy) + (math.sqrt(2) - 2) * min([dx, dy])

		return val

	def __add_neighbors_to_priority_queue(self, point, priorityQueue, graph):
		"""
		Takes in a list containing the row and column of a point, the current priority queue, and the current graph and
		adds all of the neighbors of the current point(so long as they haven't been visited and
		they are not a barrier) to the priority queue and updates the graph accordingly.
		This is used with the A* search algorithm.

		:param point: This is a list that contains the row and column of the point whose neighbors are to be added
					  to the priority queue.

		:param priorityQueue: The priorityQueue that is used in the A* heuristic search algorithm.

		:param graph: A 2D array containing a dict that holds the "cost" and "parent" keys associated with
					  each point in the search area.
		"""

		vectors = [[-1, -1], [-1, 0], [-1, 1],
				   [0, -1], [0, 1], 
				   [1, -1], [1, 0], [1, 1]]

		newCost = graph[point[0]][point[1]]["cost"] + 1

		for vector in vectors:
			newRow = point[0] + vector[0]
			newColumn = point[1] + vector[1]
			if self.__valid_point([newRow, newColumn]):
				if self.buttons[newRow][newColumn]["background"] != BARRIERCOLOR:
					if float(newCost) < graph[newRow][newColumn]["cost"]:
						graph[newRow][newColumn]["cost"] = newCost
						graph[newRow][newColumn]["parent"] = point
						priority = float(newCost) + self.__heuristic([newRow, newColumn])
						priorityQueue.put((priority, [newRow, newColumn]))

	def __aStarSearch(self):
		"""
		Uses A* heuristic search algorithm to find and color a path from the starting point to
		the ending point. Also colors the search area if the user asked for a visible search.
		"""

		# creates a new 2D array that will contain the search information(cost and parent variables) for each square
		graph = []
		for a in range(len(self.buttons)):
			graph.append([])
			for b in range(len(self.buttons[a])):
				square = {}
				square["cost"] = FLOAT_MAX
				square["parent"] = None
				graph[a].append(square)

		# start the search algorithm
		q = PriorityQueue()

		graph[self.startPoint[0]][self.startPoint[1]]["cost"] = 0
		self.__add_neighbors_to_priority_queue(self.startPoint, q, graph)

		while not q.empty():
			node = q.get()[1]
			if node == self.endPoint:
				break
			else:

				# color the search area if applicable
				if self.visibleSearch.get() == "True":
					self.frame.after(TIME_DELAY, self.buttons[node[0]][node[1]].color_change, SEARCHCOLOR)
				self.__add_neighbors_to_priority_queue(node, q, graph)

		# get and color the path from start point to the end point
		path = self.__get_path_from_graph(graph)
		self.frame.after(TIME_DELAY, self.__color_path, path)

	def __breadthFirstSearch(self):
		"""
		Uses a breadth first search algorithm to find and color a path from the starting point to
		the ending point. Also colors the search area if the user asked for a visible search.
		"""

		# creates a new 2D array that will contain the search information(visited and parent) for each button
		graph = []
		for a in range(len(self.buttons)):
			graph.append([])
			for b in range(len(self.buttons[a])):
				thisSquare = {}
				thisSquare["visited"] = False
				thisSquare["parent"] = None
				graph[a].append(thisSquare)

		# search from the start point to the end point 
		q = Queue()
		graph[self.startPoint[0]][self.startPoint[1]]["visited"] = True
		self.__add_neighbors_to_queue(self.startPoint, q, graph)

		while not q.empty():
			node = q.get()
			if node == self.endPoint:
				break
			else:
				# color the search area if applicable
				if self.visibleSearch.get() == "True":
					self.frame.after(TIME_DELAY, self.buttons[node[0]][node[1]].color_change, SEARCHCOLOR)
				self.__add_neighbors_to_queue(node, q, graph)

		# color the path from the start point to the end point
		path = self.__get_path_from_graph(graph)
		self.frame.after(TIME_DELAY, self.__color_path, path)

	def __get_path_from_graph(self, graph):
		"""
		Use the graph provided that contains the parent information provided from the search algorithms
		to determine the path from the start point to the end point. The returned path does not include the start 
		or end points.

		:param graph: This is a 2D array containing dicts with the parent key corresponding to the shortest path
					  from the start node to this point.

		:return: This is a list containing all points from the start point to the end point. Each point is denoted as a list that
				 contains the row and column of each point.
		"""

		path = []
		currentNode = graph[self.endPoint[0]][self.endPoint[1]]["parent"]
		while currentNode is not None:
			path.append(currentNode)
			currentNode = graph[currentNode[0]][currentNode[1]]["parent"]

		if len(path) != 0:
			path.pop()

		path.reverse()

		return path

	def __clear_colors(self, colors):
		"""
		Cycles through the buttons in the search area and resets the colors
		of any buttons that match a color provided in the colors parameter.

		:param colors: This is a list containing color strings. If a button has
					   this as their current color, the button's color is set to BACKGROUNDCOLOR.
		"""

		for rows in self.buttons:
			for button in rows:
				for color in colors:
					if button["background"] == color:
						button.color_change(BACKGROUNDCOLOR)
						break

	def __color_path(self, path):
		"""
		Uses the provided path list and updates the color of the buttons on the path 
		from the start point to the end point to PATHCOLOR.

		:param path: This is a list containing the row and column information of a path
					 from the start point to the end point. The list elements are lists that
					 contains the row and column of each square in the path.
		"""
		for square in path:
			button = self.buttons[square[0]][square[1]]
			self.frame.after(TIME_DELAY, button.color_change, PATHCOLOR)
			# button.color_change(PATHCOLOR)

	def __valid_point(self, point):
		"""
		Determines if the point provided is a valid point in the current
		search area.

		:param point: This is a list that contains the row and column of the point to be tested.

		:return: Boolean that says if the point exists in the current buttons grid.
		"""

		if point[0] < 0 or point[0] >= len(self.buttons):
			return False
		if point[1] < 0 or point[1] >= len(self.buttons[0]):
			return False

		return True

	def __add_neighbors_to_queue(self, point, q, graph):
		"""
		Takes in the current point, the current queue, and the current graph containing the information for each square and
		adds all of the neighbors of the current point(so long as they haven't been visited and
		they are not a barrier) to the queue and updates the graph accordingly.

		:param point: This is a list containing the row and column information of a point whose neighbors should be added to the
					  queue.

		:param q: This is the queue used in the breadth first search function.

		:param graph: This is a 2D graph that contains a dict representing the parent and visited information for each point.
		"""

		vectors=[ [0, -1], [-1, 0], [1, 0], 
				  [0, 1], [-1, -1],
				  [1, -1], [-1, 1], [1, 1]]

		for vector in vectors:
			newRow = point[0] + vector[0]
			newColumn = point[1] + vector[1]

			if self.__valid_point([newRow, newColumn]):

				if graph[newRow][newColumn]["visited"] == False and self.buttons[newRow][newColumn]["background"] != BARRIERCOLOR:
					graph[newRow][newColumn]["parent"] = point
					graph[newRow][newColumn]["visited"] = True
					q.put([newRow, newColumn])

	def __search(self):
		"""
		Clears any previous searches from the search area and then calls the appropriate
		pathfinging algorithm.
		"""
		self.__clear_colors([SEARCHCOLOR, PATHCOLOR])

		if self.searchType.get() == "Breadth":
			self.__breadthFirstSearch()
		elif self.searchType.get() == "A*":
			self.__aStarSearch()

	def __set_buttons_for_start_point(self):
		"""
		This function sets up the squares in the search area to select the starting point,
		and updates the UI buttons appropriately.
		"""

		self.gridframe.unbind_class("MyButton", "<Button-1>")
		self.gridframe.bind_class("MyButton", "<Button-1>", self.__select_start_point)
		self.label.configure(text="Select a start point.")
		self.nextButton.configure(command=self.__set_buttons_for_end_point, text="Next")
		self.resetButton.configure(command=self.__remove_start_point, text="Reset")

	def __set_buttons_for_end_point(self):
		"""
		Sets up the squares in the search area to select the end point,
		and updates the UI buttons appropriately.
		"""

		if self.startPoint is not None:
			self.label.configure(text="Select an end point.")
			self.gridframe.unbind_class("MyButton", "<Button-1>")
			self.gridframe.bind_class("MyButton", "<Button-1>", self.__select_end_point)
			self.nextButton.configure(command=self.__set_buttons_for_barrier)
			self.resetButton.configure(command=self.__remove_end_point)

	def __set_buttons_for_barrier(self):
		"""
		Sets up the squares in the search area to select a barrier if the user wants one and
		updates the UI buttons appropriately.
		"""

		if self.endPoint is not None:
			self.label.configure(text="Create a barrier if desired.")
			self.gridframe.unbind_class("MyButton", "<Button-1>")
			self.gridframe.unbind_class("MyButton", "<B1-Motion>")
			self.gridframe.bind_class("MyButton", "<Button-1>", self.__select_barrier)
			self.gridframe.bind_class("MyButton", "<B1-Motion>", self.__select_barrier)
			self.nextButton.configure(command=self.__update_ui_for_options)
			self.resetButton.configure(command= lambda color=BARRIERCOLOR: self.__clear_colors([color]))

	def __update_ui_for_options(self):
		"""
		Remove square functionality and update the UI for the user to select the searching options.
		"""

		self.gridframe.unbind_class("MyButton", "<Button-1>")
		self.gridframe.unbind_class("MyButton", "<B1-Motion>")

		self.breadth.grid(row=0, column=1)
		self.aStar.grid(row=0, column=3)

		self.visible.grid(row=0, column=4)

		self.label.configure(text="How do you want to search?")
		self.nextButton.configure(text="Start search", command=self.__search)
		self.resetButton.configure(text="Start over", command=self.__reset_UI)
			
	def __update_color_of_newButton_reset_oldButton_color(self, color, newButton, oldButton=None):
		"""
		Updates the provided button to the provided color, and changes
		the color of the previous point if one is provided/exists.

		:param color: This is a string that contains the color that the new button should be changed to.

		:param newButton: This is a list containing the row and column information of the new button.

		:param oldButton: This is a list containing the row and column information of the old button whose color should be set to BACKGROUNDCOLOR.
		"""

		if newButton is not None:
			if oldButton is None:
				newButton.color_change(color)

			else:
				oldButton = self.buttons[oldButton[0]][oldButton[1]]
				oldButton.color_change(BACKGROUNDCOLOR)
				newButton.color_change(color)

	def __select_start_point(self, event):
		"""
		This is used to get the start point when the user clicks on a point. Gets the square from the search area 
		that was selected as the startpoint, updates the color of the new start point and the previous start point if necessary, 
		and updates the start point variable.

		:param event: This is the click event from the tkinter button.
		"""

		button = self.__get_widget(self)
		if button is not None:
			self.__update_color_of_newButton_reset_oldButton_color(STARTCOLOR, button, self.startPoint)
			self.startPoint = self.__get_widget_row_column(button)

	def __select_end_point(self, event):
		"""
		This is used to get the end point when the user clicks on a point. Gets the square from the search area 
		that was selected as the end point, updates the color of the new end point and the previous end point if necessary, 
		and updates the end point variable.

		:param event: This is the click event from the tkinter button.
		"""

		button = self.__get_widget(self)
		if button is not None:
			gridInfo = button.grid_info()
			if [gridInfo["row"], gridInfo["column"]] != self.startPoint:
				self.__update_color_of_newButton_reset_oldButton_color(ENDCOLOR, button, self.endPoint)
				self.endPoint = self.__get_widget_row_column(button)

	def __get_widget(self, event):
		"""
		This function will return the widget that the mouse is currently hovering over.

		:param event: This is the click event from the tkinter button.

		:return: This is a widget that containd the mouse's location.
		"""

		return self.gridframe.winfo_containing(self.gridframe.winfo_pointerx(), self.gridframe.winfo_pointery())

	def __get_widget_row_column(event, widget):
		"""
		Returns the row and column variables as a list provided from the widget's grid_info command.

		:param widget: This is a tkinter widget object that the row and column information is needed from.

		:return: This is a list containing the row and column information of the provided widget.
		"""

		gridInfo = widget.grid_info()
		return [gridInfo["row"], gridInfo["column"]]

	def __select_barrier(self, event):
		"""
		This function will get the button that the cursor is hovering over and change the color to
		the BARRIERCOLOR if it is a valid button to become a barrier.

		:param event: This is the click event provided by the tkinter widget.
		"""

		button = self.__get_widget(self)
		if button is not None:
			if button.__class__.__name__ == "MyButton" and not self.__button_is_start_or_end(self, button):
				button.color_change(BARRIERCOLOR)

	def __button_is_start_or_end(self, event, button):
		"""
		Determines if the provided button is the start point or end point for the search
		algorithm and returns true if it is and false if it is not.

		:param event: This is the click event provided by the tkinter widget.

		:param button: This is the button that should be checked to see if it is a start or end point.

		:return: Returns a boolean.
		"""

		buttonRowColumn = self.__get_widget_row_column(button)
		if buttonRowColumn == self.startPoint or buttonRowColumn == self.endPoint:
			return True
		else:
			return False

"""
MyButton class which inherits from a tkinter button and increases functionality. This class
is used in the Pathfinder class.
"""
class MyButton(Button):
	def __init__(self, frame):
		"""
		The constructor sets up the button with the functionality of tkinter buttons, 
		and updates the index in the bindtages to "MyButton" for identification.

		:param frame: The frame that the button is created in.
		"""

		super().__init__(frame)

		# updating the index tag of the button so that it will update and not other buttons
		bindtags = list(self.bindtags())
		index = bindtags.index("Button")
		bindtags.insert(index, "MyButton")
		self.bindtags(tuple(bindtags))

	def color_change(self, newColor):
		"""
		This function changes the color of the button to the provided color.

		:param newColor: A string that contains a hex code for the new color or a 
						 named color in tkinter.
		"""
		self.configure(bg=newColor)


def main():
	root = Tk()

	mainframe = Frame(root)
	mainframe.grid(row=0, column=0)

	Pathfinder(mainframe, SIZE, SIZE)

	root.mainloop()

main()
