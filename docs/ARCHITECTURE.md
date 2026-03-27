# Architecture - ClearStep

## System Overview

ClearStep is a Flask web application deployed on Azure App Service. It processes user-submitted text, typed or uploaded from a file, through a multi-layer safety and AI pipeline and returns structured, validated JSON to a single-page frontend.

---

## Request Flow - Analyze

```
Browser (index.html)
        │
        │ POST /api/analyze { message, mode, reading_level }
        ▼
Flask (app.py)
        │
        ├─── [Layer 1] Azure AI Content Safety
        │         Screens for SelfHarm severity ≥ 4
        │         If triggered → hardcoded 988 response, Claude never called
        │
        ├─── [Layer 1b] Prompt Shields (Azure AI Content Safety)
        │         Detects jailbreak / prompt injection
        │         If triggered → hardcoded High Risk response, Claude never called
        │
        ├─── [Language] Azure AI Language
        │         Detects ISO 639-1 language code
        │         Non-English → lang_instruction injected into Layer 3 prompt
        │
        ├─── [Layer 2] Azure OpenAI via Microsoft Foundry (safe mode only)
        │         gpt-4o signal-classifier
        │         Returns 5 booleans: urgency / money_request / impersonation /
        │         suspicious_link / threat_language — injected as Claude context
        │         Skipped gracefully if unavailable
        │
        ├─── [Layer 3] Anthropic Claude (claude-sonnet-4-20250514)
        │         temperature: 0 - deterministic, same input → same result
        │         max_tokens: 2000 (simple mode) / 500 (safe mode)
        │         Final risk assessment and step generation
        │         Mode-specific prompts, reading level adaptation
        │         User message delivered inside XML delimiters - quote characters
        │           cannot escape prompt context, eliminates injection surface
        │         Extraction-only rule: tasks come from the document, never invented
        │         Medical hardening: conditional instructions are warnings, never tasks
        │         Crisis/shield responses return mode-appropriate JSON shape
        │
        ├─── Schema Validation — validate_response()
        │         Required fields check; risk_level normalisation
        │         List caps: warnings ≤ 6, signals ≤ 3, next_steps ≤ 2 (tasks: no count cap — frontend batches in groups of 5)
        │         Per-item word limits enforced in Python: signals ≤ 3, warnings ≤ 8, key_items ≤ 4
        │         tasks: prompt-guided to ≤ 8 words — NOT hard-truncated (truncation corrupts meaning)
        │         Frequency expansion: "three times daily" → 3 named instances (morning/afternoon/evening)
        │           Unmappable frequencies surfaced in key_items, not hard-errored
        │         is_medical keyword backstop: if model returns is_medical=false but medical
        │           keywords detected in output, overrides to true — all medical safeguards apply
        │         risk_level logic-enforced: if real warnings exist, Safe is invalid → upgraded to Caution
        │         Conditional medical instructions ("if you miss a dose", "unless") → warnings
        │         Tasks starting with "skip", "do not", "never", "avoid" → moved to warnings
        │         Medical disclaimer enforced in Python if model omits it
        │         Empty tasks list → 500, never returned to user
        │
        ├─── Azure Blob Storage — store_result_to_blob()
        │         Timestamped JSON log: risk_level, mode, is_medical, schema_valid
        │         No message content, no user ID
        │
        └─── Azure Application Insights
                  28 custom events fired across the request lifecycle
```

---

## Request Flow - File Upload

```
Browser (index.html)
        │
        │ POST /api/upload  multipart/form-data { file }
        │ Rate limited: 5/minute
        ▼
Flask (app.py)
        │
        ├─── Validation
        │         secure_filename() — strips path traversal, null bytes
        │         Extension: blocked list + allowed list
        │           Allowed: .txt .pdf .doc .docx
        │           Blocked: .js .py .sh .exe .zip .html .svg .xml and others
        │         Size: max 5 MB, reject empty
        │         MIME type: per-extension dict - no bypass for any type
        │           .txt  → text/plain (or text/* with empty allowed)
        │           .pdf  → application/pdf
        │           .docx → application/vnd.openxmlformats...
        │
        ├─── Format routing
        │         .doc            → rejected — "save as .docx" message returned
        │         .pdf            → pypdf page-by-page extraction
        │         .docx           → python-docx paragraph extraction
        │         .txt            → UTF-8 decode, latin-1 fallback
        │
        ├─── Content screening — screen_upload_content()
        │         Truncate to 5000 chars first
        │         Azure Content Safety (first 1000 chars):
        │           SelfHarm ≥ 4 → crisis block, 988 message
        │           Sexual ≥ 2   → blocked
        │           Violence ≥ 2 → blocked
        │           Hate ≥ 2     → blocked
        │         Azure Prompt Shields (first 1000 chars):
        │           attackDetected → blocked
        │         Cyber abuse regex (full 5000 chars):
        │           reverse shells, payloads, credential theft, etc. → blocked
        │
        └─── Return { text, filename }
                  Frontend puts text in textarea
                  User submits to /api/analyze as normal
```

---

## Request Flow - Text-to-Speech

```
Browser (index.html)
        │
        │ POST /api/tts { text, lang }
        │ Rate limited: 5/minute
        ▼
Flask (app.py)
        │
        ├─── Speech credentials check → 503 if not configured
        ├─── Strip HTML tags from text
        ├─── Max 500 characters check
        ├─── lang code → Neural voice (VOICE_MAP) + SSML locale (VOICE_LOCALE_MAP)
        ├─── SSML built with xml_escape
        ├─── Azure Speech REST API → MP3 binary
        └─── Return audio/mpeg — never stored
```

---

## Frontend Architecture

Single HTML file. No build step. No framework. Fully responsive on desktop and mobile.

**Task engine state machine:**
- Phase 1: overview (warnings, start button, batch notice if > 5 tasks)
- Phase 2: one step at a time (progress bar, reminder, mark done, undo)
- Phase 3: batch complete — "Continue to next N steps" if more remain
- Phase 4: all steps done

**Batch task delivery:** Frontend slices the full task list into batches of 5 (`TASK_BATCH_SIZE = 5`). After each batch completes, the user is offered the next; never are all tasks shown at once for long documents.

**Upload flow:** Client pre-checks extension + size → POST to `/api/upload` → text loaded into textarea. Error handling: `clearUpload()` runs first, then `showUploadError()` which prevents the flash-hide bug where' clearUpload () ' killed the error message.

**TTS:** Read-aloud buttons on meaning, next steps, warnings, and current step. Language passed from the API response—voice matches detected, one audio at a time.

**Palette engine:** 5 profiles via CSS custom properties. Each profile overrides the full semantic variable set, including `--mark-done` for profile-aware button colours.

---

## API Surface

| Endpoint | Method | Rate limit | Purpose |
|---|---|---|---|
| `/` | GET | — | Serves index.html |
| `/api/analyze` | POST | 10/min | Main AI pipeline |
| `/api/upload` | POST | 5/min | File extraction + content screening |
| `/api/tts` | POST | 5/min | Text-to-speech audio |
| `/api/calendar-link` | POST | 20/min | Calendar URL generation |
| `/api/preferences/<id>` | GET/POST | 30/min default | Preference read/write |

---

## Graceful Degradation

Every Azure dependency is wrapped in try/except. The app never fails because a non-core service is unavailable.

| Service | If unavailable |
|---|---|
| Azure Key Vault | Falls back to App Service env vars |
| Azure AI Content Safety | Screening skipped - analysis continues |
| Azure Prompt Shields | Skipped - analysis continues |
| Azure OpenAI / Foundry | Layer 2 skipped - Claude runs without signal flags |
| Azure AI Language | Returns `en` - analysis continues |
| Azure Blob Storage | Audit log skipped - analysis continues |
| Azure Application Insights | Telemetry skipped - analysis continues |
| Azure Cosmos DB | Falls back to localStorage silently |
| Azure AI Speech | TTS unavailable - 503 returned |

Full security documentation: `docs/SECURITY.md`
