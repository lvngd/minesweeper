import random
import pickle


"""
Square class to represent each square in Minesweeper board

MinesweeperBoard class to generate the board

Minesweeper boards are a 2-D grid of squares that either contain a mine or a number
between 0-8.

In this implementation, a mine is set with a constant of 9.
"""


class Square:
	def __init__(self,x,y,constant,original_constant,val=None,uncovered=False,flagged=False,constraints=[]):
		self.x = x
		self.y = y 
		self.constant = constant
		self.original_constant = constant
		self.val = val 
		self.uncovered = uncovered
		self.flagged = flagged
		self.constraints = constraints
		 
	def __str__(self):
		return "{}".format(self.constant)

	def __repr__(self):
		if self.uncovered:
			return "{}".format(self.original_constant)
		elif self.flagged:
			return "{}".format(self.original_constant)
		else:
			return "-"
		

class MinesweeperBoard:
	def __init__(self,rows,columns,num_mines,starting_point=None):
		self.rows = rows
		self.cols = columns
		self.num_mines = num_mines
		self.starting_point = self.get_starting_point(starting_point)
		self.board_coordinates = self.get_coordinates()
		self.board,self.mine_coordinates = self.place_mines()
		self.marked_squares = set()
		self.mines_flagged = set()
		#constraints list
		self.moves = []

	def show_board(self):
		for row in self.board:
			print(row)
		return

	def get_neighbors(self,x,y):
		neighbors = []
		possible_neighbors = [(x-1,y),(x-1,y+1),(x,y-1),(x+1,y-1),(x+1,y),(x+1,y+1),(x,y+1),(x-1,y-1)]
		for n in possible_neighbors:
			if 0 <= n[0] <= self.cols-1 and 0 <= n[1] <= self.rows-1:
				neighbors.append(n)
		return neighbors

	def get_coordinates(self):
		"""return list of coordinates of the board minus the starting point"""
		return [(x, y) for x in range(0,self.cols) for y in range(0, self.rows) if (x,y) != self.starting_point]

	def get_starting_point(self,starting_point):
		if not starting_point:
			#random starting point
			start_x = random.randint(0,self.cols-1)
			start_y = random.randint(0,self.rows-1)
			starting_point = (start_x,start_y)
		return starting_point

	def place_mines(self):
		"""mines are set with a constant of 9"""
		mine_coordinates = random.sample(self.board_coordinates, self.num_mines)
		#board is a 2-D matrix
		board = [[Square(x=i,y=j,constant=0,original_constant=0,constraints=self.get_neighbors(j,i)) for i in range(0,self.rows)] for j in range(0,self.cols)]
		for mine in mine_coordinates:
			x,y = mine 
			board[x][y].constant = 9
			board[x][y].original_constant = 9
			neighbors = [(x-1,y),(x-1,y+1),(x,y-1),(x+1,y-1),(x+1,y),(x+1,y+1),(x,y+1),(x-1,y-1)]
			for n in neighbors:
				if 0 <= n[0] <= self.cols-1 and 0 <= n[1] <= self.rows-1 and n not in mine_coordinates:
					board[n[0]][n[1]].constant += 1
					board[n[0]][n[1]].original_constant += 1
		return board,mine_coordinates