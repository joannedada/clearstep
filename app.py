from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient
import logging
import os
import requests
import json
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.', static_url_path='')

# ── Application Insights telemetry ───────────────────────
logger = logging.getLogger(__name__)
insights_key = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
if insights_key:
    try:
        from opencensus.ext.azure.log_exporter import AzureLogHandler
        logger.addHandler(AzureLogHandler(connection_string=insights_key))
        logger.setLevel(logging.INFO)
        print("Application Insights telemetry enabled.")
    except Exception as e:
        print("Application Insights setup failed:", e)

# ── Secrets — env vars first, Key Vault overrides if available ────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
STORAGE_CONN_STR = os.getenv("STORAGE_CONN_STR")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_CONTENT_SAFETY_ENDPOINT = os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT")
AZURE_CONTENT_SAFETY_KEY = os.getenv("AZURE_CONTENT_SAFETY_KEY")

try:
    vault_url = "https://keyvault-clearstep.vault.azure.net/"
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=vault_url, credential=credential)
    ANTHROPIC_API_KEY = secret_client.get_secret("ANTHROPIC-API-KEY").value
    STORAGE_CONN_STR = secret_client.get_secret("STORAGE-CONN-STR").value
    AZURE_OPENAI_API_KEY = secret_client.get_secret("AZURE-OPENAI-API-KEY").value
    AZURE_OPENAI_DEPLOYMENT = secret_client.get_secret("AZURE-OPENAI-DEPLOYMENT").value
    AZURE_OPENAI_API_VERSION = secret_client.get_secret("AZURE-OPENAI-API-VERSION").value
    AZURE_OPENAI_ENDPOINT = secret_client.get_secret("AZURE-OPENAI-ENDPOINT").value
    print("Secrets loaded successfully from Key Vault.")
except Exception as e:
    print(f"Key Vault unavailable, using environment variables: {e}")

# ── Azure AI Content Safety screener ─────────────────────
def screen_with_content_safety(msg):
    if not all([AZURE_CONTENT_SAFETY_ENDPOINT, AZURE_CONTENT_SAFETY_KEY]):
        print("Content Safety not configured, skipping.")
        return None
    url = f"{AZURE_CONTENT_SAFETY_ENDPOINT}/contentsafety/text:analyze?api-version=2023-10-01"
    try:
        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Ocp-Apim-Subscription-Key": AZURE_CONTENT_SAFETY_KEY
            },
            json={
                "text": msg[:1000],
                "categories": ["Hate", "SelfHarm", "Sexual", "Violence"],
                "outputType": "FourSeverityLevels"
            },
            timeout=10
        )
        if response.status_code != 200:
            print("Content Safety error:", response.status_code, response.text)
            return None
        result = response.json()
        print("Content Safety result:", json.dumps(result, indent=2))
        return result
    except Exception as e:
        print("Content Safety exception:", e)
        return None

# ── Blob storage helper ─────────────────────────────────
def store_result_to_blob(parsed):
    if not STORAGE_CONN_STR:
        print("Blob storage not configured, skipping.")
        return
    try:
        blob_client = BlobServiceClient.from_connection_string(STORAGE_CONN_STR)
        container = blob_client.get_container_client("results")
        try:
            container.create_container()
        except Exception:
            pass
        from datetime import datetime, timezone
        filename = f"analysis_{datetime.now(timezone.utc).isoformat()}.json"
        container.upload_blob(name=filename, data=json.dumps(parsed), overwrite=True)
        print(f"Result saved to blob: {filename}")
    except Exception as e:
        print(f"Blob upload failed: {e}")

# ── Prompt builder ─────────────────────────────────────
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

# ── Azure OpenAI signal extractor ───────────────────────
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

# ── Routes ────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    msg = data.get("message", "").strip()
    if not msg:
        return jsonify({"error": "Missing message"}), 400
    # Input length guard — Fairness + Reliability
    if len(msg) > 2000:
        return jsonify({"error": "Message too long. Please limit to 2000 characters."}), 400
    if not ANTHROPIC_API_KEY:
        return jsonify({"error": "Missing ANTHROPIC_API_KEY"}), 500
    # Layer 1 — Azure AI Content Safety screening
    safety_result = screen_with_content_safety(msg)
    print("Content Safety screening complete:", safety_result is not None)
    # Layer 2 — Azure OpenAI signal extraction
    detected_flags = None
    try:
        detected_flags = extract_signals_with_azure(msg)
    except Exception as e:
        print("Azure error:", e)
        detected_flags = None
    print("Detected flags:", detected_flags)
    # Layer 3 — Anthropic final decision
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
        # Store result to Azure Blob Storage
        store_result_to_blob(parsed)
        # Application Insights custom telemetry — Accountability
        logger.info("ClearStep analysis complete", extra={
            "custom_dimensions": {
                "risk_level": parsed.get("risk_level"),
                "azure_flags_detected": str(detected_flags),
                "content_safety_ran": str(safety_result is not None)
            }
        })
        return jsonify(parsed)
    except Exception:
        return jsonify({"error": "Model returned invalid JSON", "raw": raw_text}), 500

if __name__ == "__main__":
    app.run()