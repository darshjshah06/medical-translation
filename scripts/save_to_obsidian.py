from pathlib import Path
from datetime import datetime
from full_pipeline import process

VAULT_DIR = Path("../obsidian_vault/Cleaned_Transcripts")

def slugify(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "_" for c in text).strip("_")

def save_cleaned_note(raw_text: str, title: str = "cleaned_transcript") -> Path:
    cleaned_text, flags = process(raw_text)

    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{slugify(title)}_{timestamp}.md"
    out_path = VAULT_DIR / filename

    flag_lines = "\n".join(f"- {f}" for f in flags) if flags else "- None"

    content = f"""# {title}

## Raw Transcript
{raw_text}

## Cleaned Transcript
{cleaned_text}

## Flags
{flag_lines}
"""

    out_path.write_text(content, encoding="utf-8")
    return out_path

if __name__ == "__main__":
    raw = input("Paste transcript:\n")
    title = input("Note title:\n").strip() or "cleaned_transcript"
    path = save_cleaned_note(raw, title)
    print(f"Saved to: {path}")