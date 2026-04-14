# Medical Translation Accuracy System

## Overview
Multilingual correction + validation system for improving AI transcription accuracy (Hindi, Telugu, English).

## Features
- Dictionary-based correction
- Numeric confusion handling
- Medical term normalization
- Obsidian integration (RAG)
- Gradio integration ready

## Structure
- scripts/ → processing pipeline
- data/libraries/ → language dictionaries
- obsidian_vault/ → knowledge base

## Usage
Run:
```bash
python3 scripts/full_pipeline.py