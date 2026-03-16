import re

HEBREW_LETTER = r"\u0590-\u05FF"
NIKUD = r"\u0591-\u05C7"

pattern = re.compile(
    rf'^[{HEBREW_LETTER}"\'_]+(?:-[{HEBREW_LETTER}"\'_]+)*$'
)

nikud_re = re.compile(f"[{NIKUD}]")

def is_valid_hebrew_title(title: str) -> bool:
    if not title:
        return False

    if title[0] in "-־/":
        return False

    # No  one letter titles
    if len(title) == 1:
        return False
    
	# No phrases longer than 3 words
    if title.count("_") > 2:
        return False

    # No nikud
    if nikud_re.search(title):
        return False

    # No multi acronym entries
    if '"' in title and '_' in title:
        return False

    # No acronyms longer than 4 letters 
    if '"' in title:
        if len(title.replace('"', '')) > 4:
            return False

    return bool(pattern.fullmatch(title))
if __name__ == "__main__":
    with open("raw_titles.txt", "r", encoding="utf-8") as file:
        titles = file.read().splitlines()

    filtered_titles = [t for t in titles if is_valid_hebrew_title(t)]

    with open("filtered_titles.txt", "w", encoding="utf-8") as file:
        for title in filtered_titles:
            file.write(title + "\n")