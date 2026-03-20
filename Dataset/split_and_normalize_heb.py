import json
import os
import re

INPUT_FILE = "wiktionary_entries.json"
OUTPUT_DIR = "output_by_length"

MIN_LENGTH = 2
MAX_LENGTH = 15

FINAL_MAP = str.maketrans({
    "ך": "כ",
    "ם": "מ",
    "ן": "נ",
    "ף": "פ",
    "ץ": "צ",
})

# Hebrew nikud / cantillation marks
NIKUD_RE = re.compile(r"[\u0591-\u05C7]")

# Keep Hebrew letters only for keys
NON_HEBREW_RE = re.compile(r"[^א-ת]")


def remove_nikud(text: str) -> str:
    return NIKUD_RE.sub("", text)


def normalize_key(text: str) -> str:
    text = remove_nikud(text)
    text = text.translate(FINAL_MAP)
    text = NON_HEBREW_RE.sub("", text)
    return text


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    grouped = {}

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

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for length, group_data in grouped.items():
        if not group_data:
            continue

        sorted_group_data = {
            key: group_data[key]
            for key in sorted(group_data.keys())
        }

        output_path = os.path.join(OUTPUT_DIR, f"length_{length}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sorted_group_data, f, ensure_ascii=False, indent=2)

    print(f"Done. Created {len(grouped)} files in '{OUTPUT_DIR}'.")


if __name__ == "__main__":
    main()