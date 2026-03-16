import random

BOARD_WIDTH = 8
BOARD_HEIGHT = 8

EMPTY_CHAR = ' '
CLUE_CELL = '?'

# Each cell can be a clue cell. or a letter cell.
# Letter cells can be the start of words. If they are, they will be denoted as follows: <origin><direction><length>:
# Origin: denotes what adjacent clue cell is the origin of the word. it can be U, D, L, R.
# Direction: denotes the direction of the word. it can be L,D.
# Length: denotes the length of the word.

def get_cell(board, x, y):
	return board[y][BOARD_WIDTH - 1 - x]


def set_cell(board, x, y, value):
	board[y][BOARD_WIDTH - 1 - x] = value


def is_clue_cell(board, x, y):
	return get_cell(board, x, y) == CLUE_CELL


def is_start_cell(cell):
	return cell not in (EMPTY_CHAR, CLUE_CELL)


def num_clues(board, x, y):
	if get_cell(board, x, y) != CLUE_CELL:
		return 0

	count = 0

	if x > 0:
		cell = get_cell(board, x - 1, y)
		if is_start_cell(cell) and cell[0] == 'L':
			count += 1

	if x < BOARD_WIDTH - 1:
		cell = get_cell(board, x + 1, y)
		if is_start_cell(cell) and cell[0] == 'R':
			count += 1

	if y > 0:
		cell = get_cell(board, x, y - 1)
		if is_start_cell(cell) and cell[0] == 'D':
			count += 1

	if y < BOARD_HEIGHT - 1:
		cell = get_cell(board, x, y + 1)
		if is_start_cell(cell) and cell[0] == 'U':
			count += 1

	return count


def find_clue_origin(board, x, y):
	if get_cell(board, x, y)[0] not in ('U', 'D', 'L', 'R'):
		return None
	direction = get_cell(board, x, y)[0]
	if direction == 'U':
		return (x, y - 1)
	elif direction == 'D':
		return (x, y + 1)
	elif direction == 'L':
		return (x - 1, y)
	else:  # direction == 'R'
		return (x + 1, y)


def calc_run_length(board, x, y, direction):
	if is_clue_cell(board, x, y):
		return 0

	length = 0

	if direction == 'L':
		for i in range(x, BOARD_WIDTH):
			if is_clue_cell(board, i, y):
				break
			length += 1
	else:  # direction == 'D'
		for j in range(y, BOARD_HEIGHT):
			if is_clue_cell(board, x, j):
				break
			length += 1

	return length


# Cells are eligible iff:
# 1. They do not shorten the only run of a clue cell to less than 2
# 2. They do not turn the only run of a letter cell into a length 1 run
# 3. The down going run from their bottom and/or the left going run from their left is of length 2 or more
def is_eligible_for_clue_cell(board, x, y):
	if is_clue_cell(board, x, y):
		return False

	# Check the cell directly above.
	# If it is the start of a down run, the clue cell this run belongs to must have at least one more run.
	# In addition, it must only be a part of a left run, starting to its right
	if y > 0:
		above = get_cell(board, x, y - 1)

		if is_start_cell(above):
			if above[1] == 'D':
				origin = find_clue_origin(board, x, y - 1)
				if origin and num_clues(board, origin[0], origin[1]) == 1:
					return False
				
				i = x
				found_left_start = False

				while i >= 0:
					cell = get_cell(board, i, y - 1)
					if is_clue_cell(board, i, y - 1):
						break
					if is_start_cell(cell) and cell[1] == 'L':
						found_left_start = True
						break
					i -= 1

				if not found_left_start:
					return False

		# If it is a clue cell, it must have at least one more run.
		if num_clues(board, x, y - 1) == 1:
			return False

	# Check the cell directly to the right.
	# If it is the start of a left run, the clue cell this run belongs to must have at least one more run.
	if x > 0:
		right = get_cell(board, x - 1, y)

		if is_start_cell(right):
			if right[1] == 'L':
				origin = find_clue_origin(board, x - 1, y)
				if origin and num_clues(board, origin[0], origin[1]) == 1:
					return False

				j = y
				found_up_start = False

				while j >= 0:
					cell = get_cell(board, x - 1, j)
					if is_clue_cell(board, x - 1, j):
						break
					if is_start_cell(cell) and cell[1] == 'D':
						found_up_start = True
						break
					j -= 1

				if not found_up_start:
					return False

		# If it is a clue cell, it must have at least one more run.
		if num_clues(board, x - 1, y) == 1:
			return False

	# Check the lengths of the down going run from the bottom and left going run from the left.
	left_run = 0
	down_run = 0

	if x < BOARD_WIDTH - 1:
		left_run = calc_run_length(board, x + 1, y, 'L')

	if y < BOARD_HEIGHT - 1:
		down_run = calc_run_length(board, x, y + 1, 'D')

	if left_run < 2 and down_run < 2:
		return False

	return True


def len_1_runs_created(board, x, y):
	count = 0

	if y > 0:
		cell = get_cell(board, x, y - 1)
		if is_start_cell(cell) and cell[0] == 'D':
			count += 1

	if x > 0:
		cell = get_cell(board, x - 1, y)
		if is_start_cell(cell) and cell[0] == 'L':
			count += 1

	left_run = 0
	down_run = 0

	if x < BOARD_WIDTH - 1:
		left_run = calc_run_length(board, x + 1, y, 'L')

	if y < BOARD_HEIGHT - 1:
		down_run = calc_run_length(board, x, y + 1, 'D')

	if left_run == 1:
		count += 1
	if down_run == 1:
		count += 1

	return count


def update_left_run_lengths_to_the_right(board, x, y):
	i = x - 1
	while i >= 0:
		cell = get_cell(board, i, y)

		if cell == CLUE_CELL:
			break

		if is_start_cell(cell) and cell[1] == 'L':
			origin = cell[0]
			new_len = calc_run_length(board, i, y, 'L')
			if new_len >= 2:
				set_cell(board, i, y, f"{origin}L{new_len}")
			else:
				set_cell(board, i, y, EMPTY_CHAR)
			break

		i -= 1


def update_down_run_lengths_above(board, x, y):
	j = y - 1
	while j >= 0:
		cell = get_cell(board, x, j)

		if cell == CLUE_CELL:
			break

		if is_start_cell(cell) and cell[1] == 'D':
			origin = cell[0]
			new_len = calc_run_length(board, x, j, 'D')
			if new_len >= 2:
				set_cell(board, x, j, f"{origin}D{new_len}")
			else:
				set_cell(board, x, j, EMPTY_CHAR)
			break

		j -= 1


def clue_start_cells_of_clue(board, x, y):
	"""
	Return all start cells belonging to clue cell (x, y).
	Each item is (sx, sy, cell_string).
	"""
	if not is_clue_cell(board, x, y):
		return []

	starts = []

	if x > 0:
		cell = get_cell(board, x - 1, y)
		if is_start_cell(cell) and cell[0] == 'L':
			starts.append((x - 1, y, cell))

	if x < BOARD_WIDTH - 1:
		cell = get_cell(board, x + 1, y)
		if is_start_cell(cell) and cell[0] == 'R':
			starts.append((x + 1, y, cell))

	if y > 0:
		cell = get_cell(board, x, y - 1)
		if is_start_cell(cell) and cell[0] == 'D':
			starts.append((x, y - 1, cell))

	if y < BOARD_HEIGHT - 1:
		cell = get_cell(board, x, y + 1)
		if is_start_cell(cell) and cell[0] == 'U':
			starts.append((x, y + 1, cell))

	return starts


def are_diagonal(x1, y1, x2, y2):
	return abs(x1 - x2) == 1 and abs(y1 - y2) == 1


def are_orthogonally_adjacent(x1, y1, x2, y2):
	return abs(x1 - x2) + abs(y1 - y2) == 1


def origin_letter_for_clue(start_x, start_y, clue_x, clue_y):
	"""
	Return the origin letter that the start cell should have
	if its clue cell is at (clue_x, clue_y).
	"""
	if clue_x == start_x and clue_y == start_y - 1:
		return 'U'
	if clue_x == start_x and clue_y == start_y + 1:
		return 'D'
	if clue_x == start_x - 1 and clue_y == start_y:
		return 'R'
	if clue_x == start_x + 1 and clue_y == start_y:
		return 'L'
	return None


def same_start_cell(a, b):
	ax, ay = a[0], a[1]
	bx, by = b[0], b[1]
	return ax == bx and ay == by


def get_transfer_info(board, ax, ay, bx, by):
	"""
	Check if clue cell A=(ax,ay) can transfer one clue to diagonal clue cell B=(bx,by).

	Returns None if not eligible.
	Otherwise returns:
		(start_x, start_y, old_cell_string, new_cell_string)
	where the move is done by rewriting the start cell.
	"""
	if not are_diagonal(ax, ay, bx, by):
		return None

	if not is_clue_cell(board, ax, ay) or not is_clue_cell(board, bx, by):
		return None

	if num_clues(board, ax, ay) != 2:
		return None

	if num_clues(board, bx, by) != 1:
		return None

	a_starts = clue_start_cells_of_clue(board, ax, ay)
	b_starts = clue_start_cells_of_clue(board, bx, by)

	b_only = b_starts[0]

	candidates = []
	for sx, sy, cell in a_starts:
		# criterion 3: one of A's clues starts adjacent to B
		if are_orthogonally_adjacent(sx, sy, bx, by):
			# criterion 5: B's clue must not start at the same start cell
			if not same_start_cell((sx, sy, cell), b_only):
				candidates.append((sx, sy, cell))

	if len(candidates) != 1:
		return None

	sx, sy, old_cell = candidates[0]

	# same direction, same length, only origin changes
	new_origin = origin_letter_for_clue(sx, sy, bx, by)
	if new_origin is None:
		return None

	new_cell = new_origin + old_cell[1:]   # keep direction+length

	return (sx, sy, old_cell, new_cell)


def collect_eligible_transfer_pairs(board):
	"""
	Return a list of ordered pairs (ax, ay, bx, by) where
	A can transfer one clue to B.
	"""
	pairs = []

	for y in range(BOARD_HEIGHT):
		for x in range(BOARD_WIDTH):
			if not is_clue_cell(board, x, y):
				continue

			# check down-left diagonal
			nx, ny = x - 1, y + 1
			if 0 <= nx < BOARD_WIDTH and 0 <= ny < BOARD_HEIGHT and is_clue_cell(board, nx, ny):
				# Either direction may be eligible
				if get_transfer_info(board, x, y, nx, ny) is not None:
					pairs.append((x, y, nx, ny))
				if get_transfer_info(board, nx, ny, x, y) is not None:
					pairs.append((nx, ny, x, y))

			# check down-right diagonal
			nx, ny = x + 1, y + 1
			if 0 <= nx < BOARD_WIDTH and 0 <= ny < BOARD_HEIGHT and is_clue_cell(board, nx, ny):
				if get_transfer_info(board, x, y, nx, ny) is not None:
					pairs.append((x, y, nx, ny))
				if get_transfer_info(board, nx, ny, x, y) is not None:
					pairs.append((nx, ny, x, y))

	return pairs


def apply_transfer(board, ax, ay, bx, by):
	info = get_transfer_info(board, ax, ay, bx, by)
	if info is None:
		return False

	sx, sy, old_cell, new_cell = info
	set_cell(board, sx, sy, new_cell)
	return True


def apply_random_transfers(board):
	pairs = collect_eligible_transfer_pairs(board)
	random.shuffle(pairs)

	moved = 0
	for ax, ay, bx, by in pairs:
		if apply_transfer(board, ax, ay, bx, by):
			print(f"Transferred clue from ({ax},{ay}) to ({bx},{by})")
			moved += 1

	return moved


def create_board():
	# Create an empty board
	board = [[EMPTY_CHAR for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]

	# Select one of 3 possibilities for the top right corner:
	#  ?? | _? | _?
	#  __ | _? | __

	random_choice = random.choice([1, 2, 3])
	if random_choice == 1:
		set_cell(board, 0, 0, CLUE_CELL)
		set_cell(board, 0, 1, f"UL{calc_run_length(board, 0, 1, 'L')}")

		set_cell(board, 1, 0, CLUE_CELL)
		set_cell(board, 1, 1, f"UD{calc_run_length(board, 1, 1, 'D')}")

	elif random_choice == 2:
		set_cell(board, 0, 0, CLUE_CELL)
		set_cell(board, 1, 0, f"RD{calc_run_length(board, 1, 0, 'D')}")

		set_cell(board, 0, 1, CLUE_CELL)
		set_cell(board, 1, 1, f"RL{calc_run_length(board, 1, 1, 'L')}")

	else:
		set_cell(board, 0, 0, CLUE_CELL)
		set_cell(board, 1, 0, f"RD{calc_run_length(board, 1, 0, 'D')}")
		set_cell(board, 0, 1, f"UL{calc_run_length(board, 0, 1, 'L')}")
	
	# Assign clue cells in rightmost column
	# Each row must contain a clue defining its run. It can be defined by one of three cells:
	# 1. The rightmost cell in the row above (not always possible)
	# 2. The rightmost cell in the row below (not always possible)
	# 3. The rightmost cell in the row itself (always possible)

	for r in range(2, BOARD_HEIGHT):
		# If already a clue cell, skip
		if is_clue_cell(board, 0, r):
			continue

		legal_options = [3]

		# There is a clue cell above that has only one clue
		if (r > 0) and (num_clues(board, 0, r - 1) == 1):
			legal_options.append(1)

		# There is a cell below and the cell above is a clue cell
		if (r < BOARD_HEIGHT - 1) and is_clue_cell(board, 0, r - 1):
			legal_options.append(2)
		
		random_choice = random.choice(legal_options)
		if random_choice == 1:
			set_cell(board, 0, r, f"UL{calc_run_length(board, 0, r, 'L')}")

		elif random_choice == 2:
			set_cell(board, 0, r + 1, CLUE_CELL)
			set_cell(board, 1, r + 1, f"RL{calc_run_length(board, 1, r + 1, 'L')}")
			set_cell(board, 0, r, f"DL{calc_run_length(board, 0, r, 'L')}")

		else:
			set_cell(board, 0, r, CLUE_CELL)
			set_cell(board, 1, r, f"RL{calc_run_length(board, 1, r, 'L')}")

	# Assign clue cells in top row
	# Each column must contain a clue defining its run. It can be defined by one of three cells:
	# 1. The top cell in the column to the right (not always possible)
	# 2. The top cell in the column to the left (not always possible)
	# 3. The top cell in the column itself (always possible)

	for c in range(2, BOARD_WIDTH):
		# If already a clue cell, skip
		if is_clue_cell(board, c, 0):
			continue

		legal_options = [3]

		# There is a clue cell to the right that has only one clue
		if (c > 0) and (num_clues(board, c - 1, 0) == 1):
			legal_options.append(1)

		# There is a cell to the left and the cell to the right is a clue cell
		if (c < BOARD_WIDTH - 1) and is_clue_cell(board, c - 1, 0):
			legal_options.append(2)
		
		random_choice = random.choice(legal_options)
		if random_choice == 1:
			set_cell(board, c, 0, f"RD{calc_run_length(board, c, 0, 'D')}")

		elif random_choice == 2:
			set_cell(board, c + 1, 0, CLUE_CELL)
			set_cell(board, c + 1, 1, f"UD{calc_run_length(board, c + 1, 1, 'D')}")
			set_cell(board, c, 0, f"LD{calc_run_length(board, c, 0, 'D')}")

		else:
			set_cell(board, c, 0, CLUE_CELL)
			set_cell(board, c, 1, f"UD{calc_run_length(board, c, 1, 'D')}")



	# Iterate over the rest of the board and assign clue cell with low probability in eligible cells
	# Eligable cells have a 1/6 base probability of being a clue cell, multiplied by 0.5 for each length 1 run it would create
	coords = [(x, y) for x in range(1, BOARD_WIDTH) for y in range(1, BOARD_HEIGHT)]
	random.shuffle(coords)

	for x, y in coords:
		if is_eligible_for_clue_cell(board, x, y):
			prob = (1.0 / 6) * (0.5 ** len_1_runs_created(board, x, y))
			if random.random() < prob:
				# Set the cell to be a clue cell and update the runs of adjacent cells accordingly
				set_cell(board, x, y, CLUE_CELL)

				left_run = 0
				down_run = 0

				if x < BOARD_WIDTH - 1:
					left_run = calc_run_length(board, x + 1, y, 'L')
				if y < BOARD_HEIGHT - 1:
					down_run = calc_run_length(board, x, y + 1, 'D')

				if left_run >= 2:
					set_cell(board, x + 1, y, f"RL{left_run}")
				if down_run >= 2:
					set_cell(board, x, y + 1, f"UD{down_run}")
									
				update_left_run_lengths_to_the_right(board, x, y)
				update_down_run_lengths_above(board, x, y)

	apply_random_transfers(board)
	return board

def validate_board(board):
	for y in range(BOARD_HEIGHT):
		for x in range(BOARD_WIDTH):
			cell = get_cell(board, x, y)

			if cell in (EMPTY_CHAR, CLUE_CELL):
				continue

			origin = cell[0]
			direction = cell[1]
			stored_len = int(cell[2:])

			if origin == 'U':
				ox, oy = x, y - 1
			elif origin == 'D':
				ox, oy = x, y + 1
			elif origin == 'L':
				ox, oy = x + 1, y
			elif origin == 'R':
				ox, oy = x - 1, y
			else:
				print(f"Bad origin at {(x,y)}: {cell}")
				return False

			if not (0 <= ox < BOARD_WIDTH and 0 <= oy < BOARD_HEIGHT):
				print(f"Origin out of bounds at {(x,y)}: {cell}")
				return False

			if not is_clue_cell(board, ox, oy):
				print(f"Origin is not a clue cell at {(x,y)}: {cell}, origin {(ox,oy)}")
				return False

			actual_len = calc_run_length(board, x, y, direction)
			if stored_len != actual_len:
				print(f"Bad length at {(x,y)}: stored {stored_len}, actual {actual_len}, cell={cell}")
				return False

			if actual_len < 2:
				print(f"Too-short run at {(x,y)}: {cell}")
				return False

	return True

def print_board(board):
	for row in board:
		print(" | ".join(f"{cell:>3}" for cell in row))


def main():
	board = create_board()
	print_board(board)


if __name__ == "__main__":
	main()