# ClearStep — Azure Services
### Every integration explained: why it was chosen, how the app uses it, and where to find it in the code.

For a quick overview of all 9 services, see the [README](../README.md#azure-services).

---

## Azure Services — Every Integration Explained

### 1. Azure App Service
**Why it was chosen:** Managed PaaS hosting with native GitHub Actions CI/CD integration, Managed Identity support for Key Vault, and no server management overhead.

**How the app uses it:** Flask runs via Gunicorn on Python 3.11. Every push to `main` triggers automatic deployment via `.github/workflows/`. `DefaultAzureCredential` resolves to the App Service Managed Identity in production — no keys needed for Azure-to-Azure authentication.

**Code location:** `app.py` entrypoint, `requirements.txt`, `.github/workflows/`

---

### 2. Azure AI Content Safety
**Why it was chosen:** This is the most critical safety layer. It runs **before any LLM is invoked** — meaning no prompt injection, adversarial input, or model behaviour can bypass it. For a tool used by vulnerable populations, a hardcoded safety net is non-negotiable.

**How the app uses it:** `screen_with_content_safety()` sends every input to the Content Safety API using `FourSeverityLevels` output. It screens for Hate, SelfHarm, Sexual, and Violence. If `SelfHarm` severity reaches 4, the function returns a hardcoded Python dict — the 988 Suicide and Crisis Lifeline response. Claude never sees the message. This is enforced in Python code, not a prompt instruction.

**Code location:** `screen_with_content_safety()` — first call inside `analyze()`, before all other processing

---

### 3. Azure OpenAI
**Why it was chosen:** Claude is powerful but expensive and slower as a pure binary classifier. Azure OpenAI (`gpt-4o-mini`) runs a fast, cheap, zero-temperature classification pass first. This separates roles cleanly — signal detection vs. nuanced reasoning — and improves accuracy.

**How the app uses it:** `extract_signals_with_azure()` sends the message and returns exactly 5 boolean fields: `urgency`, `money_request`, `impersonation`, `suspicious_link`, `threat_language`. These are serialised as JSON and injected into the Claude prompt as pre-processed context. Claude uses them as supporting evidence — final judgment must match the actual message.

**Code location:** `extract_signals_with_azure()` — called in `analyze()` for `safe` mode only

---

### 4. Azure AI Language
**Why it was chosen:** ClearStep is built for accessibility. Limiting it to English excludes a significant portion of the neurodiverse, elderly, and low-literacy population it was designed to serve. Language detection makes multilingual support automatic — no language selector, no extra steps.

**How the app uses it:** `detect_language()` calls the `LanguageDetection` endpoint on the first 500 characters of every input. It returns an ISO 639-1 code and confidence score. If the language is not English, a `lang_instruction` string is injected into the Claude prompt: *"The user's message is in [language]. Respond in [language]. All fields must be in [language]."* The `language_detected` telemetry event fires with language code and confidence.

**Code location:** `detect_language()` — called in `analyze()` after Content Safety, before Azure OpenAI

---

### 5. Azure Key Vault
**Why it was chosen:** Zero secrets hardcoded or committed anywhere. Key Vault provides centralised, auditable, access-controlled secret storage with Managed Identity authentication — no API keys in any file.

**How the app uses it:** At startup, `SecretClient` connects to `keyvault-clearstep.vault.azure.net` and retrieves all secrets (Anthropic key, Azure OpenAI keys, Content Safety keys, Language keys, Cosmos keys, Blob connection string), overwriting environment variable values. If Key Vault is unavailable, the `try/except` block falls back to App Service environment variables — a Key Vault outage never takes down the application.

**Code location:** `SecretClient` block at the top of `app.py`, executed at startup

---

### 6. Azure Blob Storage
**Why it was chosen:** Audit trail and accountability. Every analysis result is stored for review — risk distributions, medical flag rates, schema validation failures. Enables responsible AI monitoring. Raw message content is never stored.

**How the app uses it:** `store_result_to_blob()` uploads a timestamped JSON file to the `results` container after every successful analysis. The stored object contains `risk_level`, `mode`, `reading_level`, `is_medical`, `schema_valid`, and the full AI response. No message text, no session ID, no user-identifying information of any kind.

**Code location:** `store_result_to_blob()` — called after `validate_response()` passes

---

### 7. Azure Application Insights
**Why it was chosen:** Production observability. Without telemetry, there is no evidence that safety features are firing. App Insights provides proof that responsible AI features are working in production — not just designed.

**How the app uses it:** `AzureLogHandler` is attached to the Python logger at startup. 11 custom events fire via `logger.info()` with `custom_dimensions` dictionaries throughout the request lifecycle.

| Event | When | What it proves |
|---|---|---|
| `session_created` | Every request starts | mode and reading level distribution |
| `task_decomposed` | Make It Simple completes | task counts, medical flag rate |
| `message_assessed` | Is This Safe? completes | risk level distribution |
| `content_safety_flagged` | Crisis detected | safety layer is firing |
| `language_detected` | Every request | multilingual usage |
| `leaked_warnings_detected` | Model put rules in tasks | model correction is working |
| `medical_disclaimer_enforced` | Model omitted disclaimer | enforcement is firing |
| `reminder_created` | Calendar reminder added | feature usage |
| `preferences_saved` | Palette/reading level changed | Cosmos DB writes |
| `preferences_loaded` | Returning user detected | Cosmos DB reads |
| `analysis_complete` | Every successful analysis | full pipeline execution confirmed |

**Code location:** `logger.info()` calls throughout `analyze()`, `detect_language()`, `validate_response()`, `get_preferences()`, `save_preferences()`, `calendar_link()`

---

### 8. Azure Cosmos DB
**Why it was chosen:** Accessibility preferences are personal. A dyslexic user who configures the cream background and large text should not have to reconfigure every visit. Cosmos DB makes ClearStep remember users across sessions and devices — without storing any personal data.

**How the app uses it:** `get_cosmos_container()` initialises a `CosmosClient`. The `clearstep` database and `user_preferences` container are created on first use. Each document stores exactly: `session_id` (anonymous, browser-generated random string), `palette`, and `reading_level`. The session ID is generated in JavaScript using `Date.now()` + random suffix — never linked to any identity. `loadPreferences()` calls `GET /api/preferences/<session_id>` on every page load. Every palette or reading level change calls `POST /api/preferences/<session_id>`. If Cosmos is unavailable, falls back to localStorage silently — user experience unaffected.

**Code location:** `get_cosmos_container()`, `get_preferences()`, `save_preferences()` in `app.py`; `loadPreferences()`, `syncPreferencesToCloud()` in `index.html`

---


---
---

### 9. Microsoft Foundry
**Why it was chosen:** Foundry provides the managed deployment platform for Azure OpenAI models. Rather than calling a raw API endpoint, Foundry gives the team a dedicated deployment with controlled capacity, version management, rate limits, and monitoring — all in one place.

**How the app uses it:** Deployed the `signal-classifier` endpoint through Foundry using `gpt-4o-mini`. This is the model called by `extract_signals_with_azure()` in Layer 2 of the pipeline. The deployment runs at 100,000 tokens/minute with a Standard deployment type. The endpoint URL and key are stored in Azure Key Vault and loaded at startup.

**Where in code:** `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_DEPLOYMENT` variables in `app.py` — both point to the Foundry-managed signal-classifier deployment.
