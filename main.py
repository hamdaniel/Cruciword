from Board.board import Board

def main():
	board = Board(15, 15)
	board.load_dataset("Data/datasets/wiktionary_heb")
	while True:
		board.generate_skeleton()
		board.init_cells_possibilities()
		board.init_runs_possibilities()
		if(board.propagate_constraints()):
			print(board)
			break
		else:
			print("Found contradiction, try again")
	# print(board)
	# print(board.verbose_print())



if __name__ == "__main__":
	main()