# Architecture — ClearStep

## System Overview

ClearStep is a Flask web application deployed on Azure App Service. It processes user-submitted text through a three-layer AI pipeline and returns structured, validated JSON to a single-page frontend.

---

## Request Flow

```
Browser (index.html)
        │
        │ POST /api/analyze
        │ { message, mode, reading_level }
        ▼
Flask (app.py)
        │
        ├─── [Layer 1] Azure AI Content Safety
        │         • Screens for SelfHarm severity ≥ 4
        │         • If triggered: returns hardcoded 988 response immediately
        │         • No LLM is called
        │
        ├─── [Language] Azure AI Language
        │           Detects input language (ISO 639-1) — non-English triggers
        │           lang_instruction in Layer 3 prompt so Claude responds in
        │           the user's language
        │
        ├─── [Layer 2] Azure OpenAI via Microsoft Foundry  (safe mode only)
        │           signal-classifier deployment (gpt-4o-mini)
        │         • Extracts 5 boolean signals from the message:
        │           urgency, money_request, impersonation,
        │           suspicious_link, threat_language
        │         • These flags are passed to Layer 3 as context
        │         • If unavailable: skipped gracefully
        │
        ├─── [Layer 3] Anthropic Claude (claude-sonnet-4-20250514)
        │         • Final risk assessment and step generation
        │         • Mode-specific prompts (safe vs. simple)
        │         • Reading level adaptation (Big / Normal / Small)
        │         • Medical hardening rules in prompt
        │
        ├─── Schema Validation (validate_response)
        │         • Checks all required fields present
        │         • Normalises risk_level casing
        │         • Caps list lengths (tasks ≤ 10, warnings ≤ 6)
        │         • Detects leaked warnings in task lists → moves them
        │         • Enforces medical disclaimer if is_medical=True
        │         • Rejects response if tasks list is empty
        │
        ├─── Azure Blob Storage
        │         • Logs validated result (no message content)
        │
        └─── Azure Application Insights
                  • Logs: risk_level, mode, reading_level, is_medical,
                    azure_flags_detected, content_safety_ran, schema_valid
```

---

## Frontend Architecture

Single HTML file. No build step. No framework dependencies.

- **Two modes:** Is This Safe? / Make It Simple
- **Palette engine:** 5 accessible colour profiles via CSS custom properties
- **Reading level:** Three font size / line height presets
- **Task engine:** State machine — phase 1 (overview) → phase 2 (one step at a time) → phase 3 (complete)
- **Reminder system:** Calls `/api/calendar-link` → returns pre-filled Google + Outlook URLs, no OAuth required
- **Fallback:** If the API fails, client-side keyword scoring produces a degraded but functional result

---

## Azure Services

| Service | Role | Graceful degradation |
|---|---|---|
| Azure App Service | Hosts Flask app | N/A — core |
| Azure Key Vault | All secrets | Falls back to env vars |
| Azure AI Content Safety | Crisis detection | Skipped — analysis continues |
| Azure OpenAI (via Microsoft Foundry) | Signal extraction — signal-classifier deployment | Skipped — Claude runs without flags |
| Azure AI Language | Language detection for multilingual responses | Returns `en` fallback — analysis continues |
| Azure Blob Storage | Result audit log | Skipped — analysis continues |
| Azure Application Insights | Telemetry | Skipped — analysis continues |
| Azure Cosmos DB | Persistent user preferences (palette + reading level) | Falls back to localStorage silently |

Every Azure dependency is wrapped in try/except. The app never fails because a non-core service is unavailable.

---

## Security

- No API keys in code or committed files
- Key Vault accessed via `DefaultAzureCredential` (managed identity in production)
- Input length limits: 2,000 chars (messages), 5,000 chars (documents)
- No user PII stored anywhere
- Content Safety runs before any user input reaches the LLM
- **Rate limiting:** Flask-Limiter — 10 requests/minute on `/api/analyze`, 20/minute on `/api/calendar-link` (per IP, in-memory storage)
- **CORS:** Flask-CORS restricts API access to ClearStep's own domain and localhost only
- **XSS sanitisation:** All model output rendered via `innerHTML` is escaped through `esc()` before DOM insertion — signals, next_steps, tasks, key_items, and explainability items are all protected
- **Generic error responses:** Upstream provider errors logged server-side only; user receives safe generic message with HTTP 503
- **Fallback indicator:** When AI is unavailable and client-side fallback runs, a visible bar informs the user

Full security documentation: [`docs/SECURITY.md`](./docs/SECURITY.md)
