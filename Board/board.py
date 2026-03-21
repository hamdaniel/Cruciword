import random
from .cells import ClueCell, LetterCell, RunStart

MAX_RUN_LENGTH = 15

class Board:

	def __init__(self, width, height):

		self.width = width
		self.height = height

		self.grid = [
			[LetterCell() for _ in range(width)]
			for _ in range(height)
		]

	# -------------------------------------------------
	# BASIC ACCESS
	# -------------------------------------------------

	def get_cell(self, x, y):
		return self.grid[y][self.width - 1 - x]


	def set_cell(self, x, y, cell):
		self.grid[y][self.width - 1 - x] = cell


	def is_clue_cell(self, x, y=None):

		if y is None:
			return isinstance(x, ClueCell)

		return isinstance(self.get_cell(x, y), ClueCell)


	def is_letter_cell(self, x, y=None):

		if y is None:
			return isinstance(x, LetterCell)

		return isinstance(self.get_cell(x, y), LetterCell)


	# -------------------------------------------------
	# RUN CALCULATIONS
	# -------------------------------------------------

	def calc_run_length(self, x, y, direction):

		if self.is_clue_cell(x, y):
			return 0

		length = 0

		if direction == "L":

			for i in range(x, self.width):

				if self.is_clue_cell(i, y):
					break

				length += 1

		elif direction == "D":

			for j in range(y, self.height):

				if self.is_clue_cell(x, j):
					break

				length += 1

		return length

	# -------------------------------------------------
	# CLUE OWNERSHIP
	# -------------------------------------------------

	def num_clues(self, x, y):
		if not self.is_clue_cell(x, y):
			return 0

		count = 0

		# U neighbor: only left-going run, owned by clue below it
		if y > 0:
			c = self.get_cell(x, y - 1)
			if self.is_letter_cell(c) and c.has_horizontal_start() and c.horizontal_run.origin == "D":
				count += 1

		# D neighbor: may have left-going or down-going runs, both can belong to clue above
		if y < self.height - 1:
			c = self.get_cell(x, y + 1)
			if self.is_letter_cell(c):
				if (c.has_horizontal_start() and c.horizontal_run.origin == "U") \
				or (c.has_vertical_start() and c.vertical_run.origin == "U"):
					count += 1

		# L neighbor: may have left-going or down-going runs, both can belong to clue right
		if x < self.width - 1:
			c = self.get_cell(x + 1, y)
			if self.is_letter_cell(c):
				if (c.has_horizontal_start() and c.horizontal_run.origin == "R") \
				or (c.has_vertical_start() and c.vertical_run.origin == "R"):
					count += 1

		# R neighbor: only down-going run, owned by clue left
		if x > 0:
			c = self.get_cell(x - 1, y)
			if self.is_letter_cell(c) and c.has_vertical_start() and c.vertical_run.origin == "L":
				count += 1

		return count

	def find_clue_origin(self, x, y, direction):

		if direction == "U":
			return (x, y - 1)

		if direction == "D":
			return (x, y + 1)

		if direction == "L":
			return (x + 1, y)

		if direction == "R":
			return (x - 1, y)

		return None

	# -------------------------------------------------
	# RUN LENGTH MAINTENANCE
	# -------------------------------------------------

	def update_left_run_lengths_to_the_right(self, x, y):

		i = x - 1

		while i >= 0:

			cell = self.get_cell(i, y)

			if isinstance(cell, ClueCell):
				break

			if self.is_letter_cell(cell) and cell.has_horizontal_start():

				new_len = self.calc_run_length(i, y, "L")

				if new_len >= 2:
					cell.horizontal_run.length = new_len
				else:
					cell.clear_horizontal()

				break

			i -= 1

	def update_down_run_lengths_above(self, x, y):

		j = y - 1

		while j >= 0:

			cell = self.get_cell(x, j)

			if isinstance(cell, ClueCell):
				break

			if self.is_letter_cell(cell) and cell.has_vertical_start():

				new_len = self.calc_run_length(x, j, "D")

				if new_len >= 2:
					cell.vertical_run.length = new_len
				else:
					cell.clear_vertical()

				break

			j -= 1


	# -------------------------------------------------
	# CLUE CELL CREATION
	# -------------------------------------------------
	def is_eligible_for_clue_cell(self, x, y):

		if self.is_clue_cell(x, y):
			return False

		# --------------------------------
		# check cell above
		# --------------------------------

		if y > 0:

			above = self.get_cell(x, y - 1)

			if self.is_letter_cell(above) and above.has_vertical_start():

				clue = self.find_clue_origin(x, y - 1, above.vertical_run.origin)

				# Check if clue above belongs to a clue cell with no other clues
				if clue and self.num_clues(*clue) == 1:
					return False

				# Check if the cell above has no other run
				i = x
				found_left_start = False

				while i >= 0:

					c = self.get_cell(i, y - 1)

					if isinstance(c, ClueCell):
						break

					if self.is_letter_cell(c) and c.has_horizontal_start():
						found_left_start = True
						break

					i -= 1

				if not found_left_start:
					return False

			# Check if the cell above is a clue cell with no other clues
			if self.is_clue_cell(x, y - 1):

				if self.num_clues(x, y - 1) == 1:
					return False

		# --------------------------------
		# check cell right
		# --------------------------------

		if x > 0:

			right = self.get_cell(x - 1, y)

			if self.is_letter_cell(right) and right.has_horizontal_start():

				clue = self.find_clue_origin(x - 1, y, right.horizontal_run.origin)

				# Check if clue to the right belongs to a clue cell with no other clues
				if clue and self.num_clues(*clue) == 1:
					return False

				# Check if the cell to the right has no other run
				j = y
				found_up_start = False

				while j >= 0:

					c = self.get_cell(x - 1, j)

					if isinstance(c, ClueCell):
						break

					if self.is_letter_cell(c) and c.has_vertical_start():
						found_up_start = True
						break

					j -= 1

				if not found_up_start:
					return False

			# Check if the cell to the right is a clue cell with no other clues
			if self.is_clue_cell(x - 1, y):

				if self.num_clues(x - 1, y) == 1:
					return False

		# --------------------------------
		# check resulting run lengths
		# --------------------------------

		left_run = 0
		down_run = 0

		if x < self.width - 1:
			left_run = self.calc_run_length(x + 1, y, "L")

		if y < self.height - 1:
			down_run = self.calc_run_length(x, y + 1, "D")

		if left_run < 2 and down_run < 2:
			return False

		return True


	def len_1_runs_created(self, x, y):

		count = 0

		if y > 0:

			c = self.get_cell(x, y - 1)

			if self.is_letter_cell(c) and c.has_vertical_start():
				count += 1

		if x > 0:

			c = self.get_cell(x - 1, y)

			if self.is_letter_cell(c) and c.has_horizontal_start():
				count += 1

		left_run = 0
		down_run = 0

		if x < self.width - 1:
			left_run = self.calc_run_length(x + 1, y, "L")

		if y < self.height - 1:
			down_run = self.calc_run_length(x, y + 1, "D")

		if left_run == 1:
			count += 1

		if down_run == 1:
			count += 1

		return count
	

	def over_max_len_run_broken(self, x, y):

		count = 0

		left_run = 0
		down_run = 0
		right_run = 0
		up_run = 0

		while x - right_run - 1 > 0 and not self.is_clue_cell(x - right_run - 1, y):
			right_run += 1

		while y - up_run - 1 > 0 and not self.is_clue_cell(x, y - up_run - 1):
			up_run += 1

		if x < self.width - 1:
			left_run = self.calc_run_length(x + 1, y, "L")

		if y < self.height - 1:
			down_run = self.calc_run_length(x, y + 1, "D")

		if left_run + right_run + 1 > MAX_RUN_LENGTH:
			count += 1

		if down_run + up_run + 1 > MAX_RUN_LENGTH:
			count += 1

		return count


	# -------------------------------------------------
	# TRANSFER LOGIC
	# -------------------------------------------------

	# Clues can be transfered from clue cells A&B that satisfy the following:
	# 1. A is a clue cell with two clues
	# 2. B is a clue cell with one clue
	# 3. A&B are diagonally adjacent, with A being above and/or to the right of B (not adjacency type DL)
	# 4. At least one of the two cells that touch A&B satisfies the following:
	# 	a. It has no clue from B
	# 	b. It has a clue from A that is either:
	#		i. A vertical and originating from the right
	#		ii. A horizontal and originating from above

	def clue_start_cells_of_clue(self, x, y):

		if not self.is_clue_cell(x, y):
			return []

		starts = []

		if x > 0:
			c = self.get_cell(x - 1, y)
			if self.is_letter_cell(c) and c.has_vertical_start() and c.vertical_run.origin == "L":
				starts.append((x - 1, y, c))

		if x < self.width - 1:
			c = self.get_cell(x + 1, y)
			if self.is_letter_cell(c):
				if (c.has_horizontal_start() and c.horizontal_run.origin == "R") \
				or (c.has_vertical_start() and c.vertical_run.origin == "R"):
					starts.append((x + 1, y, c))

		if y > 0:
			c = self.get_cell(x, y - 1)
			if self.is_letter_cell(c) and c.has_horizontal_start() and c.horizontal_run.origin == "D":
					starts.append((x, y - 1, c))

		if y < self.height - 1:
			c = self.get_cell(x, y + 1)
			if self.is_letter_cell(c):
				if (c.has_horizontal_start() and c.horizontal_run.origin == "U") \
				or (c.has_vertical_start() and c.vertical_run.origin == "U"):
					starts.append((x, y + 1, c))

		return starts
	
	# Determine the diagonal adjacency type of B from A, if any
	# Returns one of "UR", "DR", "UL", "DL", or None
	def diagonal_adjacency(self, ax, ay, bx, by):
		if not ( abs(ax - bx) == 1 and abs(ay - by) == 1):
			return None
		if ax < bx and ay < by:
			return "UR"
		if ax < bx and ay > by:
			return "DR"
		if ax > bx and ay < by:
			return "UL"
		if ax > bx and ay > by:
			return "DL"

	
	def collect_diagonal_clue_cells(self):

		pairs = []

		for y in range(self.height):

			for x in range(self.width):

				if not self.is_clue_cell(x, y):
					continue

				for dx in (-1, 1):

					for dy in (-1, 1):

						nx = x + dx
						ny = y + dy

						if (
							0 <= nx < self.width
							and 0 <= ny < self.height
							and self.is_clue_cell(nx, ny)
						):
							pairs.append((x, y, nx, ny))

		return pairs


	def apply_transfer_if_valid(self, ax, ay, bx, by):

		adjacency = self.diagonal_adjacency(ax, ay, bx, by)

		# Can't transfer from A to B if A is below and to the left of B
		if adjacency is None or adjacency == "DL":
			return False
		
		if self.num_clues(ax, ay) != 2 or self.num_clues(bx, by) != 1:
			return False
		
		b_clues = self.clue_start_cells_of_clue(bx, by)
		if len(b_clues) != 1:
			return False
		b_clue = b_clues[0]
				
		
		if 'R' in adjacency:
			aybx = self.get_cell(bx, ay)
			if self.is_letter_cell(aybx):
				if (aybx.has_horizontal_start() and aybx.horizontal_run.origin == "R") \
				and b_clue[2] != aybx:
					aybx.horizontal_run.origin = 'U' if adjacency[0] == 'D' else 'D'
					return True
				
		if 'U' in adjacency:
			axby = self.get_cell(ax, by)
			if self.is_letter_cell(axby):
				if (axby.has_vertical_start() and axby.vertical_run.origin == "U") \
				and b_clue[2] != axby:
					axby.vertical_run.origin = 'L' if adjacency[1] == 'R' else 'R'
					return True
		
		return False


	def apply_all_possible_transfers(self):

		pairs = self.collect_diagonal_clue_cells()

		random.shuffle(pairs)

		moved = 0

		for ax, ay, bx, by in pairs:

			if self.apply_transfer_if_valid(ax, ay, bx, by):

				print(
					f"Transferred clue from ({ax},{ay}) to ({bx},{by})"
				)

				moved += 1

		return moved


	def generate_template(self):

		# -------------------------------------------------
		# Top-right corner initialization
		# -------------------------------------------------

		# Select one of 3 possibilities for the top right corner:
		#  ?? | _? | _?
		#  __ | _? | __
		choice = random.choice([1, 2, 3])

		if choice == 1:

			self.set_cell(0, 0, ClueCell())

			run_len = self.calc_run_length(0, 1, "L")
			cell = self.get_cell(0, 1)
			cell.horizontal_run = RunStart("U", run_len)

			self.set_cell(1, 0, ClueCell())

			run_len = self.calc_run_length(1, 1, "D")
			cell = self.get_cell(1, 1)
			cell.vertical_run = RunStart("U", run_len)

		elif choice == 2:

			self.set_cell(0, 0, ClueCell())

			run_len = self.calc_run_length(1, 0, "D")
			cell = self.get_cell(1, 0)
			cell.vertical_run = RunStart("R", run_len)

			self.set_cell(0, 1, ClueCell())

			run_len = self.calc_run_length(1, 1, "L")
			cell = self.get_cell(1, 1)
			cell.horizontal_run = RunStart("R", run_len)

		else:

			self.set_cell(0, 0, ClueCell())

			run_len = self.calc_run_length(1, 0, "D")
			cell = self.get_cell(1, 0)
			cell.vertical_run = RunStart("R", run_len)

			run_len = self.calc_run_length(0, 1, "L")
			cell = self.get_cell(0, 1)
			cell.horizontal_run = RunStart("U", run_len)

		# -------------------------------------------------
		# Right column clues
		# -------------------------------------------------

		# Assign clue cells in rightmost column
		# Each row must contain a clue defining its run. It can be defined by one of three cells:
		# 1. The rightmost cell in the row above (not always possible)
		# 2. The rightmost cell in the row below (not always possible)
		# 3. The rightmost cell in the row itself (always possible)
		for y in range(2, self.height):

			if self.is_clue_cell(0, y):
				continue

			legal = [3]

			# There is a clue cell above that has only one clue
			if y > 0 and self.num_clues(0, y - 1) == 1:
				legal.append(1)

			# There is a cell below and the cell above is a clue cell
			if y < self.height - 1 and self.is_clue_cell(0, y - 1):
				legal.append(2)

			choice = random.choice(legal)

			if choice == 1:

				run = self.calc_run_length(0, y, "L")
				cell = self.get_cell(0, y)
				cell.horizontal_run = RunStart("U", run)

			elif choice == 2:

				self.set_cell(0, y + 1, ClueCell())

				run = self.calc_run_length(1, y + 1, "L")
				cell = self.get_cell(1, y + 1)
				cell.horizontal_run = RunStart("R", run)

				run = self.calc_run_length(0, y, "L")
				cell = self.get_cell(0, y)
				cell.horizontal_run = RunStart("D", run)

			else:

				self.set_cell(0, y, ClueCell())

				run = self.calc_run_length(1, y, "L")
				cell = self.get_cell(1, y)
				cell.horizontal_run = RunStart("R", run)

		# -------------------------------------------------
		# Top row clues
		# -------------------------------------------------

		# Assign clue cells in top row
		# Each column must contain a clue defining its run. It can be defined by one of three cells:
		# 1. The top cell in the column to the right (not always possible)
		# 2. The top cell in the column to the left (not always possible)
		# 3. The top cell in the column itself (always possible)
		for x in range(2, self.width):

			if self.is_clue_cell(x, 0):
				continue

			legal = [3]

			if x > 0 and self.num_clues(x - 1, 0) == 1:
				legal.append(1)

			if x < self.width - 1 and self.is_clue_cell(x - 1, 0):
				legal.append(2)

			choice = random.choice(legal)

			if choice == 1:

				run = self.calc_run_length(x, 0, "D")
				cell = self.get_cell(x, 0)
				cell.vertical_run = RunStart("R", run)

			elif choice == 2:

				self.set_cell(x + 1, 0, ClueCell())

				run = self.calc_run_length(x + 1, 1, "D")
				cell = self.get_cell(x + 1, 1)
				cell.vertical_run = RunStart("U", run)

				run = self.calc_run_length(x, 0, "D")
				cell = self.get_cell(x, 0)
				cell.vertical_run = RunStart("L", run)

			else:

				self.set_cell(x, 0, ClueCell())

				run = self.calc_run_length(x, 1, "D")
				cell = self.get_cell(x, 1)
				cell.vertical_run = RunStart("U", run)

		# -------------------------------------------------
		# Random interior clues
		# -------------------------------------------------

		# Iterate over the rest of the board and assign clue cell with low probability in eligible cells
		# Eligable cells have a 1/6 base probability of being a clue cell, multiplied by 0.5 for each length 1 run it would create
		# If the clue cell would break a run of length greater than MAX_RUN_LENGTH, it is assigned with probability 1
		coords = [(x, y) for x in range(1, self.width) for y in range(1, self.height)]

		random.shuffle(coords)

		for x, y in coords:

			if self.is_eligible_for_clue_cell(x, y):

				prob = 1 if self.over_max_len_run_broken(x,y) > 0 else (1.0 / 6) * (0.5 ** self.len_1_runs_created(x, y))

				if random.random() < prob:

					self.set_cell(x, y, ClueCell())

					left_run = 0
					down_run = 0

					if x < self.width - 1:
						left_run = self.calc_run_length(x + 1, y, "L")

					if y < self.height - 1:
						down_run = self.calc_run_length(x, y + 1, "D")

					if left_run >= 2:
						cell = self.get_cell(x + 1, y)
						cell.horizontal_run = RunStart("R", left_run)

					if down_run >= 2:
						cell = self.get_cell(x, y + 1)
						cell.vertical_run = RunStart("U", down_run)

					self.update_left_run_lengths_to_the_right(x, y)
					self.update_down_run_lengths_above(x, y)

		self.apply_all_possible_transfers()


	# -------------------------------------------------
	# PRINTING
	# -------------------------------------------------

	def verbose_print(self):
		cell_w = 8
		horizontal = "+" + "+".join(["-" * cell_w] * self.width) + "+"

		rows = [horizontal]

		for y in range(self.height):
			row_cells = []

			for x in range(self.width - 1, -1, -1):
				row_cells.append(f"{str(self.get_cell(x, y)):^{cell_w}}")

			rows.append("|" + "|".join(row_cells) + "|")
			rows.append(horizontal)

		return "\n".join(rows)

	def __str__(self, cell_w = 7, cell_h = 3):

		horizontal = "+" + "+".join(["-" * cell_w] * self.width) + "+"
		rows = [horizontal]

		for y in range(self.height):
			row_cells = [
				self.get_cell(x, y).visualize(cell_w, cell_h)
				for x in range(self.width - 1, -1, -1)
			]

			for i in range(cell_h):
				rows.append("|" + "|".join(cell[i] for cell in row_cells) + "|")

			rows.append(horizontal)

		return "\n".join(rows)
