# ClearStep — Design Decisions
### Why we built it the way we did

This document captures the intentional design choices behind ClearStep — the reasoning behind the UI, the interaction patterns, the safety architecture, and the technical details that don't belong in a README but matter deeply to how the system works.

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
- **No enforced timers.** The challenge brief mentioned time-boxed tasks. ClearStep deliberately does not implement them. For many users already in cognitive overload, a countdown timer adds urgency and anxiety — the opposite of what the tool is for. Focus support is delivered through optional, user-initiated calendar reminders, not imposed deadlines.
- Calm phrases appear as toasts during longer operations: *"No rush. You have time."* — the system models the calm it wants the user to feel.
- The topbar fades to 20% opacity on the mode selection screen — it exists but does not compete for attention until the user has made a choice.

### Emotional Design

- **No "you are being scammed" language.** Signals are labelled as patterns, not accusations.
- **No fear amplification.** High Risk means "take care", not "you are in danger right now."
- **No false certainty.** Every result includes "ClearStep is an AI tool. Always verify with a professional."
- **Crisis response bypasses the entire AI pipeline.** When Azure AI Content Safety detects severe self-harm (severity ≥ 4), no model is ever invoked. The 988 Lifeline response is hardcoded in Python — it cannot be altered by a prompt, a model hallucination, or an API failure.

---


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


---

## Schema Validation

`validate_response()` in `app.py` runs on every model response before the user sees anything:

- Required fields verified per mode — missing fields return 500, never a partial result
- `risk_level` casing normalised automatically (`"high risk"` → `"High Risk"`)
- All list fields coerced to clean string arrays — wrong types reset to empty list
- List caps enforced: tasks ≤ 10, warnings ≤ 6, key items ≤ 4, signals ≤ 3, next_steps ≤ 2
- Mode field isolation — safe mode strips `tasks`, `warnings`, `key_items`; simple mode strips `next_steps`

---


---

## Calendar Reminder System

Built entirely in Flask — no external service dependency, no OAuth, no account required.

`/api/calendar-link` receives the step text and time choice and returns pre-filled Google Calendar and Outlook URLs. The event title is `"ClearStep reminder: [step text]"`.

**Smart mode detection:** Tasks containing deadline keywords (`"60-day"`, `"expires"`, `"submit by"`, `"within"`, `"due"`) automatically open the date picker instead of quick time buttons. The system reads content and infers intent.

Time options: `1hour` (now + 60 min, rounded), `afternoon` (2:00 PM), `evening` (7:00 PM), `tomorrow` (8:00 AM next day), `custom` (user picks exact date + time).

---


---

## Fallback Mode

If the Anthropic API fails, the frontend `fallback()` function runs a local keyword scoring pass in JavaScript. Detects urgent language (+3), suspicious links (+2), gift card requests (+4), and medical keywords. Returns a structured result in the exact same schema as the API — the user always gets something, even if the server is unreachable.

**Fallback transparency:** Every fallback result carries a `_fallback: true` flag. When `renderResult()` detects this flag, it displays a visible caution bar: *"AI unavailable — showing basic analysis only. Results may be less accurate."* The bar uses the caution palette and monospace font to visually distinguish it from normal results. This ensures the app never silently presents keyword-matching as AI analysis — a core transparency requirement.

---


---

## Security

- **14 prompt injection attack vectors tested** — override attempts, jailbreaks, roleplay manipulation, indirect creative writing manipulation. All return High Risk or Caution. The model is never instructed to comply.
- **Input length limits:** 2,000 chars for messages, 5,000 for documents — enforced server-side before any API call
- **No raw message content stored anywhere**
- **No API keys in any file** — Key Vault only, with env var fallback
- **Content Safety runs before any LLM** — adversarial inputs never reach the model pipeline
- **Rate limiting:** Flask-Limiter enforces per-IP request caps — 10/minute on `/api/analyze`, 20/minute on `/api/calendar-link`. Prevents token burning, credit abuse, and denial-of-service.
- **CORS restriction:** Flask-CORS locks all API endpoints to the ClearStep domain and localhost. No third-party website can call the backend.
- **XSS sanitisation:** A dedicated `esc()` function in `index.html` escapes all model-derived content before DOM insertion. Every `innerHTML` that renders signals, next_steps, tasks, key_items, or explainability text is wrapped in `esc()`. If a model returns `<script>` tags or HTML payloads, they render as plain text.
- **Generic error responses:** Upstream API errors (Anthropic, Azure OpenAI) are logged server-side with detail but never returned to the user. The frontend receives only `"Analysis service temporarily unavailable. Please try again."` — no internal URLs, auth details, or stack traces leak.
- **Fallback transparency:** When the AI is unavailable and client-side keyword scoring runs instead, a visible caution bar informs the user: *"AI unavailable — showing basic analysis only."* The app never silently pretends a keyword match is an AI result.

Full security documentation: [`docs/SECURITY.md`]

---

