from board import Board
from cells import Cell, ClueCell, LetterCell, RunStart

def main():
	board = Board(8, 8)
	board.generate_template()
	print(board)


if __name__ == "__main__":
	main()