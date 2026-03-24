from __future__ import annotations
from Utils.bitarray import BitArray,bitArrayStack, HEBREW_ALPHABET

class Cell:
	"""Abstract base class for all board cells."""
	def __init__(self, x, y):
		self.x = x
		self.y = y


	def visualize(self, width, height):
		output = []
		for _ in range(height):
			output.append(' ' * width)
		return output


class ClueCell(Cell):
	"""Represents a clue cell."""
	def __init__(self, x, y):
		super().__init__(x, y)
		self.run_1 = None
		self.run_2 = None
		

	def visualize(self, width, height):
		output = []
		for _ in range(height // 2):
			output.append(' ' * width)
		output.append(' ' * (width // 2) + "?" + ' ' * (width - width // 2 - 1))
		for _ in range(height - height // 2 - 1):
			output.append(' ' * width)
		return output
	

	def __str__(self):
		return "?"
	

	def assign_run(self, run):
		if run == self.run_1 or run == self.run_2:
			return  # Run is already assigned to this clue cell, do nothing
		if self.run_1 is None:
			self.run_1 = run
		elif self.run_2 is None:
			self.run_2 = run
		else:
			raise ValueError("Clue cell cannot have more than 2 runs.")


	def delete_run(self, run):
		if self.run_1 == run:
			self.run_1 = None
		elif self.run_2 == run:
			self.run_2 = None

	def num_runs(self):
		count = 0
		if self.run_1 is not None:
			count += 1
		if self.run_2 is not None:
			count += 1
		return count

class Run:
	"""
	Represents a run.
	origin_dir: direction of the clue cell relative to the start cell

	length: length of the run
	start_x, start_y: coordinates of the start cell (the first cell in the run)
	cells: list of (x, y) coordinates of the cells in the run, starting with the clue cell and ending with the last letter cell
	"""

	def __init__(self, origin_dir, start_x, start_y, length, dir):
		self.start_x = start_x
		self.start_y = start_y
		self.origin_dir = origin_dir
		self.clue_x = start_x + (0 if origin_dir in ['U', 'D'] else (-1 if origin_dir == 'R' else 1))
		self.clue_y = start_y + (0 if origin_dir in ['L', 'R'] else (-1 if origin_dir == 'U' else 1))
		self.length = length
		self.direction = dir
		self.cells_coords = [(self.start_x + (i if dir == "H" else 0), self.start_y + (i if dir == "V" else 0)) for i in range(0, length)]
		self.possible_words = None
		self.assigned_word = None


	def __repr__(self):
		return f"Run(origin_dir={self.origin_dir}, length={self.length})"
	

	def update_length(self, new_length):
		self.length = new_length
		self.cells_coords = [(self.start_x + (i if self.direction == "H" else 0), self.start_y + (i if self.direction == "V" else 0)) for i in range(0, new_length)]


class LetterCell(Cell):
	"""
	Represents a letter cell.
	It may start a horizontal run, a vertical run, both, or neither.
	"""

	def __init__(self, x, y):
		super().__init__(x, y)
		self.horizontal_run = None
		self.horizontal_index = None
		self.vertical_run = None
		self.vertical_index = None
		self.possible_letters = None
		self.assigned_letter = None


	def get_horizontal_run(self):
		return self.horizontal_run
	

	def has_horizontal_run(self):
		return self.horizontal_run is not None


	def set_horizontal_run(self, run):
		self.horizontal_run = run
		for i, (cell_x, cell_y) in enumerate(run.cells_coords):
			if cell_x == self.x and cell_y == self.y:
				self.horizontal_index = i
				break


	def has_horizontal_start(self):
		return self.has_horizontal_run() and self.horizontal_run.start_x == self.x


	def delete_horizontal(self):
		self.horizontal_run = None


	def get_vertical_run(self):
		return self.vertical_run


	def has_vertical_run(self):
		return self.vertical_run is not None


	def set_vertical_run(self, run):
		self.vertical_run = run
		for i, (cell_x, cell_y) in enumerate(run.cells_coords):
			if cell_x == self.x and cell_y == self.y:
				self.vertical_index = i
				break



	def has_vertical_start(self):
		return self.has_vertical_run() and self.vertical_run.start_y == self.y
	

	def delete_vertical(self):
		self.vertical_run = None


	def has_both_runs(self):
		return self.has_horizontal_run() and self.has_vertical_run()
	

	def has_any_start(self):
		return self.has_horizontal_start() or self.has_vertical_start()


	def __str__(self):
		parts = []

		if self.has_horizontal_start():
			parts.append(f"{self.horizontal_run.origin_dir}H{self.horizontal_run.length}")

		if self.has_vertical_start():
			parts.append(f"{self.vertical_run.origin_dir}V{self.vertical_run.length}")

		return "|".join(parts) if parts else " "
	

	def visualize(self, width, height):
		output = []

		# Top row
		row_1 = [' '] * width

		# UL
		if self.has_horizontal_start() and self.horizontal_run.origin_dir == 'U':
			row_1[width // 2] = '⮠'

		# D
		if self.has_vertical_start() and self.vertical_run.origin_dir == 'U':
			row_1[width // 2] = '↓'

		output.append(''.join(row_1))

		# Rows before middle
		for _ in range(1, height // 2):
			output.append(' ' * width)

		# Middle row
		row_mid = [' '] * width

		# LD
		if self.has_vertical_start() and self.vertical_run.origin_dir == 'L':
			row_mid[0] = '⮧'

		# L
		if self.has_horizontal_start() and self.horizontal_run.origin_dir == 'R':
			row_mid[width - 1] = '←'

		# RD
		if self.has_vertical_start() and self.vertical_run.origin_dir == 'R':
			row_mid[width - 1] = '⮦'

		if self.assigned_letter is not None:
			row_mid[width // 2] = self.assigned_letter
			
		output.append(''.join(row_mid))

		# Rows before bottom
		for _ in range(height // 2 + 1, height - 1):
			output.append(' ' * width)

		# Bottom row
		row_h = [' '] * width

		# DL
		if self.has_horizontal_start() and self.horizontal_run.origin_dir == 'D':
			row_h[width // 2] = '⮢'

		output.append(''.join(row_h))

		return output