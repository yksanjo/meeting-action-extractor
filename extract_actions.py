#!/usr/bin/env python3
"""
Meeting Note → Action Item Extractor

Extracts action items, assignees, and deadlines from meeting notes.
Supports multiple extraction methods: LLM (OpenAI/Ollama) and rule-based.
"""

import re
import json
import argparse
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def extract_with_regex(text: str) -> List[Dict]:
    """Extract action items using regex patterns."""
    actions = []
    
    # Pattern for @mentions with tasks
    mention_pattern = r'@(\w+)\s+(?:to|will|should)\s+(.+?)(?:by|before|until|due)\s+(\w+\s*\d*,?\s*\d*|today|tomorrow|next\s+\w+|Friday|Monday|etc\.?)'
    
    # Pattern for names followed by tasks
    name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:will|should|to)\s+(.+?)(?:by|before|until|due)\s+(\w+\s*\d*,?\s*\d*|today|tomorrow|next\s+\w+|Friday|Monday|etc\.?)'
    
    # Pattern for simple task lists
    task_pattern = r'[-•*]\s*(.+?)(?:by|before|until|due)\s+(\w+\s*\d*,?\s*\d*|today|tomorrow|next\s+\w+|Friday|Monday|etc\.?)'
    
    for pattern in [mention_pattern, name_pattern, task_pattern]:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            if len(match.groups()) >= 3:
                assignee = match.group(1) if match.group(1) else "Unassigned"
                task = match.group(2).strip()
                due_date = match.group(3).strip()
            elif len(match.groups()) == 2:
                assignee = "Unassigned"
                task = match.group(1).strip()
                due_date = match.group(2).strip()
            else:
                continue
                
            actions.append({
                "assignee": assignee,
                "task": task,
                "due_date": due_date,
                "priority": "medium",
                "context": "extracted from meeting notes"
            })
    
    return actions


def extract_with_openai(text: str, api_key: Optional[str] = None) -> List[Dict]:
    """Extract action items using OpenAI API."""
    if not OPENAI_AVAILABLE:
        raise ImportError("openai package not installed. Install with: pip install openai")
    
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment or provided")
    
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Extract action items from the following meeting notes. Return a JSON array of objects with:
- assignee: person responsible (extract @mentions, names, or "Unassigned")
- task: the action item description
- due_date: deadline if mentioned (or "Not specified")
- priority: "high", "medium", or "low" based on urgency
- context: brief context if available

Meeting notes:
{text}

Return ONLY valid JSON array, no markdown formatting."""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts action items from meeting notes. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        result = re.sub(r'```json\n?', '', result)
        result = re.sub(r'```\n?', '', result)
        
        actions = json.loads(result)
        return actions if isinstance(actions, list) else [actions]
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        print("Falling back to regex extraction...")
        return extract_with_regex(text)


def extract_with_ollama(text: str, base_url: str = "http://localhost:11434", model: str = "llama2") -> List[Dict]:
    """Extract action items using Ollama (local LLM)."""
    if not REQUESTS_AVAILABLE:
        raise ImportError("requests package not installed. Install with: pip install requests")
    
    prompt = f"""Extract action items from the following meeting notes. Return a JSON array of objects with:
- assignee: person responsible (extract @mentions, names, or "Unassigned")
- task: the action item description
- due_date: deadline if mentioned (or "Not specified")
- priority: "high", "medium", or "low" based on urgency
- context: brief context if available

Meeting notes:
{text}

Return ONLY valid JSON array, no markdown formatting."""

    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            },
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json().get("response", "")
        # Remove markdown code blocks if present
        result = re.sub(r'```json\n?', '', result)
        result = re.sub(r'```\n?', '', result)
        
        actions = json.loads(result)
        return actions if isinstance(actions, list) else [actions]
    except Exception as e:
        print(f"Error with Ollama API: {e}")
        print("Falling back to regex extraction...")
        return extract_with_regex(text)


def extract_action_items(text: str, provider: str = "regex", **kwargs) -> List[Dict]:
    """
    Extract action items from meeting notes.
    
    Args:
        text: Meeting notes text
        provider: "regex", "openai", or "ollama"
        **kwargs: Additional arguments for specific providers
    
    Returns:
        List of action item dictionaries
    """
    if provider == "openai":
        return extract_with_openai(text, kwargs.get("api_key"))
    elif provider == "ollama":
        return extract_with_ollama(
            text,
            kwargs.get("base_url", "http://localhost:11434"),
            kwargs.get("model", "llama2")
        )
    else:
        return extract_with_regex(text)


def save_output(actions: List[Dict], output_path: str, format: str = "json"):
    """Save extracted actions to file."""
    output_path = Path(output_path)
    
    if format == "json":
        with open(output_path, "w") as f:
            json.dump(actions, f, indent=2)
    
    elif format == "csv":
        import pandas as pd
        df = pd.DataFrame(actions)
        df.to_csv(output_path, index=False)
    
    elif format == "md":
        with open(output_path, "w") as f:
            f.write("# Action Items\n\n")
            f.write("| Assignee | Task | Due Date | Priority |\n")
            f.write("|----------|------|----------|----------|\n")
            for action in actions:
                f.write(f"| {action.get('assignee', 'N/A')} | {action.get('task', 'N/A')} | "
                       f"{action.get('due_date', 'N/A')} | {action.get('priority', 'N/A')} |\n")
    
    print(f"Saved {len(actions)} action items to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Extract action items from meeting notes")
    parser.add_argument("--input", "-i", required=True, help="Input file with meeting notes")
    parser.add_argument("--output", "-o", required=True, help="Output file path")
    parser.add_argument("--provider", "-p", default="regex", choices=["regex", "openai", "ollama"],
                       help="Extraction provider (default: regex)")
    parser.add_argument("--format", "-f", default="json", choices=["json", "csv", "md"],
                       help="Output format (default: json)")
    parser.add_argument("--ollama-url", default="http://localhost:11434",
                       help="Ollama base URL (default: http://localhost:11434)")
    parser.add_argument("--ollama-model", default="llama2",
                       help="Ollama model name (default: llama2)")
    
    args = parser.parse_args()
    
    # Read input
    with open(args.input, "r") as f:
        text = f.read()
    
    # Extract actions
    print(f"Extracting action items using {args.provider}...")
    kwargs = {}
    if args.provider == "ollama":
        kwargs["base_url"] = args.ollama_url
        kwargs["model"] = args.ollama_model
    
    actions = extract_action_items(text, provider=args.provider, **kwargs)
    
    # Save output
    output_format = args.format or Path(args.output).suffix[1:] or "json"
    save_output(actions, args.output, format=output_format)
    
    print(f"\nExtracted {len(actions)} action items:")
    for i, action in enumerate(actions, 1):
        print(f"{i}. [{action.get('assignee', 'Unassigned')}] {action.get('task', 'N/A')} "
              f"(Due: {action.get('due_date', 'Not specified')})")


if __name__ == "__main__":
    main()
