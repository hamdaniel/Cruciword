import json
import os

from Utils.bitarray import BitArray


LENGTH = 3
STORE_DIR = os.path.join("bitmaps", f"length_{LENGTH}")

# Choose the bitmaps you want to test here.
BITMAP_A = (1, "א")
BITMAP_B = (2, "ב")
BITMAP_C = (3, "א")


def load_json(path: str):
	with open(path, "r", encoding="utf-8") as f:
		return json.load(f)


def bitmap_to_word_set(bitmap: BitArray, words: list[str]) -> list[str]:
	result = []

	for i in range(len(bitmap)):
		if bitmap[i]:
			result.append(words[i])

	return result


def load_bitmap(file_data: bytes, logical_size: int, position: int, letter: str) -> BitArray:
	bitmap_index = BitArray.bitmap_index_for(position=position, letter=letter)
	return BitArray(file_data, logical_size=logical_size, bitmap_index=bitmap_index)


def print_word_set(title: str, word_set: list[str]) -> None:
	print(title)
	print(f"count = {len(word_set)}")

	if word_set:
		print(word_set)
	else:
		print("[]")

	print()


def main():
	bitmaps_path = os.path.join(STORE_DIR, f"length_{LENGTH}.bitmaps")
	words_path = os.path.join(STORE_DIR, "words.json")
	metadata_path = os.path.join(STORE_DIR, "metadata.json")

	words = load_json(words_path)
	metadata = load_json(metadata_path)
	file_data = BitArray.load_file(bitmaps_path)

	logical_size = metadata["logical_size"]

	a = load_bitmap(file_data, logical_size, *BITMAP_A)
	b = load_bitmap(file_data, logical_size, *BITMAP_B)
	c = load_bitmap(file_data, logical_size, *BITMAP_C)

	a_words = bitmap_to_word_set(a, words)
	b_words = bitmap_to_word_set(b, words)
	c_words = bitmap_to_word_set(c, words)

	print_word_set(f"A = {BITMAP_A}", a_words)
	print_word_set(f"B = {BITMAP_B}", b_words)
	print_word_set(f"C = {BITMAP_C}", c_words)

	union_ab = a | b
	intersection_ab = a & b

	print_word_set("A ∪ B", bitmap_to_word_set(union_ab, words))
	print_word_set("A ∩ B", bitmap_to_word_set(intersection_ab, words))

	union_abc = a | b
	union_abc |= c

	intersection_abc = a & b
	intersection_abc &= c

	print_word_set("A ∪ B ∪ C", bitmap_to_word_set(union_abc, words))
	print_word_set("A ∩ B ∩ C", bitmap_to_word_set(intersection_abc, words))
	difference_ab = a - b
	print_word_set("A - B", bitmap_to_word_set(difference_ab, words))


if __name__ == "__main__":
	main()