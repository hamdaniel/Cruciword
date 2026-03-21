from Board.board import Board
from Board.cells import Cell, ClueCell, LetterCell, RunStart

def main():
	board = Board(15, 15)
	board.generate_template()
	print(board)


if __name__ == "__main__":
	main()