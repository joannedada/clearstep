[AZURE_SERVICES.md](https://github.com/user-attachments/files/26266728/AZURE_SERVICES.md)
# Azure Services Used
### Every integration explained: why it was chosen, how the app uses it, and where to find it in the code.

For a quick overview of all services, see the [README](../README.md#azure-services).

---

## Azure Services - Every Integration Explained

### 1. Azure App Service
**Why it was chosen:** Managed PaaS hosting with native GitHub Actions CI/CD integration, Managed Identity support for Key Vault, and no server management overhead.

**How the app uses it:** Flask runs via Gunicorn on Python 3.11. Every push to `main` triggers automatic deployment via `.github/workflows/`. `DefaultAzureCredential` resolves to the App Service Managed Identity in production with no keys needed for Azure-to-Azure authentication.

**Code location:** `app.py` entrypoint, `requirements.txt`, `.github/workflows/`

---

### 2. Azure AI Content Safety
**Why it was chosen:** This is the most critical safety layer. It runs **before any LLM is invoked**, which means no prompt injection, adversarial input, or model behaviour can bypass it. For a tool used by vulnerable populations, a hardcoded safety net is non-negotiable.

**How the app uses it:**

*For message analysis:* `screen_with_content_safety()` sends every input to the Content Safety API using `FourSeverityLevels` output. It screens for Hate, Self-Harm, Sexual, and Violence. If `SelfHarm` severity reaches 4, the function returns a hardcoded Python dict — the 988 Suicide and Crisis Lifeline response. Claude never sees the message.

`screen_prompt_shield()` calls the Prompt Shields endpoint on the same Content Safety resource. This detects jailbreak and prompt injection attempts at the infrastructure level. If an attack is detected, the app returns a hardcoded High Risk response immediately. Claude never sees the message.

*For uploaded files:* `screen_upload_content()` runs a separate screening pass on all extracted file text before it is returned to the frontend. This inline check blocks:
- `SelfHarm` severity ≥ 4 → crisis block with 988 message
- `Sexual`, `Violence`, or `Hate` severity ≥ 2 → content blocked
- Prompt injection detected via Prompt Shields → blocked
- Cyber/malware keywords detected via regex → blocked

Azure API calls in the upload screener are bound to the first 1000 characters for latency reasons. The cyber regex scans the full 5000-character extraction.

**Code location:** `screen_with_content_safety()`, `screen_prompt_shield()`, `screen_upload_content()` in `app.py`

---

### 3. Azure OpenAI
**Why it was chosen:** Claude is powerful but expensive and slower as a pure binary classifier. Azure OpenAI (`gpt-4o-mini`) first runs a fast, cheap, zero-temperature classification pass. This cleanly separates roles - signal detection vs. nuanced reasoning - and improves accuracy.

**How the app uses it:** `extract_signals_with_azure()` sends the message and returns exactly 5 boolean fields: `urgency`, `money_request`, `impersonation`, `suspicious_link`, `threat_language`. These are serialized as JSON and injected into the Claude prompt as pre-processed context. Claude uses them as supporting evidence; the final judgment must match the actual message.

**Code location:** `extract_signals_with_azure()` — called in `analyze()` for `safe` mode only

---

### 4. Azure AI Language
**Why it was chosen:** ClearStep is built for accessibility. Limiting it to English excludes a significant portion of the neurodiverse, elderly, and low-literacy population it was designed to serve. Language detection makes multilingual support automatic, no language selector, no extra steps.

**How the app uses it:** `detect_language()` calls the `LanguageDetection` endpoint on the first 500 characters of every input. It returns an ISO 639-1 code and confidence score. If the language is not English, a `lang_instruction` string is injected into the Claude prompt. The `language_detected` telemetry event fires with language code and confidence.

**Code location:** `detect_language()`, called in `analyze()` after Content Safety, before Azure OpenAI

---

### 5. Azure AI Speech
**Why it was chosen:** Text-to-speech directly serves users with low literacy, vision impairments, and those who process spoken language better than written. It was also the lowest-friction way to add audio support without requiring any browser permissions or client-side audio processing.

**How the app uses it:** `/api/tts` accepts a text string and language code. It builds an SSML payload with a language-matched Neural voice and calls the Azure Speech REST API. The response is MP3 audio streamed directly back to the browser, no SDK dependency, no stored audio. Voices are selected per language from a 10-language map (English, Spanish, French, Portuguese, German, Chinese, Japanese, Korean, Arabic, Hindi). HTML tags are stripped before synthesis. Text is capped at 500 characters per request.

**Rate limit:** 5 requests per minute per IP.

**Graceful degradation:** If `AZURE_SPEECH_KEY` or `AZURE_SPEECH_REGION` are not configured, the endpoint returns HTTP 503 with `"Audio unavailable"`. The TTS buttons are simply not shown in the UI, and the rest of the app is unaffected.

**Code location:** `text_to_speech()`, `VOICE_MAP`, `VOICE_LOCALE_MAP`, `strip_html()` in `app.py`; `ttsSpeak()`, `ttsStop()`, `ttsShowButtons()` in `index.html`

---

### 6. Azure Key Vault
**Why it was chosen:** Zero secrets hardcoded or committed anywhere. Key Vault provides centralised, auditable, access-controlled secret storage with Managed Identity authentication. There were no API keys in any file.

**How the app uses it:** At startup, `SecretClient` connects to `keyvault-clearstep.vault.azure.net` and retrieves all secrets, overwriting environment variable values. Secrets retrieved include: Anthropic key, Azure OpenAI keys, Content Safety keys, Language keys, Cosmos keys, Blob connection string, Speech keys, and Vision keys. If Key Vault is unavailable, the `try/except` block falls back to App Service environment variables; a Key Vault outage never takes down the application.

**Key Vault secret names to provision:**
`ANTHROPIC-API-KEY`, `STORAGE-CONN-STR`, `AZURE-OPENAI-API-KEY`, `AZURE-OPENAI-DEPLOYMENT`, `AZURE-OPENAI-API-VERSION`, `AZURE-OPENAI-ENDPOINT`, `AZURE-CONTENT-SAFETY-ENDPOINT`, `AZURE-CONTENT-SAFETY-KEY`, `AZURE-LANGUAGE-ENDPOINT`, `AZURE-LANGUAGE-KEY`, `COSMOS-ENDPOINT`, `COSMOS-KEY`, `AZURE-SPEECH-KEY`, `AZURE-SPEECH-REGION`, `AZURE-VISION-ENDPOINT`, `AZURE-VISION-KEY`

**Note:** `APPLICATIONINSIGHTS_CONNECTION_STRING` is loaded from App Service environment variables only and not retrieved from Key Vault. This is intentional: Application Insights is initialised at logger setup before Key Vault is queried, so it must be available as an env var.

**Code location:** `SecretClient` block at the top of `app.py`, executed at startup

---

### 7. Azure Blob Storage
**Why it was chosen:** Audit trail and accountability. Every analysis result is stored for review. Examples include risk distributions, medical flag rates, and schema validation failures. Enables responsible AI monitoring. Raw message content is never stored.

**How the app uses it:** `store_result_to_blob()` uploads a timestamped JSON file to the `results` container after every successful analysis. The stored object contains `risk_level`, `mode`, `reading_level`, `is_medical`, `schema_valid`, and the full AI response. There is no message text, no session ID, no user-identifying information of any kind. Uploaded file content is never stored, and files are read in-memory and discarded after extraction.

**Code location:** `store_result_to_blob()`, called after `validate_response()` passes

---

### 8. Azure Application Insights
**Why it was chosen:** Production observability. Without telemetry, there is no evidence that safety features are firing. App Insights provides proof that responsible AI features are working in production, not just designed.

**How the app uses it:** `AzureLogHandler` is attached to the Python logger at startup. Custom events fire via `logger.info()` and `logger.warning()` throughout the request lifecycle.

| Event | When | What it proves |
|---|---|---|
| `analysis_started` | Every request starts | mode and reading level distribution |
| `task_decomposed` | Make It Simple completes | task counts, medical flag rate |
| `message_assessed` | Is This Safe? completes | risk level distribution |
| `analysis_complete` | Every successful analysis | full pipeline execution confirmed |
| `content_safety_flagged` | Crisis detected in message | safety layer is firing |
| `prompt_shield_flagged` | Jailbreak attempt detected in message | prompt shield is firing |
| `language_detected` | Every request | multilingual usage |
| `leaked_warnings_detected` | Model put safety rules in tasks | leaked warning correction is working |
| `medical_disclaimer_enforced` | Model omitted disclaimer | medical enforcement is firing |
| `is_medical_backstop_triggered` | Model returned is_medical=false but medical keywords detected | keyword backstop override fired |
| `frequency_expanded` | Stacked frequency task corrected into named instances | frequency enforcement working |
| `frequency_unmappable_kept` | Frequency could not be safely expanded - surfaced in key_items | graceful fallback for edge cases |
| `risk_level_upgraded` | Model returned Safe but real warnings exist - upgraded to Caution | risk_level logic enforcement firing |
| `schema_validation_failed` | Model returned bad structure | validation catching issues |
| `reminder_created` | Calendar reminder added | feature usage |
| `preferences_saved` | Palette/reading level changed | Cosmos DB writes |
| `preferences_loaded` | Returning user detected | Cosmos DB reads |
| `upload_processed` | File successfully extracted | upload pipeline working |
| `upload_blocked` | File blocked by content screening | upload safety firing |
| `upload_blocked_crisis` | SelfHarm ≥ 4 in uploaded file | upload crisis path working |
| `upload_blocked_harmful` | Sexual/Violence/Hate ≥ 2 in file | upload harm screening firing |
| `ocr_api_failed` | Azure Vision OCR API returned non-200 | OCR API failure monitoring |
| `ocr_extraction_failed` | OCR ran but returned no usable text | OCR extraction failure tracking |
| `pdf_extraction_failed` | PDF text extraction threw an exception | PDF pipeline failure monitoring |
| `docx_extraction_failed` | DOCX text extraction threw an exception | DOCX pipeline failure monitoring |
| `tts_generated` | Audio successfully synthesised | TTS feature usage |
| `tts_failed` | Speech API returned non-200 | TTS API failure monitoring |
| `tts_exception` | Speech request threw an exception | TTS exception tracking |

**Code location:** `logger.info()` and `logger.warning()` calls throughout `app.py`

---

### 9. Azure Cosmos DB
**Why it was chosen:** Accessibility preferences are personal. A dyslexic user who configures the cream background and large text should not have to reconfigure every visit. Cosmos DB makes ClearStep remember users across sessions and devices without storing any personal data.

**How the app uses it:** `get_cosmos_container()` initialises a `CosmosClient`. The `clearstep` database and `user_preferences` container are created on first use. Each document stores exactly: `session_id` (anonymous, browser-generated random string), `palette`, and `reading_level`. The session ID is generated in JavaScript using `Date.now()` + random suffix — never linked to any identity. If Cosmos is unavailable, it falls back to localStorage silently, and the user experience is unaffected.

**Code location:** `get_cosmos_container()`, `get_preferences()`, `save_preferences()` in `app.py`; `loadPreferences()`, `syncPreferencesToCloud()` in `index.html`

---

### 10. Microsoft Foundry
**Why it was chosen:** Foundry provides the managed deployment platform for Azure OpenAI models. Rather than calling a raw API endpoint, Foundry gives the team a dedicated deployment with controlled capacity, version management, rate limits, and monitoring; all in one place.

**How the app uses it:** Joanne deployed the `signal-classifier` endpoint through Foundry using `gpt-4o-mini`. This is the model called by `extract_signals_with_azure()` in Layer 2 of the pipeline. The deployment runs at 100,000 tokens/minute with a Standard deployment type. The endpoint URL and key are stored in Azure Key Vault and loaded at startup.

**Where in code:** `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_DEPLOYMENT` variables in `app.py`, both point to the Foundry-managed signal-classifier deployment.
