import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from Utils.bitarray import MIN_LENGTH, MAX_LENGTH

FINAL_MAP = str.maketrans({
    "ך": "כ",
    "ם": "מ",
    "ן": "נ",
    "ף": "פ",
    "ץ": "צ",
})

NIKUD_RE = re.compile(r"[\u0591-\u05C7]")
NON_HEBREW_RE = re.compile(r"[^א-ת]")


def remove_nikud(text: str) -> str:
    return NIKUD_RE.sub("", text)


def normalize_key(text: str) -> str:
    text = remove_nikud(text)
    text = text.translate(FINAL_MAP)
    text = NON_HEBREW_RE.sub("", text)
    return text


def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <dataset_root_dir>")
        sys.exit(1)

    root_dir = Path(sys.argv[1]).resolve()

    input_file = root_dir / "raw" / "wiktionary_entries.json"
    output_dir = root_dir / "processed" / "words_by_length"

    if not input_file.is_file():
        print(f"Error: input file not found: {input_file}")
        sys.exit(1)

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_original = len(data)
    print(f"Original entries: {total_original}")

    grouped = {}
    total_kept = 0

    for key, value in data.items():
        norm_key = normalize_key(key)

        if not norm_key:
            continue

        length = len(norm_key)

        if length < MIN_LENGTH or length > MAX_LENGTH:
            continue

        normalized_values = [remove_nikud(v) for v in value]

        if length not in grouped:
            grouped[length] = {}

        if norm_key in grouped[length]:
            grouped[length][norm_key].extend(normalized_values)
        else:
            grouped[length][norm_key] = normalized_values
            total_kept += 1  # count unique normalized entries

    os.makedirs(output_dir, exist_ok=True)

    print(f"Total normalized entries kept: {total_kept}")

    for length, group_data in grouped.items():
        if not group_data:
            continue

        sorted_group_data = {
            key: group_data[key]
            for key in sorted(group_data.keys())
        }

        output_path = output_dir / f"length_{length}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sorted_group_data, f, ensure_ascii=False, indent=2)

        print(f"  length {length}: {len(sorted_group_data)} entries")

    print(f"Done. Created {len(grouped)} files in '{output_dir}'.")


if __name__ == "__main__":
    main()