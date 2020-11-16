import pickle
import random
from minesweeper import MinesweeperBoard,Square

"""
Class to solve Minesweeper puzzles as a constraint satisfaction problem.
"""

class MinesweeperSolver:
	def __init__(self,board):
		self.ms = board
		self.board = board.board
		self.num_mines_flagged = 0
		self.squares_to_probe = [self.ms.starting_point]
		self.probed_squares = set()
		self.marked_count = {}
		self.path_uncovered = []
		self.lost_game = False

	def start_game(self):
		while self.squares_to_probe:
			square = self.squares_to_probe.pop()
			uncovered = self.uncover_square(square)
			if uncovered == True:
				#uncovered a mine
				self.lost_game = True
				return
			self.simplify_constraints()
		mines_left = self.ms.num_mines - self.num_mines_flagged
		if len(self.ms.moves) > 0 and mines_left > 0:
			#time to do backtracking search to pick squares to uncover
			self.search()
		mines_left = self.ms.num_mines - self.num_mines_flagged
		#corner edge case - check if last mine is surrounded by other mines
		if mines_left:
			squares_left = list(set(self.ms.board_coordinates) - self.ms.marked_squares)
			if squares_left:
				if len(squares_left) == mines_left:
					for sq in squares_left:
						self.mark_square_as_mine(sq)
		else:
			#if there are still uncovered squares 
			if self.ms.moves:
				for square in self.ms.moves:
					for constraint in square.constraints:
						self.uncover_square(constraint)
		return

	def uncover_square(self,square):
		"""returns True if the uncovered square is a mine"""
		if square in self.probed_squares:
			return
		x,y = square
		self.probed_squares.add(square)
		self.path_uncovered.append((square,'uncovered'))
		current = self.get_current_square(x,y)
		current.uncovered = True
		if current.original_constant == 9:
			#uncovered a mine
			return True
		else:
			self.mark_square_as_safe(square)
			if current.original_constant == 0:
				#keep uncovering adjacent squares until they have non-zero constants
				neighbors = self.ms.get_neighbors(x,y)
				for n in neighbors:
					if n not in self.probed_squares:
						nx,ny = n
						self.uncover_square((nx,ny))
			elif current.original_constant > 0 and current.original_constant < 9:
				#numbered square, add to list of moves
				if current not in self.ms.moves:
					self.ms.moves.append(current)
				return
		return

	def search(self):
		#backtracking for all solutions with the remaining squares
		leftovers = {}
		#make a list of unknown constraints
		for m in self.ms.moves:
			if m.constraints:
				for constraint in m.constraints:
					if constraint not in leftovers:
						leftovers[constraint] = 1
					else:
						leftovers[constraint] += 1
		squares = list(leftovers.keys())
		mines_left = self.ms.num_mines - self.num_mines_flagged
		squares_left = len(squares)
		def backtrack(comb):
			if len(comb) > squares_left:
				return
			elif sum(comb) > mines_left:
				return
			else:	
				for choice in [0,1]:
					comb.append(choice)
					if sum(comb) == mines_left and len(comb) == squares_left:
						valid = self.check_solution_validity(squares,comb)
						if valid:
							#only keep valid solutions
							c = comb.copy()
							solutions.append(c)
					backtrack(comb)
					removed = comb.pop()
				return solutions
		solutions = []
		#backtrack to find solutions if there are fewer mines than squares
		if mines_left < squares_left:
			backtrack([])
		if solutions:
			#check if any squares are safe in all solutions
			square_solution_counts = {}
			for s in range(len(solutions)):
				for sq in range(len(solutions[s])):
					current_square = squares[sq]
					if current_square not in square_solution_counts:
						square_solution_counts[current_square] = solutions[s][sq]
					else:
						square_solution_counts[current_square] += solutions[s][sq]
			added_safe_squares = False
			for square,count in square_solution_counts.items():
				if count == 0:
					added_safe_squares = True
					self.squares_to_probe.append(square)
			if not added_safe_squares:
				#pick a random solution and probe safe squares
				random_solution = random.randint(0,len(solutions)-1)
				comb = solutions[random_solution]
				for square,value in zip(squares,comb):
					if value == 0:
						#currently just adding all squares marked as safe in the first solution in list
						self.squares_to_probe.append(square)
			
		else:
			#no solutions, so pick a random square
			squares_left = list(set(self.ms.board_coordinates) - self.ms.marked_squares)
			random_square = random.randint(0,len(squares_left)-1)
			next_square = squares_left[random_square]
			self.squares_to_probe.append(next_square)
		self.start_game()
		return

	def meets_constraints(self,variable,val):
		"""sets the variable to the value {0,1} and checks to see if it violates constraints"""
		x,y = variable
		square = self.get_current_square(x,y)
		square.val = val
		neighbors = self.ms.get_neighbors(x,y)
		for n in neighbors:
			nx,ny = n
			neighbor_square = self.get_current_square(nx,ny)
			neighbor_constant = neighbor_square.original_constant
			#only look at neighbors that are uncovered and aren't mines
			if neighbor_square.val is not None and neighbor_square.val != 1:
				mines,safe,unknown = self.get_neighbor_count((nx,ny))
				if mines > neighbor_constant:
					#violation: too many mines
					return False
				elif (neighbor_constant - mines) > unknown:
					#violation: not enough mines
					return False
		return True

	def get_neighbor_count(self,variable):
		"""
		return count of mines, safe squares and unknown squares around the variable
		"""
		nx,ny = variable
		#get its neighbors
		nbors = self.ms.get_neighbors(nx,ny)
		mine_count = 0
		unknown_count = 0
		safe_count = 0
		for nb in nbors:
			nbx,nby = nb
			nbor_square = self.get_current_square(nbx,nby)
			#TODO - need to take into account unknowns
			if nbor_square.val == 1:
				mine_count += 1
			elif nbor_square.val == 0:
				safe_count += 1
			elif not nbor_square.val:
				unknown_count += 1
		return mine_count,safe_count,unknown_count

	def check_solution_validity(self,squares,comb):
		"""check each solution from backtracking to make sure they don't violate constraints"""
		all_valid = False
		for square,value in zip(squares,comb):
			all_valid = self.meets_constraints(square,value)
		#after checking validity, set the square's val back to None
		for square in squares:
			x,y = square
			sq = self.get_current_square(x,y)
			sq.val = None
		return all_valid

	def simplify(self,c1,c2):
		if c1 == c2:
			return
		to_remove = set()
		c1_constraints = set(c1.constraints)
		c2_constraints = set(c2.constraints)
		if c1_constraints and c2_constraints:
			if c1_constraints.issubset(c2_constraints):
				c2.constraints = list(c2_constraints - c1_constraints)
				c2.constant -= c1.constant
				if c2.constant == 0 and len(c2.constraints) > 0:
					#constraints are safe/can be uncovered
					while c2.constraints:
						c = c2.constraints.pop()
						if c not in self.squares_to_probe and c not in self.probed_squares:
							self.squares_to_probe.append(c)
					to_remove.add(c2)
				elif c2.constant > 0 and c2.constant == len(c2.constraints):
					while c2.constraints:
						c = c2.constraints.pop()
						self.mark_square_as_mine(c)
					to_remove.add(c2)
				if c1.constant > 0 and c1.constant == len(c1.constraints):
					while c1.constraints:
						c = c1.constraints.pop()
						self.mark_square_as_mine(c)
					to_remove.add(c1)

				return to_remove
			elif c2_constraints.issubset(c1_constraints):
				return self.simplify(c2,c1)

	def simplify_constraints(self):
		constraints_to_remove = set()
		for move in self.ms.moves:
			if len(move.constraints) == move.constant:
				#leftover constraints are mines
				while move.constraints:
					square = move.constraints.pop()
					self.mark_square_as_mine(square)
				constraints_to_remove.add(move)
			elif move.constant == 0:
				#if there are constraints left, they are safe squares
				while move.constraints:
					square = move.constraints.pop()
					self.squares_to_probe.append(square)
				constraints_to_remove.add(move)
		#remove any Squares that constraints have been satisfied
		for m in constraints_to_remove:
			self.ms.moves.remove(m)
		
		#now look at pairs of constraints to reduce subsets
		constraints_to_remove = set()
		if len(self.ms.moves) > 1:
			i = 0
			j = i+1
			while i < len(self.ms.moves):
				while j < len(self.ms.moves):
					c1 = self.ms.moves[i]
					c2 = self.ms.moves[j]
					to_remove = self.simplify(c1,c2)
					if to_remove:
						constraints_to_remove.update(to_remove)
					j += 1
				i += 1
				j = i+1
		for m in constraints_to_remove:
			self.ms.moves.remove(m)
		return

	def mark_square_as_safe(self,square):
		self.mark_square(square)
		return

	def mark_square_as_mine(self,square):
		self.path_uncovered.append((square,'flagged'))
		self.num_mines_flagged += 1
		self.ms.mines_flagged.add(square)
		self.mark_square(square,is_mine=True)
		return

	def mark_square(self,square,is_mine=False):
		"""update neighbors of known mine or safe square"""
		x,y = square
		if (x,y) not in self.marked_count:
			self.marked_count[(x,y)] = 1
		else:
			self.marked_count[(x,y)] += 1
		self.ms.marked_squares.add(square)
		current_square = self.get_current_square(x,y)
		if current_square.val is not None:
			#square already marked
			return
		else:
			if is_mine:
				current_square.val = 1
				current_square.flagged = True
			else:
				current_square.val = 0
			neighbors = self.ms.get_neighbors(x,y)
			#remove known square from adjacent neighbor constraints
			for neighbor in neighbors:
				nx,ny = neighbor
				neighbor_square = self.get_current_square(nx,ny)
				if (x,y) in neighbor_square.constraints:
					neighbor_square.constraints.remove(square)
					if is_mine:
						#if square is a mine, decrement neighbors constants
						neighbor_square.constant -= 1
		return

	def get_current_square(self,x,y):
		"""return Square object at (x,y) in board"""
		return self.board[x][y]


