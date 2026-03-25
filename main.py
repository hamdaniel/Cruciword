from Board.board import Board
import argparse
import random


def main(seed=None):
	if seed is None:
		seed = random.SystemRandom().randrange(0, 2**32)
		print(f"No seed provided. Using random seed: {seed}")

	random.seed(seed)

	board = Board(5, 5)
	board.load_dataset("Data/datasets/wiktionary_heb")
	while True:
		board.reset_generation_state()
		board.generate_skeleton()
		board.init_cells_possibilities()
		board.init_runs_possibilities()
		if(board.solve()):
			print(board)
			break
		else:
			print("Found contradiction, try again")
	# print(board)
	# print(board.verbose_print())


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Generate a crossword board")
	parser.add_argument("seed", nargs="?", type=int, help="Optional random seed")
	args = parser.parse_args()
	main(args.seed)