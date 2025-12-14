#!/usr/bin/env python3
"""
Web interface for Meeting Action Item Extractor
"""

from flask import Flask, render_template_string, request, jsonify
from extract_actions import extract_action_items
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Meeting Action Item Extractor</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
        }
        textarea {
            width: 100%;
            min-height: 200px;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: monospace;
            font-size: 14px;
            box-sizing: border-box;
        }
        .controls {
            margin: 20px 0;
            display: flex;
            gap: 10px;
            align-items: center;
        }
        select, button {
            padding: 10px 20px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        button {
            background: #007bff;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background: #0056b3;
        }
        .results {
            margin-top: 30px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #f8f9fa;
            font-weight: 600;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .error {
            color: #dc3545;
            padding: 10px;
            background: #f8d7da;
            border-radius: 4px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📝 Meeting Action Item Extractor</h1>
        
        <form id="extractForm">
            <label for="notes"><strong>Paste meeting notes:</strong></label>
            <textarea id="notes" name="notes" placeholder="Example:&#10;@sarah to finalize API spec by Friday&#10;@dev team to investigate latency issues&#10;John will update the documentation by next week"></textarea>
            
            <div class="controls">
                <label for="provider">Provider:</label>
                <select id="provider" name="provider">
                    <option value="regex">Regex (Fast, No API)</option>
                    <option value="openai">OpenAI (Accurate)</option>
                    <option value="ollama">Ollama (Local)</option>
                </select>
                
                <button type="submit">Extract Action Items</button>
            </div>
        </form>
        
        <div class="loading" id="loading">Extracting action items...</div>
        <div id="error"></div>
        
        <div class="results" id="results"></div>
    </div>
    
    <script>
        document.getElementById('extractForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const notes = document.getElementById('notes').value;
            const provider = document.getElementById('provider').value;
            const loading = document.getElementById('loading');
            const error = document.getElementById('error');
            const results = document.getElementById('results');
            
            loading.style.display = 'block';
            error.innerHTML = '';
            results.innerHTML = '';
            
            try {
                const response = await fetch('/extract', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ notes, provider })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    error.innerHTML = `<div class="error">${data.error}</div>`;
                } else {
                    displayResults(data.actions);
                }
            } catch (err) {
                error.innerHTML = `<div class="error">Error: ${err.message}</div>`;
            } finally {
                loading.style.display = 'none';
            }
        });
        
        function displayResults(actions) {
            if (actions.length === 0) {
                document.getElementById('results').innerHTML = '<p>No action items found.</p>';
                return;
            }
            
            let html = '<h2>Extracted Action Items</h2><table><thead><tr><th>Assignee</th><th>Task</th><th>Due Date</th><th>Priority</th></tr></thead><tbody>';
            
            actions.forEach(action => {
                html += `<tr>
                    <td>${action.assignee || 'Unassigned'}</td>
                    <td>${action.task || 'N/A'}</td>
                    <td>${action.due_date || 'Not specified'}</td>
                    <td>${action.priority || 'medium'}</td>
                </tr>`;
            });
            
            html += '</tbody></table>';
            document.getElementById('results').innerHTML = html;
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/extract", methods=["POST"])
def extract():
    try:
        data = request.json
        notes = data.get("notes", "")
        provider = data.get("provider", "regex")
        
        if not notes:
            return jsonify({"error": "No notes provided"}), 400
        
        kwargs = {}
        if provider == "ollama":
            kwargs["base_url"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            kwargs["model"] = os.getenv("OLLAMA_MODEL", "llama2")
        
        actions = extract_action_items(notes, provider=provider, **kwargs)
        
        return jsonify({"actions": actions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
