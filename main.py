from Board.board import Board
from Board.cells import Cell, ClueCell, LetterCell, Run

def main():
	board = Board(15, 15)
	board.generate_skeleton()
	print(board)
	# print(board.verbose_print())


if __name__ == "__main__":
	main()