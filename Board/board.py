import random
from .cells import ClueCell, LetterCell, Run
from Utils.bitarray import BitArray, HEBREW_ALPHABET, MIN_LENGTH, MAX_LENGTH

class Board:

	def __init__(self, width, height):

		self.width = width
		self.height = height

		self.grid = [
			[LetterCell(self.width - x - 1, y) for x in range(width)]
			for y in range(height)
		]

	# -------------------------------------------------
	# BASIC ACCESS
	# -------------------------------------------------

	def get_cell(self, x, y):
		return self.grid[y][self.width - 1 - x]


	def set_cell(self, x, y, cell):
		self.grid[y][self.width - 1 - x] = cell


	def is_clue_cell(self, x, y = None):
		if y is None:
			return isinstance(x, ClueCell)
		
		return isinstance(self.get_cell(x, y), ClueCell)


	def is_letter_cell(self, x, y = None):
		if y is None:
			return isinstance(x, LetterCell)
		
		return isinstance(self.get_cell(x, y), LetterCell)


	# -------------------------------------------------
	# RUN MAINTENANCE
	# -------------------------------------------------

	def assign_run(self, run, dir):
		# Assign the run to all cells in the run
		for x, y in run.cells_coords:
			cell = self.get_cell(x, y)
			if dir == "H":
				cell.set_horizontal_run(run)
			else:
				cell.set_vertical_run(run)
		
		# Assign the run to the clue cell
		clue_cell = self.get_cell(run.clue_x, run.clue_y)
		clue_cell.assign_run(run)


	def calc_potential_run_length(self, x, y, direction):
		length = 0
		
		if direction == "H":

			for i in range(x, self.width):

				if self.is_clue_cell(i, y):
					break

				length += 1

		else: # direction == "V"

			for j in range(y, self.height):

				if self.is_clue_cell(x, j):
					break

				length += 1

		return length
	

	def get_run_length(self, x, y, direction):

		cell = self.get_cell(x, y)

		if not self.is_letter_cell(cell):
			return 0
		
		if direction == "H" and cell.has_horizontal_start() or direction == "V" and cell.has_vertical_start():
			run = cell.get_horizontal_run() if direction == "H" else cell.get_vertical_run()
			return run.length
		
		return 0


	def update_horizontal_run_right(self, x, y):

		# Find the horizontal run the cell to the left belongs to, if any
		if x == 0 or not self.is_letter_cell(x - 1, y) or not self.get_cell(x - 1, y).has_horizontal_run():
			return
		
		run = self.get_cell(x - 1, y).get_horizontal_run()
		# Remove the old horizontal run from all cells in the run
		for cell_x, cell_y in run.cells_coords:
			if cell_x == x and cell_y == y:
				continue

			cell = self.get_cell(cell_x, cell_y)
			cell.delete_horizontal()
		
		# Calculate the new horizontal run length and assign the new run to all cells in the run

		new_len = self.calc_potential_run_length(run.start_x, run.start_y, "H")

		# If the new run length is less than 2, delete the run
		if new_len < 2:
			clue_cell = self.get_cell(run.clue_x, run.clue_y)
			clue_cell.delete_run(run)
			return
		
		run.update_length(new_len, "H")
		self.assign_run(run, "H")



	def update_vertical_run_above(self, x, y):
		# Find the vertical run the cell above belongs to, if any
		if y == 0 or not self.is_letter_cell(x, y - 1) or not self.get_cell(x, y - 1).has_vertical_run():
			return
		
		run = self.get_cell(x, y - 1).get_vertical_run()

		# Remove the old vertical run from all cells in the run
		for cell_x, cell_y in run.cells_coords:
			if cell_x == x and cell_y == y:
				continue

			cell = self.get_cell(cell_x, cell_y)
			cell.delete_vertical()
		
		# Calculate the new vertical run length and assign the new run to all cells in the run

		new_len = self.calc_potential_run_length(run.start_x, run.start_y, "V")

		# If the new run length is less than 2, delete the run
		if new_len < 2:
			clue_cell = self.get_cell(run.clue_x, run.clue_y)
			clue_cell.delete_run(run)
			return
		
		run.update_length(new_len, "V")
		self.assign_run(run, "V")
		

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

			# Check if the placing the clue cell will break the vertical run above.
			# If it does, both the clue sell the run belongs to and the cell above must have another run
			if self.is_letter_cell(above) and above.has_vertical_start():

				clue = self.get_cell(above.get_vertical_run().clue_x, above.get_vertical_run().clue_y)

				# Check if clue above belongs to a clue cell with no other clues
				if self.is_clue_cell(clue) and clue.num_runs() == 1:
					return False

				# Check if the cell above has a horizontal run
				if not above.has_horizontal_run():
					return False

			# Check if the cell above is a clue cell with no other clues
			if self.is_clue_cell(above) and above.num_runs() == 1:
				return False

		# --------------------------------
		# check cell right
		# --------------------------------

		if x > 0:

			right = self.get_cell(x - 1, y)

			# Check if the placing the clue cell will break the vertical run above.
			# If it does, both the clue sell the run belongs to and the cell above must have another run
			if self.is_letter_cell(right) and right.has_horizontal_start():

				clue = self.get_cell(right.get_horizontal_run().clue_x, right.get_horizontal_run().clue_y)

				# Check if clue to the right belongs to a clue cell with no other clues
				if self.is_clue_cell(clue) and clue.num_runs() == 1:
					return False

				# Check if the cell right has a vertical run
				if not right.has_vertical_run():
					return False

			# Check if the cell to the right is a clue cell with no other clues
			if self.is_clue_cell(right) and right.num_runs() == 1:
				return False

		# --------------------------------
		# check resulting run lengths
		# --------------------------------

		left_run = 0
		down_run = 0

		if x < self.width - 1:
			left_run = self.calc_potential_run_length(x + 1, y, "H")

		if y < self.height - 1:
			down_run = self.calc_potential_run_length(x, y + 1, "V")

		# If the clue cell only has runs of length 1, it will be a clue cell with no clues
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
			left_run = self.calc_potential_run_length(x + 1, y, "H")

		if y < self.height - 1:
			down_run = self.calc_potential_run_length(x, y + 1, "V")

		if left_run == 1:
			count += 1

		if down_run == 1:
			count += 1

		return count
	

	def over_max_len_run_broken(self, x, y):

		count = 0
		v_length = 0
		h_length = 0
		if self.is_letter_cell(x, y - 1) and self.get_cell(x, y - 1).has_vertical_run():
			v_length = self.get_cell(x, y - 1).get_vertical_run().length

		if self.is_letter_cell(x - 1, y) and self.get_cell(x - 1, y).has_horizontal_run():
			h_length = self.get_cell(x - 1, y).get_horizontal_run().length

		if v_length > MAX_LENGTH:
			count += 1

		if h_length > MAX_LENGTH:
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
			if self.is_letter_cell(c) and c.has_vertical_start() and c.get_vertical_run().origin_dir == "L":
				starts.append((x - 1, y, c))

		if x < self.width - 1:
			c = self.get_cell(x + 1, y)
			if self.is_letter_cell(c):
				if (c.has_horizontal_start() and c.get_horizontal_run().origin_dir == "R") \
				or (c.has_vertical_start() and c.get_vertical_run().origin_dir == "R"):
					starts.append((x + 1, y, c))

		if y > 0:
			c = self.get_cell(x, y - 1)
			if self.is_letter_cell(c) and c.has_horizontal_start() and c.get_horizontal_run().origin_dir == "D":
					starts.append((x, y - 1, c))

		if y < self.height - 1:
			c = self.get_cell(x, y + 1)
			if self.is_letter_cell(c):
				if (c.has_horizontal_start() and c.get_horizontal_run().origin_dir == "U") \
				or (c.has_vertical_start() and c.get_vertical_run().origin_dir == "U"):
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
		a = self.get_cell(ax, ay)
		b = self.get_cell(bx, by)
		adjacency = self.diagonal_adjacency(ax, ay, bx, by)

		# Can't transfer from A to B if A is below and to the left of B
		if adjacency is None or adjacency == "DL":
			return False
		
		if a.num_runs() != 2 or b.num_runs() != 1:
			return False
		
		b_clues = self.clue_start_cells_of_clue(bx, by)
		if len(b_clues) != 1:
			return False
		b_clue = b_clues[0]
				
		
		if 'R' in adjacency:
			aybx = self.get_cell(bx, ay)
			if self.is_letter_cell(aybx):
				if (aybx.has_horizontal_start() and aybx.get_horizontal_run().origin_dir == "R") \
				and b_clue[2] != aybx:
					aybx.get_horizontal_run().origin_dir = 'U' if adjacency[0] == 'D' else 'D'
					return True
				
		if 'U' in adjacency:
			axby = self.get_cell(ax, by)
			if self.is_letter_cell(axby):
				if (axby.has_vertical_start() and axby.get_vertical_run().origin_dir == "U") \
				and b_clue[2] != axby:
					axby.get_vertical_run().origin_dir = 'L' if adjacency[1] == 'R' else 'R'
					return True
		
		return False


	def apply_all_possible_transfers(self):

		pairs = self.collect_diagonal_clue_cells()

		random.shuffle(pairs)

		moved = 0

		for ax, ay, bx, by in pairs:

			if self.apply_transfer_if_valid(ax, ay, bx, by):

				print(f"Transferred clue from ({ax},{ay}) to ({bx},{by})")

				moved += 1

		return moved


	def generate_skeleton(self):

		# -------------------------------------------------
		# Top-right corner initialization
		# -------------------------------------------------

		# Select one of 3 possibilities for the top right corner:
		#  ?? | _? | _?
		#  __ | _? | __

		self.set_cell(0, 0, ClueCell(0, 0))
		choice = random.choice([1, 2, 3])

		if choice == 1:
			run_len = self.calc_potential_run_length(0, 1, "H")
			run = Run("U", 0, 1, run_len, "H")
			self.assign_run(run, "H")

			self.set_cell(1, 0, ClueCell(1, 0))
			run_len = self.calc_potential_run_length(1, 1, "V")
			run = Run("U", 1, 1, run_len, "V")
			self.assign_run(run, "V")

		elif choice == 2:
			run_len = self.calc_potential_run_length(1, 0, "V")
			run = Run("R", 1, 0, run_len, "V")
			self.assign_run(run, "V")

			self.set_cell(0, 1, ClueCell(0, 1))
			run_len = self.calc_potential_run_length(1, 1, "H")
			run = Run("R", 1, 1, run_len, "H")
			self.assign_run(run, "H")

		else:
			run_len = self.calc_potential_run_length(1, 0, "V")
			run = Run("R", 1, 0, run_len, "V")
			self.assign_run(run, "V")
			run_len = self.calc_potential_run_length(0, 1, "H")
			run = Run("U", 0, 1, run_len, "H")
			self.assign_run(run, "H")

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
			if y > 0 and self.is_clue_cell(0, y - 1) and self.get_cell(0, y - 1).num_runs() == 1:
				legal.append(1)

			# There is a cell below and the cell above is a clue cell
			if y < self.height - 1 and self.is_clue_cell(0, y - 1):
				legal.append(2)

			choice = random.choice(legal)

			if choice == 1:

				run_len = self.calc_potential_run_length(0, y, "H")
				run = Run("U", 0, y, run_len, "H")
				self.assign_run(run, "H")


			elif choice == 2:

				self.set_cell(0, y + 1, ClueCell(0, y + 1))
				run_len = self.calc_potential_run_length(1, y + 1, "H")
				run = Run("R", 1, y + 1, run_len, "H")
				self.assign_run(run, "H")
				run_len = self.calc_potential_run_length(0, y, "H")
				run = Run("D", 0, y, run_len, "H")
				self.assign_run(run, "H")

			else:

				self.set_cell(0, y, ClueCell(0, y))
				run_len = self.calc_potential_run_length(1, y, "H")
				run = Run("R", 1, y, run_len, "H")
				self.assign_run(run, "H")

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

			if x > 0 and self.is_clue_cell(x - 1, 0) and self.get_cell(x - 1, 0).num_runs() == 1:
				legal.append(1)

			if x < self.width - 1 and self.is_clue_cell(x - 1, 0):
				legal.append(2)

			choice = random.choice(legal)

			if choice == 1:

				run_len = self.calc_potential_run_length(x, 0, "V")
				run = Run("R", x, 0, run_len, "V")
				self.assign_run(run, "V")

			elif choice == 2:

				self.set_cell(x + 1, 0, ClueCell(x + 1, 0))
				run_len = self.calc_potential_run_length(x + 1, 1, "V")
				run = Run("U", x + 1, 1, run_len, "V")
				self.assign_run(run, "V")
				run_len = self.calc_potential_run_length(x, 0, "V")
				run = Run("L", x, 0, run_len, "V")
				self.assign_run(run, "V")

			else:

				self.set_cell(x, 0, ClueCell(x, 0))
				run_len = self.calc_potential_run_length(x, 1, "V")
				run = Run("U", x, 1, run_len, "V")
				self.assign_run(run, "V")

		# # -------------------------------------------------
		# # Random interior clues
		# # -------------------------------------------------

		# # Iterate over the rest of the board and assign clue cell with low probability in eligible cells
		# # Eligable cells have a 1/6 base probability of being a clue cell, multiplied by 0.5 for each length 1 run it would create
		# # If the clue cell would break a run of length greater than MAX_LENGTH, it is assigned with probability 1
		coords = [(x, y) for x in range(1, self.width) for y in range(1, self.height)]

		random.shuffle(coords)

		for x, y in coords:

			if self.is_eligible_for_clue_cell(x, y):

				prob = 1 if self.over_max_len_run_broken(x,y) > 0 else (1.0 / 6) * (0.5 ** self.len_1_runs_created(x, y))

				if random.random() < prob:
					
					self.set_cell(x, y, ClueCell(x, y))
					self.update_horizontal_run_right(x, y)
					self.update_vertical_run_above(x, y)

					left_run = 0
					down_run = 0

					if x < self.width - 1:
						left_run = self.calc_potential_run_length(x + 1, y, "H")

					if y < self.height - 1:
						down_run = self.calc_potential_run_length(x, y + 1, "V")

					if left_run >= 2:
						run = Run("R", x + 1, y, left_run, "H")
						self.assign_run(run, "H")

					if down_run >= 2:
						run = Run("U", x, y + 1, down_run, "V")
						self.assign_run(run, "V")


		# self.apply_all_possible_transfers()


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
