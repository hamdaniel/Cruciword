import json
import os
import re

from Utils.bitarray import BitArray, HEBREW_ALPHABET, MIN_LENGTH, MAX_LENGTH

INPUT_DIR = "processed/output_by_length"
OUTPUT_DIR = "processed/bitmaps"


LENGTH_FILE_RE = re.compile(r"^length_(\d+)\.json$")



def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def iter_length_files(input_dir: str):
    for name in sorted(os.listdir(input_dir)):
        match = LENGTH_FILE_RE.match(name)
        if not match:
            continue

        length = int(match.group(1))
        if length < MIN_LENGTH or length > MAX_LENGTH:
            continue

        yield length, os.path.join(input_dir, name)


def build_bitmaps_for_length(length: int, words: list[str]) -> dict[tuple[int, str], BitArray]:
    logical_size = len(words)
    bitmaps = {}

    for position in range(1, length + 1):
        for letter in HEBREW_ALPHABET:
            bitmaps[(position, letter)] = BitArray(logical_size)

    for word_index, word in enumerate(words):
        if len(word) != length:
            raise ValueError(
                f"Word {word!r} in length_{length}.json has actual length {len(word)}"
            )

        for position, letter in enumerate(word, start=1):
            if letter not in HEBREW_ALPHABET:
                raise ValueError(
                    f"Word {word!r} contains non-Hebrew-alphabet letter {letter!r}"
                )

            bitmaps[(position, letter)][word_index] = 1

    return bitmaps


def process_length_file(length: int, input_path: str) -> None:
    print(f"Processing {input_path}")

    data = load_json(input_path)

    # The JSON files are already written in canonical sorted order.
    words = list(data.keys())

    logical_size = len(words)
    print(f"  length={length}, words={logical_size}")

    bitmaps = build_bitmaps_for_length(length, words)

    length_output_dir = os.path.join(OUTPUT_DIR, f"length_{length}")
    os.makedirs(length_output_dir, exist_ok=True)

    bitmaps_path = os.path.join(length_output_dir, f"length_{length}.bitmaps")
    words_path = os.path.join(length_output_dir, "words.json")
    metadata_path = os.path.join(length_output_dir, "metadata.json")

    BitArray.save_store(
        path=bitmaps_path,
        word_length=length,
        logical_size=logical_size,
        bitmaps_by_key=bitmaps,
        alphabet=HEBREW_ALPHABET,
    )

    save_json(words_path, words)

    metadata = {
        "length": length,
        "logical_size": logical_size,
        "alphabet": HEBREW_ALPHABET,
        "bitmaps_file": os.path.basename(bitmaps_path),
        "words_file": os.path.basename(words_path),
    }
    save_json(metadata_path, metadata)

    print(f"  wrote {bitmaps_path}")
    print(f"  wrote {words_path}")
    print(f"  wrote {metadata_path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    found_any = False

    for length, input_path in iter_length_files(INPUT_DIR):
        found_any = True
        process_length_file(length, input_path)

    if not found_any:
        print(f"No length_*.json files found in '{INPUT_DIR}'.")
        return

    print("Done.")


if __name__ == "__main__":
    main()