from flask import Flask, request, jsonify, send_from_directory
import os
import requests
import json

app = Flask(__name__, static_folder='.', static_url_path='')

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

def build_prompt(msg, detected_flags=None):
    flags_text = "None"
    if detected_flags:
        flags_text = json.dumps(detected_flags)

    return f"""
You are a calm, clear cognitive load reduction assistant. Analyze the message below and return ONLY a JSON object — no extra text, no markdown, no explanation.

Detected signal flags from a pre-check:
{flags_text}

Rules:
- risk_level: exactly one of "Safe", "Caution", or "High Risk"
- meaning: ONE sentence only. Max 12 words. Simple and calm. No technical words. No brand names.
- signals: max 3 items. Each must be 2-3 words only. Label the pattern, not the detail.
- next_steps: max 2 items. Always lead with the most protective action.
- If Safe: signals must be ["No suspicious signals"], next_steps should be short and reassuring
- Never use fear-based language. Never use jargon. Always be calm and supportive.
- Only include signals that are clearly present in the message. Do not infer.
- Use the detected signal flags only as support. Final judgment must still match the actual message.

Return ONLY this JSON:
{{
  "risk_level": "Safe | Caution | High Risk",
  "meaning": "one short sentence, max 12 words",
  "signals": ["signal 1", "signal 2", "signal 3"],
  "next_steps": ["step 1", "step 2"]
}}

Message: "{msg}"
"""

def extract_signals_with_azure(msg):
    if not all([AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT]):
        return None

    url = f"{AZURE_OPENAI_ENDPOINT}/openai/v1/chat/completions"

    system_prompt = """
You are a strict classifier.
Read the message and return ONLY valid JSON.
Do not explain.
Do not add markdown.
Return exactly these boolean fields:

{
  "urgency": true,
  "money_request": false,
  "impersonation": false,
  "suspicious_link": false,
  "threat_language": false
}
"""

    response = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "api-key": AZURE_OPENAI_API_KEY
        },
        json={
            "model": AZURE_OPENAI_DEPLOYMENT,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": msg}
            ],
            "temperature": 0,
            "max_tokens": 150
        },
        timeout=15
    )

    if response.status_code != 200:
        print("Azure API error:", response.status_code, response.text)
        return {
            "urgency": False,
            "money_request": False,
            "impersonation": False,
            "suspicious_link": False,
            "threat_language": False
        }

    result = response.json()
    print("Azure raw response:", json.dumps(result, indent=2))

    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    print("Azure content:", repr(content))

    if not content:
        print("Azure returned empty content")
        return None

    raw_text = content.strip().replace("```json", "").replace("```", "").strip()
    print("Azure raw_text:", repr(raw_text))

    try:
        parsed = json.loads(raw_text)
        print("Azure parsed JSON:", parsed)
        return {
            "urgency": bool(parsed.get("urgency", False)),
            "money_request": bool(parsed.get("money_request", False)),
            "impersonation": bool(parsed.get("impersonation", False)),
            "suspicious_link": bool(parsed.get("suspicious_link", False)),
            "threat_language": bool(parsed.get("threat_language", False)),
        }
    except Exception:
        return None

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    msg = data.get("message", "").strip()

    if not msg:
        return jsonify({"error": "Missing message"}), 400

    if not ANTHROPIC_API_KEY:
        return jsonify({"error": "Missing ANTHROPIC_API_KEY"}), 500

    detected_flags = None
    try:
        detected_flags = extract_signals_with_azure(msg)
    except Exception as e:
        print("Azure error:", e)
        detected_flags = None

    print("Detected flags:", detected_flags)

    prompt = build_prompt(msg, detected_flags)

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01"
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=30
    )

    if response.status_code != 200:
        print("Anthropic error:", response.status_code, response.text)
        return jsonify({"error": response.text}), response.status_code

    result = response.json()
    raw_text = result["content"][0]["text"].strip().replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw_text)
        return jsonify(parsed)
    except Exception:
        return jsonify({"error": "Model returned invalid JSON", "raw": raw_text}), 500

if __name__ == "__main__":
    app.run()
