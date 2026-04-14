import json
import re

# Load libraries
with open("../data/libraries/hindi_error_library.json") as f:
    hindi_lib = json.load(f)

with open("../data/libraries/hindi_medical_phonetics.json") as f:
    medical_map = json.load(f)

with open("../data/libraries/validation_rules.json") as f:
    rules = json.load(f)


def normalize_text(text):
    text = text.lower()
    return text


def apply_dictionary(text):
    flags = []

    for entry in hindi_lib:
        heard = entry["heard"]
        if heard in text:
            action = entry["action"]

            if action == "normalize":
                text = text.replace(heard, entry["correct"])

            elif action == "autocorrect":
                text = text.replace(heard, entry["correct"])

            elif action == "flag":
                flags.append(f"Ambiguous phrase: {heard}")

            elif action == "ignore":
                text = text.replace(heard, "")

    return text, flags


def apply_medical_phonetics(text):
    for k, v in medical_map.items():
        if k in text:
            text = text.replace(k, v)
    return text


def validate_pan(pan):
    if not re.match(rules["pan"], pan):
        return False
    return True


def validate_pincode(pin):
    if not re.match(rules["pincode"], pin):
        return False
    return True


def process_text(text):
    text = normalize_text(text)

    text, flags = apply_dictionary(text)

    text = apply_medical_phonetics(text)

    return text, flags


if __name__ == "__main__":
    sample = input("Enter Hindi/hinglish text:\n")

    corrected, flags = process_text(sample)

    print("\nCorrected Text:\n", corrected)

    if flags:
        print("\nFlags:")
        for f in flags:
            print("-", f)