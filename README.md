# Meeting Note → Action Item Extractor

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/) [![GitHub stars](https://img.shields.io/github/stars/yksanjo/meeting-action-extractor?style=social)](https://github.com/yksanjo/meeting-action-extractor/stargazers) [![GitHub forks](https://img.shields.io/github/forks/yksanjo/meeting-action-extractor.svg)](https://github.com/yksanjo/meeting-action-extractor/network/members) [![GitHub issues](https://img.shields.io/github/issues/yksanjo/meeting-action-extractor.svg)](https://github.com/yksanjo/meeting-action-extractor/issues)
[![Last commit](https://img.shields.io/github/last-commit/yksanjo/meeting-action-extractor.svg)](https://github.com/yksanjo/meeting-action-extractor/commits/main)


Automatically extracts action items, assignees, and deadlines from meeting notes.

## Features

- Extracts action items from unstructured meeting notes
- Identifies assignees (mentions, @tags, or names)
- Extracts deadlines and due dates
- Outputs structured data (JSON, CSV, or Markdown table)
- Supports both LLM-based (OpenAI/Ollama) and rule-based extraction

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### CLI Mode

```bash
# Using LLM (OpenAI)
python extract_actions.py --input notes.txt --output actions.json --provider openai

# Using LLM (Ollama - local)
python extract_actions.py --input notes.txt --output actions.csv --provider ollama

# Using rule-based extraction (no API needed)
python extract_actions.py --input notes.txt --output actions.md --provider regex
```

### Python API

```python
from extract_actions import extract_action_items

notes = """
@sarah to finalize API spec by Friday
@dev team to investigate latency issues
John will update the documentation by next week
"""

actions = extract_action_items(notes, provider="openai")
print(actions)
```

### Web Interface

```bash
python app.py
```

Then open http://localhost:5000 in your browser.

## Configuration

Create a `.env` file for API keys:

```env
OPENAI_API_KEY=your_key_here
OLLAMA_BASE_URL=http://localhost:11434  # Optional, defaults to localhost
```

## Output Format

```json
[
  {
    "assignee": "@sarah",
    "task": "finalize API spec",
    "due_date": "Friday",
    "priority": "high",
    "context": "mentioned in meeting notes"
  }
]
```

## License

MIT
