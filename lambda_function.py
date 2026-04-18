import json
import os
from datetime import datetime, timezone

import boto3

from scripts.full_pipeline import process

s3 = boto3.client("s3")

OUTPUT_BUCKET = os.environ.get("OUTPUT_BUCKET", "")
OUTPUT_PREFIX = os.environ.get("OUTPUT_PREFIX", "vault/Cleaned_Transcripts")


def build_markdown_note(title: str, raw_text: str, cleaned_text: str, flags):
    flag_lines = "\n".join(f"- {f}" for f in flags) if flags else "- None"

    return f"""# {title}

## Raw Transcript
{raw_text}

## Cleaned Transcript
{cleaned_text}

## Flags
{flag_lines}
"""


def slugify(text: str) -> str:
    return "".join(c.lower() if c.isalnum() else "_" for c in text).strip("_")


def put_text_to_s3(bucket: str, key: str, body: str, content_type: str = "text/plain; charset=utf-8"):
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body.encode("utf-8"),
        ContentType=content_type,
    )


def lambda_handler(event, context):
    """
    Expected event:
    {
      "transcript_id": "case_001",
      "title": "case_001",
      "transcript_text": "raw transcript here",
      "write_markdown": true,
      "write_json": true
    }
    """

    transcript_id = event.get("transcript_id") or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    title = event.get("title") or transcript_id
    raw_text = event.get("transcript_text", "")
    write_markdown = bool(event.get("write_markdown", True))
    write_json = bool(event.get("write_json", True))

    if not raw_text:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "transcript_text is required"})
        }

    cleaned_text, flags = process(raw_text)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    safe_title = slugify(title)

    result = {
        "transcript_id": transcript_id,
        "title": title,
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
        "flags": flags,
        "timestamp_utc": timestamp,
        "markdown_s3_key": None,
        "json_s3_key": None,
    }

    if OUTPUT_BUCKET:
        if write_markdown:
            markdown_key = f"{OUTPUT_PREFIX}/{safe_title}_{timestamp}.md"
            markdown_body = build_markdown_note(title, raw_text, cleaned_text, flags)
            put_text_to_s3(
                bucket=OUTPUT_BUCKET,
                key=markdown_key,
                body=markdown_body,
                content_type="text/markdown; charset=utf-8",
            )
            result["markdown_s3_key"] = markdown_key

        if write_json:
            json_key = f"{OUTPUT_PREFIX}/{safe_title}_{timestamp}.json"
            put_text_to_s3(
                bucket=OUTPUT_BUCKET,
                key=json_key,
                body=json.dumps(result, ensure_ascii=False, indent=2),
                content_type="application/json; charset=utf-8",
            )
            result["json_s3_key"] = json_key

    return {
        "statusCode": 200,
        "body": json.dumps(result, ensure_ascii=False)
    }