import bz2
import json
import re
import xml.etree.ElementTree as ET

INPUT_FILE = "hewiktionary-latest-pages-articles.xml.bz2"
OUTPUT_FILE = "wiktionary_entries.json"
FILTERED_WORDS_FILE = "filtered_titles.txt"

NS_URI = "http://www.mediawiki.org/xml/export-0.11/"
NS = f"{{{NS_URI}}}"

NIKUD_RE = re.compile(r"[\u0591-\u05C7]")


def strip_nikud(text: str) -> str:
    if not text:
        return ""
    return NIKUD_RE.sub("", text)


def clean_text(text: str) -> str:
    if not text:
        return ""

    # [[page|label]] -> label
    text = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", text)

    # [[page]] -> page
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)

    # remove bold/italic wiki markup
    text = text.replace("'''", "").replace("''", "")

    # remove wiki templates like {{...}}
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)

    # remove html comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # remove html-like tags
    text = re.sub(r"</?[^>]+>", "", text)

    # normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def clean_definition(text: str) -> str:
    t = clean_text(text)

    # remove parentheses and their contents
    t = re.sub(r"\([^)]*\)", "", t)

    # normalize whitespace
    t = re.sub(r"\s+", " ", t).strip()

    # remove nikud
    t = strip_nikud(t)

    # remove trailing periods
    t = re.sub(r"[.]+$", "", t).strip()

    return t


def clean_synonym(text: str) -> str:
    t = clean_definition(text)
    t = re.sub(r"\s*\(\d+\)\s*$", "", t).strip()
    return t

def is_valid_item(text: str) -> bool:
    return bool(text) and ":" not in text

def load_filtered_words(path: str) -> set[str]:
    words = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip()
            if word:
                words.add(clean_definition(word))
    return words


def get_child_text(elem, tag_name):
    child = elem.find(f"{NS}{tag_name}")
    return child.text if child is not None else None


def find_text_elem(page):
    rev = page.find(f"{NS}revision")
    if rev is None:
        return None
    return rev.find(f"{NS}text")


def parse_entry_wikitext(title: str, text: str):
    page_title = clean_definition(title)
    lines = text.splitlines()
    items = []

    in_headword = False
    in_synonyms = False
    allow_definitions = False
    seen_definition_in_current_headword = False

    section_re = re.compile(r"^==\s*(.*?)\s*==$")
    subsection_re = re.compile(r"^===\s*(.*?)\s*===$")

    blocked_definition_subsections = {
        "גזרון",
        "גיזרון",
        "מקור",
        "אטימולוגיה",
        "תרגום",
        "תרגומים",
        "ראו גם",
        "מידע נוסף",
        "צרופים",
        "ביטויים",
        "נגזרות",
        "קישורים חיצוניים",
        "הערות שוליים",
        "אסמכתאות",
    }

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        m_sub = subsection_re.match(line)
        if m_sub:
            subsection_name = clean_definition(m_sub.group(1))
            in_synonyms = (subsection_name == "מילים נרדפות")
            allow_definitions = subsection_name not in blocked_definition_subsections
            continue

        m_sec = section_re.match(line)
        if m_sec:
            in_headword = True
            in_synonyms = False
            allow_definitions = True
            seen_definition_in_current_headword = False
            continue

        if not in_headword:
            continue

        if (
            allow_definitions
            and not seen_definition_in_current_headword
            and line.startswith("#")
            and not line.startswith("#:")
            and not line.startswith("#*")
        ):
            value = clean_definition(line[1:].strip())

            if is_valid_item(value) and value not in items:
                items.append(value)

            seen_definition_in_current_headword = True
            continue
        if in_synonyms and line.startswith("*"):
            value = clean_synonym(line[1:].strip())
            if is_valid_item(value) and value not in items:
                items.append(value)
            continue

    return page_title, items


def extract_filtered_main_namespace_pages_to_json():
    results = {}
    count = 0
    filtered_words = load_filtered_words(FILTERED_WORDS_FILE)

    with bz2.open(INPUT_FILE, "rb") as f:
        context = ET.iterparse(f, events=("end",))

        for _, elem in context:
            if elem.tag != f"{NS}page":
                continue

            ns = get_child_text(elem, "ns")
            title = get_child_text(elem, "title")

            if ns == "0" and title:
                page_title = clean_definition(title)

                if page_title not in filtered_words:
                    elem.clear()
                    continue

                text_elem = find_text_elem(elem)
                text = text_elem.text if text_elem is not None and text_elem.text else ""

                _, items = parse_entry_wikitext(title, text)

                if items:
                    results[page_title] = items
                    count += 1
                    print(f"[{count}] Processed: {page_title}")

            elem.clear()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        json.dump(results, out, ensure_ascii=False, indent=2)

    print(f"Wrote {count} entries to {OUTPUT_FILE}")


if __name__ == "__main__":
    extract_filtered_main_namespace_pages_to_json()