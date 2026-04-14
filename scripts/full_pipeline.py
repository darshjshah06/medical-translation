import json
import re

# -------------------------
# LOAD JSON FILE
# -------------------------
def load_json(path):
    with open(path) as f:
        return json.load(f)

# -------------------------
# LOAD LIBRARIES
# -------------------------
hindi_lib = load_json("../data/libraries/hindi_error_library.json")
telugu_lib = load_json("../data/libraries/telugu_error_library.json")
english_lib = load_json("../data/libraries/english_error_library.json")

# -------------------------
# BASIC CLEAN
# -------------------------
def normalize_text(text):
    return text.lower().strip()

# -------------------------
# FIX NUMERIC CONFUSION
# -------------------------
def fix_numeric_confusion(text):
    flags = []

    stripped = text.strip().lower()

    # Only fix if the whole response is likely a yes/no answer
    if stripped == "9":
        return "no", ["Numeric confusion: '9' interpreted as 'no'"]

    if stripped == "9 sir":
        return "no", ["Numeric confusion: '9 sir' interpreted as 'no'"]

    if stripped == "9 madam":
        return "no", ["Numeric confusion: '9 madam' interpreted as 'no'"]

    return text, flags

# -------------------------
# APPLY LIBRARY (CORE)
# -------------------------
def apply_library(text, lib):
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
# MAIN PROCESS FUNCTION
# -------------------------
def process(text):
    text = normalize_text(text)

    # First fix known ASR number confusion
    text, f0 = fix_numeric_confusion(text)

    # Apply all languages
    text, f1 = apply_library(text, hindi_lib)
    text, f2 = apply_library(text, telugu_lib)
    text, f3 = apply_library(text, english_lib)

    flags = f0 + f1 + f2 + f3

    return text, flags

# -------------------------
# RUN SCRIPT
# -------------------------
if __name__ == "__main__":
    user_input = input("Enter transcript:\n")

    cleaned, flags = process(user_input)

    print("\n--- CLEANED ---")
    print(cleaned)

    print("\n--- FLAGS ---")
    for f in flags:
        print("-", f)