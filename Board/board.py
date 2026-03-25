import json
import random
from pathlib import Path
from .cells import ClueCell, LetterCell, Run
from Utils.bitarray import BitArray, bitArrayStack, HEBREW_ALPHABET, LETTER_TO_INDEX, MIN_LENGTH, MAX_LENGTH

class Board:

	def __init__(self, width, height):

		self.width = width
		self.height = height

		self.grid = [
			[LetterCell(self.width - x - 1, y) for x in range(width)]
			for y in range(height)
		]

		self.runs = None
		self.bit_arrays = None
		self.bit_arrays_sizes = None
		self.words_by_length = None
		self.word_to_index_by_length = None
		self.assigned_words = None


	# -------------------------------------------------
	# BASIC ACCESS
	# -------------------------------------------------

	def get_cell(self, x, y):
		return self.grid[y][self.width - 1 - x]


	def set_cell(self, x, y, cell):
		self.grid[y][self.width - 1 - x] = cell


	def reset_generation_state(self):
		# Rebuild board cells so every generation attempt starts from a clean slate.
		self.grid = [
			[LetterCell(self.width - x - 1, y) for x in range(self.width)]
			for y in range(self.height)
		]
		self.runs = None
		if self.assigned_words is not None:
			self.assigned_words = {i: set() for i in range(MIN_LENGTH, MAX_LENGTH + 1)}


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
		
		run.update_length(new_len)
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
		
		run.update_length(new_len)
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

			self.apply_transfer_if_valid(ax, ay, bx, by)


	# -------------------------------------------------
	# SKELETON GENERATION
	# -------------------------------------------------

	# Select one of 3 possibilities for the top right corner:
	#  ?? | _? | _?
	#  __ | _? | __
	def top_right_corner_skeleton(self):
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


	# Assign clue cells in rightmost column
	# Each row must contain a clue defining its run. It can be defined by one of three cells:
	# 1. The rightmost cell in the row above (not always possible)
	# 2. The rightmost cell in the row below (not always possible)
	# 3. The rightmost cell in the row itself (always possible)
	def right_column_skeleton(self):
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
				if run_len >= 2:
					run = Run("U", 0, y, run_len, "H")
					self.assign_run(run, "H")


			elif choice == 2:

				self.set_cell(0, y + 1, ClueCell(0, y + 1))
				run_len = self.calc_potential_run_length(1, y + 1, "H")
				if run_len >= 2:
					run = Run("R", 1, y + 1, run_len, "H")
					self.assign_run(run, "H")
				run_len = self.calc_potential_run_length(0, y, "H")
				if run_len >= 2:
					run = Run("D", 0, y, run_len, "H")
					self.assign_run(run, "H")

			else:

				self.set_cell(0, y, ClueCell(0, y))
				run_len = self.calc_potential_run_length(1, y, "H")
				if run_len >= 2:
					run = Run("R", 1, y, run_len, "H")
					self.assign_run(run, "H")


	# Assign clue cells in top row
	# Each column must contain a clue defining its run. It can be defined by one of three cells:
	# 1. The top cell in the column to the right (not always possible)
	# 2. The top cell in the column to the left (not always possible)
	# 3. The top cell in the column itself (always possible)
	def top_row_skeleton(self):
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
				if run_len >= 2:
					run = Run("R", x, 0, run_len, "V")
					self.assign_run(run, "V")

			elif choice == 2:

				self.set_cell(x + 1, 0, ClueCell(x + 1, 0))
				run_len = self.calc_potential_run_length(x + 1, 1, "V")
				if run_len >= 2:
					run = Run("U", x + 1, 1, run_len, "V")
					self.assign_run(run, "V")
				run_len = self.calc_potential_run_length(x, 0, "V")
				if run_len >= 2:
					run = Run("L", x, 0, run_len, "V")
					self.assign_run(run, "V")

			else:

				self.set_cell(x, 0, ClueCell(x, 0))
				run_len = self.calc_potential_run_length(x, 1, "V")
				if run_len >= 2:
					run = Run("U", x, 1, run_len, "V")
					self.assign_run(run, "V")


	# Iterate over the rest of the board and assign clue cell with low probability in eligible cells
	# Eligable cells have a 1/6 base probability of being a clue cell, multiplied by 0.5 for each length 1 run it would create
	# If the clue cell would break a run of length greater than MAX_LENGTH, it is assigned with probability 1
	def interior_skeleton(self):	
		coords = [(x, y) for x in range(1, self.width) for y in range(1, self.height)]

		random.shuffle(coords)

		for x, y in coords:

			if self.is_eligible_for_clue_cell(x, y):

				prob = 1 if self.over_max_len_run_broken(x,y) > 0 else (1.0 / 4) * (0.5 ** self.len_1_runs_created(x, y))

				if random.random() < prob:
					
					# If the cell being converted is the start of a run, delete that run
					cell = self.get_cell(x, y)
					if self.is_letter_cell(cell):
						if cell.has_horizontal_start():
							h_run = cell.get_horizontal_run()
							for cx, cy in h_run.cells_coords:
								self.get_cell(cx, cy).delete_horizontal()
							clue = self.get_cell(h_run.clue_x, h_run.clue_y)
							clue.delete_run(h_run)
						
						if cell.has_vertical_start():
							v_run = cell.get_vertical_run()
							for cx, cy in v_run.cells_coords:
								self.get_cell(cx, cy).delete_vertical()
							clue = self.get_cell(v_run.clue_x, v_run.clue_y)
							clue.delete_run(v_run)
					
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

	def generate_skeleton(self):
		self.top_right_corner_skeleton()
		self.right_column_skeleton()
		self.top_row_skeleton()
		self.interior_skeleton()
		self.apply_all_possible_transfers()


	# -------------------------------------------------
	# WORD ASSIGNMENT
	# -------------------------------------------------

	# Load the bit array files from the proccessed dataset and initialize the bit arrays for each word length, position, and letter
	def load_dataset(self, dataset_path):
		self.bit_arrays = []
		self.bit_arrays_sizes = []
		dataset_path = Path(dataset_path)
		alphabet_size = len(HEBREW_ALPHABET)
		self.words_by_length = []
		self.word_to_index_by_length = []
		self.assigned_words = {i: set() for i in range(MIN_LENGTH, MAX_LENGTH + 1)}

		for length in range(MIN_LENGTH, MAX_LENGTH + 1):
			bit_arrays_dict = {}
			length_dir = dataset_path / "processed" / "bitmaps" / f"length_{length}"
			bitmaps_path = length_dir / f"length_{length}.bitmaps"
			metadata_path = length_dir / "metadata.json"
			words_path = length_dir / "words.json"

			with open(bitmaps_path, "rb") as f:
				bit_arrays_file = f.read()

			with open(metadata_path, "r", encoding="utf-8") as f:
				metadata = json.load(f)
				logical_size = metadata["logical_size"]

			with open(words_path, "r", encoding="utf-8") as f:
				words = json.load(f)

			word_to_index = {word: i for i, word in enumerate(words)}

			for pos in range(length):
				for i, letter in enumerate(HEBREW_ALPHABET):
					bitmap_index = i + pos * alphabet_size
					bit_arrays_dict[(pos, letter)] = BitArray(
						bit_arrays_file,
						logical_size,
						bitmap_index
					)

			self.words_by_length.append(words)
			self.word_to_index_by_length.append(word_to_index)

			self.bit_arrays.append(bit_arrays_dict)
			self.bit_arrays_sizes.append(logical_size)

	
	# Initialize possible letters for each cell based on its positions in its runs and the bit arrays for those positions
	def init_cells_possibilities(self):
		self.runs = []
		for y in range(self.height):
			for x in range(self.width):
				cell = self.get_cell(x, y)

				if self.is_letter_cell(cell):

					# initialize runs list
					if cell.has_horizontal_start():
						self.runs.append(cell.get_horizontal_run())
					if cell.has_vertical_start():
						self.runs.append(cell.get_vertical_run())

					# Initialize possible letters for the cell
					cell.possible_letters = bitArrayStack(len(HEBREW_ALPHABET))
					h_run = cell.get_horizontal_run()
					v_run = cell.get_vertical_run()

					h_pos = cell.horizontal_index
					v_pos = cell.vertical_index

					h_bit_arrays_dict = None
					if h_run is not None:
						h_bit_arrays_dict = self.bit_arrays[h_run.length - MIN_LENGTH]

					v_bit_arrays_dict = None
					if v_run is not None:
						v_bit_arrays_dict = self.bit_arrays[v_run.length - MIN_LENGTH]

					for i, letter in enumerate(HEBREW_ALPHABET):
						h_ok = (
							True if h_bit_arrays_dict is None
							else h_bit_arrays_dict[(h_pos, letter)].any()
						)
						v_ok = (
							True if v_bit_arrays_dict is None
							else v_bit_arrays_dict[(v_pos, letter)].any()
						)

						if h_ok and v_ok:
							cell.possible_letters.set(i, 1)


	# Initialize possible words for each run to all possible words of that length
	def init_runs_possibilities(self):
		for run in self.runs:
			logical_size = self.bit_arrays_sizes[run.length - MIN_LENGTH]
			run.possible_words = bitArrayStack(logical_size)
			run.possible_words.set_all(True)


	# Apply letter constraints to possible words for each run based on the possible letters of the cells in the run
	def apply_letter_constraints_to_runs(self):
		changed = False

		for run in self.runs:
			logical_size = self.bit_arrays_sizes[run.length - MIN_LENGTH]
			bit_arrays_dict = self.bit_arrays[run.length - MIN_LENGTH]

			for pos, (x, y) in enumerate(run.cells_coords):
				cell = self.get_cell(x, y)

				pos_bit_array = BitArray(logical_size)

				for i, letter in enumerate(HEBREW_ALPHABET):
					if cell.possible_letters.get(i):
						pos_bit_array |= bit_arrays_dict[(pos, letter)]

				old_possible_words = run.possible_words.top()
				run.possible_words &= pos_bit_array

				if run.possible_words.top() != old_possible_words:
					changed = True
		
		return changed


	# Apply run constraints to possible letters for each cell based on the possible words of the runs the cell belongs to
	def apply_run_constraints_to_cells(self):
		changed = False

		for run in self.runs:
			bit_arrays_dict = self.bit_arrays[run.length - MIN_LENGTH]

			for pos, (x, y) in enumerate(run.cells_coords):
				cell = self.get_cell(x, y)

				letters_supported_by_run = BitArray(len(HEBREW_ALPHABET))

				for i, letter in enumerate(HEBREW_ALPHABET):
					# words in run that have this letter at this pos
					supported_words = run.possible_words & bit_arrays_dict[(pos, letter)]
					if supported_words.any():
						letters_supported_by_run.set(i, 1)

				old_letters = cell.possible_letters.top()
				cell.possible_letters &= letters_supported_by_run

				if cell.possible_letters.top() != old_letters:
					changed = True

		return changed


	# Scan for runs with no possible word and cells with no possible letter, indicating a contradiction
	def scan_for_contradictions(self):
		for run in self.runs:
			if not run.possible_words.any():
				return True

		for y in range(self.height):
			for x in range(self.width):
				cell = self.get_cell(x, y)
				if self.is_letter_cell(cell) and not cell.possible_letters.any():
					return True

		return False
	

	# Scan for runs with only one possible word and assign that word to the run and the corresponding letters to the cells in the run
	def assign_solved_runs(self):
		for run in self.runs:
			if run.possible_words.count_ones() == 1 and run.assigned_word is None:
				word_index = run.possible_words.first_one()
				word = self.words_by_length[run.length - MIN_LENGTH][word_index]

				run.assigned_word = word
				self.assigned_words[run.length].add(word)

				for pos, (x, y) in enumerate(run.cells_coords):
					cell = self.get_cell(x, y)
					letter = word[pos]
					letter_index = LETTER_TO_INDEX[letter]

					cell.possible_letters.set_all(False)
					cell.possible_letters.set(letter_index, True)
					cell.assigned_letter = letter

				return True

		return False


	# Scan for cells with only one possible letter and assign that letter to the cell
	def assign_solved_cells(self):
		changed = False

		for y in range(self.height):
			for x in range(self.width):
				cell = self.get_cell(x, y)

				if not self.is_letter_cell(cell):
					continue

				if cell.assigned_letter is None and cell.possible_letters.count_ones() == 1:
					letter_index = cell.possible_letters.first_one()
					letter = HEBREW_ALPHABET[letter_index]
					cell.assigned_letter = letter
					changed = True

		return changed


	# Revert not certain letter and run assignments
	def unassign_incorrect_assignments(self):
		
		for run in self.runs:
			if run.assigned_word is None:
				continue

			count = run.possible_words.count_ones()
			if count != 1:
				self.assigned_words[run.length].discard(run.assigned_word)
				run.assigned_word = None
				continue

			word_index = run.possible_words.first_one()
			singleton_word = self.words_by_length[run.length - MIN_LENGTH][word_index]
			if run.assigned_word != singleton_word:
				self.assigned_words[run.length].discard(run.assigned_word)
				run.assigned_word = singleton_word
				self.assigned_words[run.length].add(singleton_word)

		for y in range(self.height):
			for x in range(self.width):
				cell = self.get_cell(x, y)
				if not self.is_letter_cell(cell) or cell.assigned_letter is None:
					continue

				count = cell.possible_letters.count_ones()
				if count != 1:
					cell.assigned_letter = None
					continue

				singleton_letter = HEBREW_ALPHABET[cell.possible_letters.first_one()]
				if cell.assigned_letter != singleton_letter:
					cell.assigned_letter = singleton_letter

		return True


	# Remove assigned words from possible words of unassigned runs
	def remove_assigned_words_from_runs(self):
		changed = False

		for run in self.runs:
			if run.assigned_word is not None:
				continue

			for word in self.assigned_words[run.length]:
				word_index = self.word_to_index_by_length[run.length - MIN_LENGTH][word]

				if run.possible_words.get(word_index):
					run.possible_words.set(word_index, 0)
					changed = True

		return changed



	# Check if the board is solved (all runs have an assigned word and all cells have an assigned letter)
	def is_solved(self):
		for run in self.runs:
			if run.assigned_word is None:
				return False

		for y in range(self.height):
			for x in range(self.width):
				cell = self.get_cell(x, y)
				if self.is_letter_cell(cell) and cell.assigned_letter is None:
					return False

		return True

	# Propagate constraints until no more can be propagated, or a contradiction is found
	def propagate_constraints(self):
		while True:
			changed = False

			changed |= self.remove_assigned_words_from_runs()
			changed |= self.apply_letter_constraints_to_runs()
			changed |= self.apply_run_constraints_to_cells()
			changed |= self.assign_solved_cells()
			changed |= self.assign_solved_runs()

			if self.scan_for_contradictions():
				return False

			if not changed:
				return True


	def find_cell_guess(self):
		most_constrained_run = None
		min_possible_words = float("inf")

		for run in self.runs:
			if run.assigned_word is not None:
				continue

			count = run.possible_words.count_ones()

			if count <= 1:
				continue

			if count < min_possible_words:
				min_possible_words = count
				most_constrained_run = run

		if most_constrained_run is None:
			return None, None

		best_pos = None
		best_letter_index = None
		max_score = -1

		run_len_bit_arrays = self.bit_arrays[most_constrained_run.length - MIN_LENGTH]

		for pos, (x, y) in enumerate(most_constrained_run.cells_coords):
			cell = self.get_cell(x, y)

			if cell.assigned_letter is not None:
				continue

			if most_constrained_run.direction == "H":
				perpendicular_run = cell.get_vertical_run()
				perpendicular_pos = cell.vertical_index
			else:
				perpendicular_run = cell.get_horizontal_run()
				perpendicular_pos = cell.horizontal_index

			for i, letter in enumerate(HEBREW_ALPHABET):
				if not cell.possible_letters.get(i):
					continue

				main_count = (
					most_constrained_run.possible_words
					& run_len_bit_arrays[(pos, letter)]
				).count_ones()

				if perpendicular_run is not None:
					perp_bit_arrays = self.bit_arrays[perpendicular_run.length - MIN_LENGTH]
					perpendicular_count = (
						perpendicular_run.possible_words
						& perp_bit_arrays[(perpendicular_pos, letter)]
					).count_ones()
				else:
					perpendicular_count = 1

				score = main_count * perpendicular_count

				if score > max_score:
					max_score = score
					best_pos = pos
					best_letter_index = i

		constraint_bitmap = BitArray(len(HEBREW_ALPHABET))
		constraint_bitmap.set(best_letter_index, 1)
		return most_constrained_run.cells_coords[best_pos], constraint_bitmap


	# Save board state and apply constraint to a cell
	def apply_constraint(self, x, y, bitmap):
		for run in self.runs:
			run.possible_words.copy_head()
		for cell in self.grid:
			if self.is_letter_cell(cell):
				cell.possible_letters.copy_head()
		cell = self.get_cell(x, y)
		cell.possible_letters &= bitmap
	

	# Restore previous board state by popping the head of the bit array stacks.
	# Remove assigned words and letters from unsolved runs and cells.
	def restore_state(self):
		for run in self.runs:
			run.possible_words.pop()
		for cell in self.grid:
			if self.is_letter_cell(cell):
				cell.possible_letters.pop()
				
		self.unassign_incorrect_assignments()


	# Repeat this loop until solved or a contradiction is found:
	# 1. Propagate constraints until no more can be propagated, or a contradiction is found
	# 2. If solved, return True
	# 3. Otherwise, select a cell and letter to guess based on the most constrained run and the bit arrays
	# 4. Assign the guessed letter and recurse. if leads to contradiction, flip guess and recurse.
	def solve(self):
		# If returns false, found contradiction
		if not self.propagate_constraints():
			return False

		# Check if solved
		if self.is_solved():
			return True

		guess_cell_coords, bit_array = self.find_cell_guess()
		if guess_cell_coords is None or bit_array is None:
			return False
		x, y = guess_cell_coords

		# Apply guess and recurse
		self.apply_constraint(x, y, bit_array)
		if self.solve():
			return True

		# Guess was wrong, flip and recurse
		bit_array = ~bit_array
		self.restore_state()
		self.apply_constraint(x, y, bit_array)
		if self.solve():
			return True

		# Restore failed second-branch guess before unwinding.
		self.restore_state()
		return False

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


	def _collect_assigned_letters(self, x, y, dx, dy):
		letters = []
		coords = []

		cx, cy = x, y
		while 0 <= cx < self.width and 0 <= cy < self.height:
			cell = self.get_cell(cx, cy)
			if not self.is_letter_cell(cell):
				break
			if cell.assigned_letter is None:
				break
			letters.append(cell.assigned_letter)
			coords.append((cx, cy))
			cx += dx
			cy += dy

		return letters, coords


	def _debug_side_run_info(self, coords, axis):
		info = []
		for x, y in coords:
			cell = self.get_cell(x, y)
			if not self.is_letter_cell(cell):
				info.append(f"({x},{y}):not-letter")
				continue

			if axis == "H":
				run = cell.get_horizontal_run()
				idx = cell.horizontal_index
			else:
				run = cell.get_vertical_run()
				idx = cell.vertical_index

			if run is None:
				info.append(f"({x},{y}):no-{axis}-run")
			else:
				info.append(
					f"({x},{y}):start=({run.start_x},{run.start_y})"
					f" clue=({run.clue_x},{run.clue_y}) idx={idx} len={run.length}"
				)

		return info


	def debug_detect_words_crossing_clues(self):
		if self.words_by_length is None:
			print("[RUN-DEBUG][cross-clue] skipped: words_by_length not loaded")
			return

		# Ignore very short matches like 2-letter words, which are often incidental.
		min_report_len = 4

		word_sets_by_len = {
			length: set(self.words_by_length[length - MIN_LENGTH])
			for length in range(MIN_LENGTH, MAX_LENGTH + 1)
		}

		hits = 0

		for y in range(self.height):
			for x in range(self.width):
				if not self.is_clue_cell(x, y):
					continue

				# Horizontal: check both concatenation orders so RTL/LTR display cannot hide issues.
				left_letters, left_coords = self._collect_assigned_letters(x - 1, y, -1, 0)
				right_letters, right_coords = self._collect_assigned_letters(x + 1, y, 1, 0)

				if left_letters and right_letters:
					cand_1 = "".join(reversed(left_letters)) + "".join(right_letters)
					cand_2 = "".join(reversed(right_letters)) + "".join(left_letters)

					for axis, cand, c1, c2 in (
						("H", cand_1, list(reversed(left_coords)), right_coords),
						("H", cand_2, list(reversed(right_coords)), left_coords),
					):
						l = len(cand)
						if l >= min_report_len and l <= MAX_LENGTH and cand in word_sets_by_len[l]:
							hits += 1
							side_a_info = self._debug_side_run_info(c1, "H")
							side_b_info = self._debug_side_run_info(c2, "H")
							print(
								f"[RUN-DEBUG][cross-clue] dictionary word spans clue: "
								f"word={cand} axis={axis} clue=({x},{y}) "
								f"side_a={c1} side_b={c2} "
								f"side_a_runs={side_a_info} side_b_runs={side_b_info}"
							)

				# Vertical: check both concatenation orders.
				up_letters, up_coords = self._collect_assigned_letters(x, y - 1, 0, -1)
				down_letters, down_coords = self._collect_assigned_letters(x, y + 1, 0, 1)

				if up_letters and down_letters:
					cand_1 = "".join(reversed(up_letters)) + "".join(down_letters)
					cand_2 = "".join(reversed(down_letters)) + "".join(up_letters)

					for axis, cand, c1, c2 in (
						("V", cand_1, list(reversed(up_coords)), down_coords),
						("V", cand_2, list(reversed(down_coords)), up_coords),
					):
						l = len(cand)
						if l >= min_report_len and l <= MAX_LENGTH and cand in word_sets_by_len[l]:
							hits += 1
							side_a_info = self._debug_side_run_info(c1, "V")
							side_b_info = self._debug_side_run_info(c2, "V")
							print(
								f"[RUN-DEBUG][cross-clue] dictionary word spans clue: "
								f"word={cand} axis={axis} clue=({x},{y}) "
								f"side_a={c1} side_b={c2} "
								f"side_a_runs={side_a_info} side_b_runs={side_b_info}"
							)

		if hits == 0:
			print("[RUN-DEBUG][cross-clue] no dictionary words detected across clue cells")
	

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
