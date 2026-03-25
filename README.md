# ClearStep
### Microsoft Innovation Challenge Hackathon — March 2026

> **ClearStep is an AI decision-support system that reduces cognitive overload** — helping users determine if something is safe to act on, and breaking overwhelming information into clear, calm, actionable steps. Built for neurodiverse users who need structure, not more noise.

**🔗 Live Demo:** [`https://clearstep-gqb6gpa9hzbdf5gy.canadaeast-01.azurewebsites.net`](https://clearstep-gqb6gpa9hzbdf5gy.canadaeast-01.azurewebsites.net)

---

## The Challenge We Solved

**Cognitive Load Reduction Assistant** — *An adaptive AI system that simplifies complex information for users experiencing cognitive overload.*

Neurodiverse individuals — including people with ADHD, autism, and dyslexia — can experience cognitive overload when interacting with dense documents, complex tasks, or unstructured information. The challenge called for an AI-powered assistant that could:

- Transform information into clear, structured, and personalized formats aligned to individual accessibility preferences
- Decompose complex instructions into step-by-step tasks
- Simplify and summarize documents at adjustable reading levels
- Provide focus support through reminders and contextual guidance
- Securely store user accessibility preferences and apply them across interactions
- Enforce responsible AI safeguards through calm, supportive, non-anxiety-inducing language
- Explain its simplification choices
- Evolve from a proof of concept into an operational, observable accessibility service

ClearStep addresses the core goals of this brief through structured simplification, adjustable reading levels, persistent preferences, explainability, and calm, safety-aware guidance. Rather than enforcing time-boxed execution, it uses low-pressure step sequencing with optional reminders — a deliberate choice to avoid adding urgency for users already experiencing cognitive overload. It also extends the brief with a second mode focused on a closely related need: helping users decide whether something feels safe to act on at all.

---

## The Solution — Two Modes, One Goal

ClearStep is a two-mode AI system designed to reduce cognitive overload in moments of uncertainty and overwhelm. Both modes use the same core approach: calm, structured guidance without adding pressure.

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
[Layer 2b] Azure OpenAI via Microsoft Foundry
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


---

## Azure Services

ClearStep uses 9 Azure services and Microsoft Foundry. Each was chosen for a specific reason — not to pad a list.

| Service | Purpose |
|---|---|
| **Azure App Service** | Hosts the Flask application — managed hosting with GitHub Actions CI/CD |
| **Azure AI Content Safety** | Crisis screening — runs before any LLM, hardcoded 988 response at severity 4 |
| **Azure OpenAI via Microsoft Foundry** | Signal extraction — 5 boolean flags injected into Claude's prompt as context |
| **Azure AI Language** | Language detection — non-English inputs trigger multilingual Claude response |
| **Azure Key Vault** | Secrets management — no keys in code or config files, Managed Identity auth |
| **Azure Blob Storage** | Audit log — AI response JSON stored per analysis, no raw message content |
| **Azure Application Insights** | Telemetry — 11 custom events prove safety features are firing in production |
| **Azure Cosmos DB** | Persistent preferences — palette and reading level stored anonymously per session |
| **Microsoft Foundry** | Model deployment platform — hosts the signal-classifier (gpt-4o-mini) used in Layer 2 of the AI pipeline |

Full breakdown — why each was chosen, how it's wired, and where in the code: [`docs/AZURE_SERVICES.md`](./docs/AZURE_SERVICES.md)


---

## Responsible AI — Microsoft RAI Standard v2 Mapping

| Principle | What ClearStep built |
|---|---|
| **Accountability** | Every analysis logged to Blob Storage. 11 App Insights events track system behaviour in production. |
| **Reliability & Safety** | Crisis response hardcoded — cannot be altered by model behaviour. Medical hardening enforced in Python. Schema validation rejects malformed output. Fallback ensures availability. Rate limiting prevents abuse. XSS sanitisation protects against model output injection. |
| **Fairness** | 5 accessibility palettes designed for specific neurological needs. Reading level changes AI output density. Language detection serves non-English speakers automatically. |
| **Transparency** | "Why this result?" panel on every output. AI tool disclaimer always visible. Medical content always defers to original document. Fallback mode shows visible indicator when AI is unavailable. |
| **Privacy** | No message content stored. Cosmos DB stores anonymous session ID + two preference values only. No accounts, no tracking. |
| **Human Oversight** | Medical and legal content always defers to real professionals. Crisis response sends users to human services (988). App never presents itself as a replacement. |
| **Inclusiveness** | Built for ADHD, dyslexia, autism, low digital literacy, elderly users, and non-English speakers. Every design decision is an accessibility decision. |

Full mapping: [`docs/RESPONSIBLE_AI.md`](./docs/RESPONSIBLE_AI.md)

---


---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | Vanilla HTML/CSS/JS — single file, no build step | Zero dependency surface, instant load, works on any device |
| Backend | Python Flask + Gunicorn | Lightweight, fast, native Azure deployment support |
| Primary AI | Anthropic Claude `claude-sonnet-4-20250514` | Best-in-class reasoning for medical and safety content |
| Signal extraction | Azure OpenAI (gpt-4o-mini) via Microsoft Foundry | Fast, cheap, zero-temperature classification — deployed and managed through Foundry |
| Crisis screening | Azure AI Content Safety | Hardened, purpose-built safety layer — not a prompt |
| Language detection | Azure AI Language | Automatic multilingual support without UI complexity |
| Secrets | Azure Key Vault + DefaultAzureCredential | Zero secrets in code or config files |
| Preferences | Azure Cosmos DB (NoSQL) | Low-latency anonymous preference storage with graceful fallback |
| Audit log | Azure Blob Storage | Immutable result log, no PII, structured for analysis |
| Observability | Azure Application Insights | 11 custom events, production safety monitoring |
| Deployment | Azure App Service + GitHub Actions CI/CD | Managed hosting, automatic deployments on push to main |
| Rate limiting | Flask-Limiter | Per-IP request caps — 10/min on analyze, 20/min on calendar |
| CORS | Flask-CORS | API locked to ClearStep domain — no third-party access |

---


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
    ├── RESPONSIBLE_AI.md   # Microsoft RAI Standard v2 mapping
    ├── SECURITY.md         # Application security hardening and test results
    ├── AZURE_SERVICES.md   # Every Azure integration explained
    └── DESIGN_DECISIONS.md # Why we built it the way we did
```

---

## Roadmap

- **Attachment support:** Drag-and-drop for screenshots, photos, and documents — for users who can't copy/paste. Requires Azure AI Vision (OCR) integration to extract text before the existing pipeline processes it.
- **Session history:** Optional anonymous history so users can revisit past analyses
- **Browser extension:** "Is This Safe?" directly from email clients

---

## Team

| Name | Role |
|---|---|
| **Leishka Pagan** | Project lead · Product strategy · System architecture · Backend development (app.py) · Frontend development (index.html) · All Azure integrations · Prompt engineering · Medical safety design · UX design · Accessibility design · Security pen testing (14 attack vectors) · Responsible AI design · Technical documentation |
| **Joanne Dada** | Azure infrastructure · Resource provisioning · Key Vault · Blob Storage · App Service deployment · Cosmos DB setup · Microsoft Foundry deployment · Cloud integration |
| **Fatima** | TBD |

---

**Hackathon Challenge:** Cognitive Load Reduction Assistant
**Deployed:** Azure App Service, Canada East
**Repo:** [github.com/joannedada/clearstep](https://github.com/joannedada/clearstep)
