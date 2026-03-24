# ClearStep
### Microsoft Innovation Challenge Hackathon — March 2026

> **ClearStep is an AI decision-support system that reduces cognitive overload — helping users determine if something is safe to act on, and breaking overwhelming information into clear, calm, actionable steps. Built for neurodiverse users who need structure, not more noise

**🔗 Live Demo:** [`https://clearstep-gqb6gpa9hzbdf5gy.canadaeast-01.azurewebsites.net`](https://clearstep-gqb6gpa9hzbdf5gy.canadaeast-01.azurewebsites.net)

---

## The Challenge We Solved

**Cognitive Load Reduction Assistant** — *An adaptive AI system that simplifies complex information for users experiencing cognitive overload.*

Neurodiverse individuals — Neurodiverse individuals — including people with ADHD, autism, and dyslexia — can experience cognitive overload when interacting with dense documents, complex tasks, or unstructured information. The challenge called for an AI-powered assistant that could:

- Transforms information into **clear, structured, and personalised formats** aligned to individual accessibility preferences
- Decomposes complex instructions into **step-by-step, time-boxed tasks**
- Simplifies and summarises documents at **adjustable reading levels**
- Provides **focus support** through reminders and contextual guidance
- **Securely stores user accessibility preferences** and applies them across interactions
- Enforces **responsible AI safeguards** — calm, supportive, non-anxiety-inducing language
- **Explains its simplification choices** (explainability)
- Evolve from proof of concept into an **operational, observable accessibility service**

ClearStep addresses the core goals of this brief through structured simplification, adjustable reading levels, persistent preferences, explainability, and calm, safety-aware guidance. Rather than enforcing time-boxed execution, it uses low-pressure step sequencing with optional reminders — a deliberate choice to avoid adding urgency for users already experiencing cognitive overload. It also extends the brief with a second mode focused on a closely related need: helping users decide whether something feels safe to act on at all.

---

## The Solution — Two Modes, One Goal

ClearStep is a two-mode AI system designed to reduce cognitive overload in moments of uncertainty and overwhelm. Both modes use the same core approach: **calm, structured guidance without adding pressure.**

### Mode 1 — Is This Safe?
Paste any message, email, link, or text that feels suspicious or confusing. ClearStep runs it through a 3-layer AI pipeline and returns:
- A risk level: **Safe**, **Caution**, or **High Risk**
- The specific warning signals detected (urgency pressure, impersonation, suspicious links, money requests, threat language)
- Exactly what to do next — two calm, actionable steps

### Mode 2 — Make It Simple
Paste anything overwhelming — medical instructions, government appeals, confusing work emails, complex onboarding tasks. ClearStep breaks it into:
- Safety warnings (things to never do) — separated from action steps
- Key facts (deadlines, requirements, conditions)
- One-at-a-time steps with progress bar, completion tracking, undo, and optional calendar reminders

---

## Intentional Design Philosophy

**Nothing in this application is accidental.** Every colour, every spacing decision, every word of copy, every interaction pattern was deliberately chosen with one goal: reduce cognitive load, not add to it.

### The Core Principle
> If the user feels panic, the system has failed.

ClearStep was designed around this constraint. Every design decision flows from it.

### Colour System — Designed for Safety, Not Aesthetics

The five colour palettes are not themes. They are accessibility tools.

Each palette overrides the **full set of CSS semantic variables** — not just background and text, but every state colour including safe, caution, danger, warning, and the medical bar. No hardcoded colour competes with the active profile anywhere in the codebase.

| Profile | Who it's for | Design decision |
|---|---|---|
| **Calm default** | General users | Off-white (#F7F7F2) reduces screen glare. Muted teal accent is non-aggressive. No pure white — pure white creates harsh contrast under stress. |
| **Low sensory** | Autism / sensory sensitivity | **Zero red or orange anywhere in the entire interface.** Every alert uses the muted amber family. Even "High Risk" renders in warm brown, not red. |
| **Dyslexia-friendly** | Dyslexia | Cream background (#F5F0E0) reduces the visual vibration that white backgrounds cause for dyslexic readers. Warm tones reduce eye strain on long reads. |
| **High focus** | ADHD | Single accent colour only. No competing visual elements. Amber for all alerts — one colour family, not three. Strips everything that pulls the eye away from the current task. |
| **Dark mode** | Photosensitivity / night use | Dark navy (#1C1F26), not pure black. Muted colour variants across all states — no blinding contrast shifts when alert colours appear. |

### Typography and Spacing

- **Bebas Neue** for display headings — high visual weight, low character count, fast to scan under stress
- **DM Sans** for body copy — optimised for readability at small sizes, low cognitive effort to parse
- **DM Mono** for labels and metadata — visually separates instructional text from UI chrome
- Line height scales with reading level: 2.0 (Big), 1.75 (Normal), 1.65 (Small) — not just font size
- Maximum content width 640px — prevents long line lengths that increase reading error rate
- A `fractalNoise` SVG texture overlay (opacity 0.025) is applied to the entire body — reduces the sterile feeling of a pure-colour screen and adds warmth without distraction

### Interaction Design — Slowing Down, Not Speeding Up

Most apps optimise for speed. ClearStep optimises for **deliberate decision-making**.

- The mode selection screen shows two options only — no menu, no dashboard, no choices before you've started
- Results never auto-scroll. The user controls pacing.
- Step-by-step mode shows **one step at a time by default** — not a list. Seeing 8 steps at once recreates the original overwhelm.
- Undo is available at every stage — last step, specific step, or all steps. No decision is permanent.
- Calm phrases appear as toasts during longer operations: *"No rush. You have time."* — the system models the calm it wants the user to feel.
- The topbar fades to 20% opacity on the mode selection screen — it exists but does not compete for attention until the user has made a choice.

### Emotional Design

- **No "you are being scammed" language.** Signals are labelled as patterns, not accusations.
- **No fear amplification.** High Risk means "take care", not "you are in danger right now."
- **No false certainty.** Every result includes "ClearStep is an AI tool. Always verify with a professional."
- **Crisis response bypasses the entire AI pipeline.** When Azure AI Content Safety detects severe self-harm (severity ≥ 4), no model is ever invoked. The 988 Lifeline response is hardcoded in Python — it cannot be altered by a prompt, a model hallucination, or an API failure.

---

## 3-Layer AI Pipeline

Every request passes through three layers in strict sequence. A failure at any layer is handled gracefully — the app never crashes.

```
User Input
    │
    ▼
[Layer 1] Azure AI Content Safety
          Screens for SelfHarm severity ≥ 4
          IF triggered → hardcoded 988 response returned immediately
          Claude is NEVER called
    │
    ▼
[Layer 2a] Azure AI Language
          Detects input language (ISO 639-1)
          Non-English → lang_instruction injected into Layer 3 prompt
    │
    ▼ (Is This Safe? mode only)
[Layer 2b] Azure OpenAI
          Extracts 5 boolean signal flags:
          urgency / money_request / impersonation / suspicious_link / threat_language
          Flags passed as context to Layer 3
    │
    ▼
[Layer 3] Anthropic Claude (claude-sonnet-4-20250514)
          Final risk assessment + step generation
          Mode-specific prompts, reading level rules, language instruction
    │
    ▼
[Validation] validate_response() — Python, server-side
          Schema check, medical hardening, leaked warning detection
          Malformed output rejected before user sees anything
    │
    ▼
[Storage] Azure Blob Storage
          AI response JSON logged — no raw message content
    │
    ▼
[Telemetry] Azure Application Insights
          11 custom events fired per request
```

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

## Medical Safety Hardening

Medical content receives a separate, stricter pipeline. All of the following are **enforced in Python** inside `validate_response()` — they cannot be bypassed by a model hallucination, prompt injection, or a model ignoring instructions.

- **Mandatory disclaimer:** If `"Reminder tool only — always follow your original prescription"` is missing from warnings, `validate_response()` appends it and fires `medical_disclaimer_enforced` to App Insights.
- **Leaked warning detection:** Tasks starting with `"do not"`, `"never "`, or `"avoid "` are moved from `tasks` to `warnings`. Safety rules cannot appear as action steps.
- **Hard fail on empty warnings:** If `is_medical` is `true` and warnings is empty, the endpoint returns 500. Nothing reaches the user.
- **Medical badge blocked:** Medical content never shows "CLEAR" regardless of model output. Enforced in `renderResult()` in `index.html`.
- **Persistent disclaimer bar:** The medical disclaimer banner stays visible across all three phases of the step-by-step flow — it is never cleared by phase transitions.
- **Dosing verbatim rule:** The prompt instructs Claude to never paraphrase dosing numbers, quantities, or timing.

---

## Schema Validation

`validate_response()` in `app.py` runs on every model response before the user sees anything:

- Required fields verified per mode — missing fields return 500, never a partial result
- `risk_level` casing normalised automatically (`"high risk"` → `"High Risk"`)
- All list fields coerced to clean string arrays — wrong types reset to empty list
- List caps enforced: tasks ≤ 10, warnings ≤ 6, key items ≤ 4, signals ≤ 3, next_steps ≤ 2
- Mode field isolation — safe mode strips `tasks`, `warnings`, `key_items`; simple mode strips `next_steps`

---

## Calendar Reminder System

Built entirely in Flask — no external service dependency, no OAuth, no account required.

`/api/calendar-link` receives the step text and time choice and returns pre-filled Google Calendar and Outlook URLs. The event title is `"ClearStep reminder: [step text]"`.

**Smart mode detection:** Tasks containing deadline keywords (`"60-day"`, `"expires"`, `"submit by"`, `"within"`, `"due"`) automatically open the date picker instead of quick time buttons. The system reads content and infers intent.

Time options: `1hour` (now + 60 min, rounded), `afternoon` (2:00 PM), `evening` (7:00 PM), `tomorrow` (8:00 AM next day), `custom` (user picks exact date + time).

---

## Fallback Mode

If the Anthropic API fails, the frontend `fallback()` function runs a local keyword scoring pass in JavaScript. Detects urgent language (+3), suspicious links (+2), gift card requests (+4), and medical keywords. Returns a structured result in the exact same schema as the API — the user always gets something, even if the server is unreachable.

---

## Security

- **14 prompt injection attack vectors tested** — override attempts, jailbreaks, roleplay manipulation, indirect creative writing manipulation. All return High Risk or Caution. The model is never instructed to comply.
- **Input length limits:** 2,000 chars for messages, 5,000 for documents — enforced server-side before any API call
- **No raw message content stored anywhere**
- **No API keys in any file** — Key Vault only, with env var fallback
- **Content Safety runs before any LLM** — adversarial inputs never reach the model pipeline

---

## Responsible AI — Microsoft RAI Standard v2 Mapping

| Principle | What ClearStep built |
|---|---|
| **Accountability** | Every analysis logged to Blob Storage. 11 App Insights events track system behaviour in production. |
| **Reliability & Safety** | Crisis response hardcoded — cannot be altered by model behaviour. Medical hardening enforced in Python. Schema validation rejects malformed output. Fallback ensures availability. |
| **Fairness** | 5 accessibility palettes designed for specific neurological needs. Reading level changes AI output density. Language detection serves non-English speakers automatically. |
| **Transparency** | "Why this result?" panel on every output. AI tool disclaimer always visible. Medical content always defers to original document. |
| **Privacy** | No message content stored. Cosmos DB stores anonymous session ID + two preference values only. No accounts, no tracking. |
| **Human Oversight** | Medical and legal content always defers to real professionals. Crisis response sends users to human services (988). App never presents itself as a replacement. |
| **Inclusiveness** | Built for ADHD, dyslexia, autism, low digital literacy, elderly users, and non-English speakers. Every design decision is an accessibility decision. |

Full mapping: [`docs/RESPONSIBLE_AI.md`](./docs/RESPONSIBLE_AI.md)

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | Vanilla HTML/CSS/JS — single file, no build step | Zero dependency surface, instant load, works on any device |
| Backend | Python Flask + Gunicorn | Lightweight, fast, native Azure deployment support |
| Primary AI | Anthropic Claude `claude-sonnet-4-20250514` | Best-in-class reasoning for medical and safety content |
| Signal extraction | Azure OpenAI (gpt-4o-mini) | Fast, cheap, zero-temperature classification — clean role separation |
| Crisis screening | Azure AI Content Safety | Hardened, purpose-built safety layer — not a prompt |
| Language detection | Azure AI Language | Automatic multilingual support without UI complexity |
| Secrets | Azure Key Vault + DefaultAzureCredential | Zero secrets in code or config files |
| Preferences | Azure Cosmos DB (NoSQL) | Low-latency anonymous preference storage with graceful fallback |
| Audit log | Azure Blob Storage | Immutable result log, no PII, structured for analysis |
| Observability | Azure Application Insights | 11 custom events, production safety monitoring |
| Deployment | Azure App Service + GitHub Actions CI/CD | Managed hosting, automatic deployments on push to main |

---

## Running Locally

```bash
git clone https://github.com/joannedada/clearstep
cd clearstep
pip install -r requirements.txt
```

Create a `.env` file — **never commit this:**
```
ANTHROPIC_API_KEY=your_key_here
```

```bash
python app.py
# Open http://localhost:5000
```

All Azure services degrade gracefully if not configured. Content Safety, Language detection, OpenAI extraction, Cosmos, and Blob all skip silently. The core experience works without Azure credentials.

---

## Project Structure

```
clearstep/
├── app.py                  # Flask backend — pipeline, Azure integrations, validation
├── index.html              # Complete frontend — modes, palettes, task engine, reminders
├── requirements.txt        # Python dependencies
├── .github/
│   └── workflows/          # Azure App Service CI/CD pipeline
└── docs/
    ├── ARCHITECTURE.md     # Full system design and request flow
    └── RESPONSIBLE_AI.md   # Microsoft RAI Standard v2 mapping
```

---

## Team

| Name | Role |
|---|---|
| **Leishka Pagan** | Project lead · Product strategy · System architecture · Backend development (app.py) · Frontend development (index.html) · Azure integrations · Prompt engineering · Medical safety design · UX design · Accessibility design · Security pen testing (14 attack vectors) · Responsible AI design |
| **Joanne Dada** | Azure infrastructure · Azure integrations · Resource provisioning · Key Vault · Blob Storage · App Service deployment · Cosmos DB setup |
| **Fatima** | TBD |

---

**Hackathon Challenge:** Cognitive Load Reduction Assistant
**Deployed:** Azure App Service, Canada East
**Repo:** [github.com/joannedada/clearstep](https://github.com/joannedada/clearstep)
