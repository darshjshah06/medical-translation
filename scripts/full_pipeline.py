import json
import re
from pathlib import Path

# -------------------------
# PATHS
# -------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
LIB_DIR = BASE_DIR / "data" / "libraries"

# -------------------------
# LOAD JSON FILE
# -------------------------
def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def load_json_optional(path: Path, default):
    if path.exists():
        return load_json(path)
    return default

# -------------------------
# LOAD LIBRARIES
# -------------------------
hindi_lib = load_json(LIB_DIR / "hindi_error_library.json")
telugu_lib = load_json(LIB_DIR / "telugu_error_library.json")
english_lib = load_json(LIB_DIR / "english_error_library.json")
insurance_entities = load_json(LIB_DIR / "insurance_entities.json")

# Optional file for exact known question normalizations
question_normalization_lib = load_json_optional(
    LIB_DIR / "question_normalization.json",
    default=[]
)

# -------------------------
# BASIC CLEAN
# -------------------------
def normalize_text(text: str) -> str:
    return (text or "").lower().strip()

# -------------------------
# FIX NUMERIC CONFUSION
# -------------------------
def fix_numeric_confusion(text: str):
    flags = []
    stripped = text.strip().lower()

    if stripped == "9":
        return "no", ["Numeric confusion: '9' interpreted as 'no'"]

    if stripped == "9 sir":
        return "no", ["Numeric confusion: '9 sir' interpreted as 'no'"]

    if stripped == "9 madam":
        return "no", ["Numeric confusion: '9 madam' interpreted as 'no'"]

    return text, flags

# -------------------------
# APPLY LIBRARY
# -------------------------
def apply_library(text: str, lib):
    flags = []

    for entry in lib:
        heard = entry["heard"]

        if heard in text:
            action = entry.get("action")

            if action in ["normalize", "autocorrect"]:
                replacement = entry.get("correct")
                if replacement is not None:
                    text = text.replace(heard, replacement)

            elif action == "ignore":
                text = text.replace(heard, "")

            elif action == "flag":
                flags.append(f"Flag: {heard}")

    return text, flags

# -------------------------
# APPLY INSURANCE ENTITIES
# -------------------------
def apply_entities(text: str) -> str:
    for entry in insurance_entities:
        heard = entry["heard"]
        correct = entry["correct"]

        if heard in text:
            text = text.replace(heard, correct)

    return text

# -------------------------
# QUESTION NORMALIZATION
# -------------------------
def apply_question_normalization_library(text: str):
    """
    Exact phrase-based normalization from question_normalization.json
    """
    flags = []

    for entry in question_normalization_lib:
        heard = entry.get("heard", "")
        correct = entry.get("correct", "")
        action = entry.get("action", "normalize")

        if heard and heard in text and action == "normalize" and correct:
            text = text.replace(heard, correct)
            flags.append(f"Question normalized (dict): {heard}")

    return text, flags


def normalize_question_form(text: str):
    """
    Structural normalization for bad statement-like translations
    caused by Hindi/Telugu SOV -> English SVO mismatch.
    """

    flags = []

    # Clean up some common mistranslated question starters
    replacements = [
        ("your chest pain", "do you have chest pain"),
        ("your problem is", "do you have"),
        ("you have liver problems", "do you have any liver problems"),
        ("you have blood disorders", "do you have any blood disorders"),
        ("you have kidney problem", "do you have any kidney problem"),
        ("you have kidney problems", "do you have any kidney problems"),
        ("you have fits", "do you have fits"),
        ("you have back", "do you have any back"),
        ("you will be traveling outside india", "do you intend to travel outside india within the next 3 months"),
        ("you have any eye, nose, or throat related problems", "do you have any eye, nose, or throat related problems"),
    ]

    for bad, good in replacements:
        if bad in text:
            text = text.replace(bad, good)
            flags.append(f"Question normalized (replace): {bad}")

    # Regex-based structural fixes
    patterns = [
        (
            r"\byou have ([a-z0-9,\-/\s]+?) problems\b",
            r"do you have any \1 problems?"
        ),
        (
            r"\byou have ([a-z0-9,\-/\s]+?) problem\b",
            r"do you have any \1 problem?"
        ),
        (
            r"\byou have ([a-z0-9,\-/\s]+?) issues\b",
            r"do you have any \1 issues?"
        ),
        (
            r"\byou have ([a-z0-9,\-/\s]+?) issue\b",
            r"do you have any \1 issue?"
        ),
        (
            r"\byou have ([a-z0-9,\-/\s]+?) disorder\b",
            r"do you have any \1 disorder?"
        ),
        (
            r"\byou have ([a-z0-9,\-/\s]+?) disorders\b",
            r"do you have any \1 disorders?"
        ),
        (
            r"\byou have ([a-z0-9,\-/\s]+?) disease\b",
            r"do you have any \1 disease?"
        ),
        (
            r"\byou have ([a-z0-9,\-/\s]+?) diseases\b",
            r"do you have any \1 diseases?"
        ),
        (
            r"\byou have ([a-z0-9,\-/\s]+?) related problems\b",
            r"do you have any \1 related problems?"
        ),
        (
            r"\byou have ([a-z0-9,\-/\s]+?) related problem\b",
            r"do you have any \1 related problem?"
        ),
        (
            r"\byour ([a-z0-9,\-/\s]+?) problems\b",
            r"do you have any \1 problems?"
        ),
        (
            r"\byour ([a-z0-9,\-/\s]+?) problem\b",
            r"do you have any \1 problem?"
        ),
    ]

    for pattern, replacement in patterns:
        if re.search(pattern, text):
            text = re.sub(pattern, replacement, text)
            flags.append(f"Question normalized (regex): {pattern}")

    # Normalize repeated awkward disease list constructions
    text = re.sub(
        r"\bdo you have any bp, sugar, cholesterol, thyroid problems\b",
        "do you have any bp, sugar, cholesterol, or thyroid problems?",
        text
    )
    text = re.sub(
        r"\bdo you have any blood disorders, anemia, leukemia, and problems with circulation\b",
        "do you have any blood disorders such as anemia, leukemia, or circulatory problems?",
        text
    )
    text = re.sub(
        r"\bdo you have any liver problems, hepatitis, jaundice, indigestion problems\b",
        "do you have any liver problems such as hepatitis, jaundice, or indigestion problems?",
        text
    )
    text = re.sub(
        r"\bdo you have any back, neck, muscle, bone joints, or arthritis\b",
        "do you have any back, neck, muscle, bone, joint, or arthritis problems?",
        text
    )

    return text, flags

# -------------------------
# MAIN PROCESS FUNCTION
# -------------------------
def process(text: str):
    text = normalize_text(text)

    # 1. Structural question repair
    text, fq1 = apply_question_normalization_library(text)
    text, fq2 = normalize_question_form(text)

    # 2. Known ASR number confusion
    text, f0 = fix_numeric_confusion(text)

    # 3. Language-specific cleanup
    text, f1 = apply_library(text, hindi_lib)
    text, f2 = apply_library(text, telugu_lib)
    text, f3 = apply_library(text, english_lib)

    # 4. Entity normalization
    text = apply_entities(text)

    # 5. Final whitespace cleanup
    text = " ".join(text.split())

    flags = fq1 + fq2 + f0 + f1 + f2 + f3
    return text, flags

# -------------------------
# CLI TEST
# -------------------------
if __name__ == "__main__":
    user_input = input("Enter transcript:\n")

    cleaned, flags = process(user_input)

    print("\n--- CLEANED ---")
    print(cleaned)

    print("\n--- FLAGS ---")
    for f in flags:
        print("-", f)