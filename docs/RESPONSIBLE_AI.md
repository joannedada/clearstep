# Responsible AI — ClearStep

This document maps ClearStep's implementation to the [Microsoft Responsible AI Standard v2](https://blogs.microsoft.com/wp-content/uploads/prod/sites/5/2022/06/Microsoft-Responsible-AI-Standard-v2-General-Requirements-3.pdf).

---

## Accountability

- All model outputs are schema-validated server-side before reaching the user — missing fields, wrong types, and empty task lists are caught and rejected before the user sees anything
- Every analysis is logged to Azure Blob Storage with risk level, mode, reading level, is_medical flag, and schema validation result — no raw message content stored
- Application Insights fires 11 custom telemetry events per request — including `leaked_warnings_detected`, `medical_disclaimer_enforced`, and `schema_validation_failed` — providing production evidence that safety features are firing, not just configured
- Microsoft Foundry provides deployment-level monitoring and metrics for the signal-classifier (gpt-4o-mini) used in Layer 2

---

## Reliability & Safety

- Azure AI Content Safety screens every input **before any LLM is invoked** — no prompt injection, adversarial input, or model behaviour can bypass it
- Severity 4 self-harm signals short-circuit the entire pipeline and return a hardcoded 988 Suicide and Crisis Lifeline response — Claude never sees the message
- Medical disclaimer enforced in Python code, not just the prompt. If the model omits it, `validate_response()` appends it automatically and logs `medical_disclaimer_enforced`
- Leaked safety rules in task lists (e.g. "Do not crush tablet") are detected by pattern matching and moved to the warnings array — users never see safety rules buried in action steps
- Input length capped at 2,000 chars (messages) and 5,000 chars (documents) — enforced server-side before any API call
- Prompt injection tested across 14 attack vectors — override attempts, jailbreaks, roleplay manipulation, indirect creative writing manipulation — all return High Risk or Caution, never compliance
- Fallback mode ensures the app never returns nothing — if the Anthropic API fails, client-side keyword scoring produces a degraded but functional result. A visible fallback indicator bar tells the user the AI was unavailable — the app never silently pretends keyword-matching is an AI response.
- **Rate limiting:** Flask-Limiter enforces 10 requests/minute on `/api/analyze` and 20/minute on `/api/calendar-link` — prevents API abuse, token burning, and denial-of-service from repeated requests
- **XSS sanitisation:** Every model output rendered via `innerHTML` is escaped through a dedicated `esc()` function before reaching the DOM — if a model ever returns HTML or script tags, they render as harmless text
- **Generic error responses:** Upstream provider errors (Anthropic, Azure) never reach the user. The backend returns a safe generic message; detailed errors are logged server-side only via Application Insights

---

## Fairness

- Accessibility is a core design requirement, not an add-on — every design decision is an accessibility decision
- Five colour palettes built for specific neurological needs: low-sensory (autism-friendly — zero red or orange), dyslexia-friendly (cream background, reduced glare), high-focus (ADHD — single accent, no competing colours), dark mode (photosensitivity), and calm default
- Three reading levels (Big / Normal / Small) control both font size/line height **and** AI output density — the model writes differently at each level, not just the font that changes
- No red or orange anywhere in the low-sensory palette — every alert uses the muted amber family only
- Medical content never receives a "CLEAR" badge regardless of model output — enforced in `renderResult()` in `index.html`
- **Multilingual equity:** Azure AI Language detects the input language on every request. If non-English, Claude is instructed to respond entirely in that language — all fields (meaning, warnings, tasks, signals, next_steps). Non-English speakers receive the same quality of response without any extra configuration or UI steps.
- **No enforced timers.** The challenge brief suggested time-boxed tasking. ClearStep deliberately does not implement timers — for users already experiencing cognitive overload, urgency adds anxiety, not support. Optional reminders replace enforced pacing.

---

## Transparency

- Every result includes a "Why this result?" explainability panel — signals explained in plain language, not technical labels
- Users are always told ClearStep is an AI tool and to verify with a professional — present on every single result
- Medical content always shows a persistent disclaimer bar across all three phases of the step-by-step flow — it never disappears when the user advances between steps
- The app never presents itself as a replacement for a doctor, lawyer, or financial advisor
- Reading level labels (Big / Normal / Small) are plain language — not technical jargon like "Lexile level"
- **Fallback transparency:** When the AI service is unavailable and the app falls back to client-side keyword scoring, a visible caution bar appears: *"AI unavailable — showing basic analysis only. Results may be less accurate."* The user always knows whether they received an AI response or a degraded fallback.

---

## Privacy

- No message content is stored anywhere — Blob Storage logs contain AI response JSON only (risk level, mode, flags), never the input text
- No user accounts, no login, no tracking, no ads
- **Cosmos DB preference storage:** Palette and reading level saved under an anonymous session ID generated in the browser using `Date.now()` + random suffix. The session ID is never linked to any identity, IP address, or message content. Only two values stored per session: palette name and reading level. Cosmos DB never receives any message content.

---

## Human Oversight

- Medical and legal content always defers to the original document and a real professional — enforced in the prompt and in the persistent disclaimer bar
- Crisis response directs users to human services (988 Lifeline) — ClearStep does not attempt to handle mental health crises itself. The model is never involved in crisis responses at severity 4.
- "Always consult a professional" is present in every medical result
- The step-by-step task engine never auto-advances — the user controls every transition. No decision is made for them.

---

## Prompt Injection Defense

- If a message attempts to override instructions or reveal system details, the model is instructed to flag it as High Risk or Caution — never to comply
- Tested across 14 attack vectors including: direct override attempts, roleplay framing, jailbreak patterns, indirect manipulation via creative writing requests, and multi-step social engineering
- System prompt is never exposed to the user
- Azure AI Content Safety runs before the prompt is ever constructed — adversarial inputs are caught before they reach any model
- **CORS policy:** Flask-CORS restricts `/api/analyze` to requests from the ClearStep domain only — third-party websites cannot call the API

---

## HAX Playbook Alignment

| HAX Guideline | ClearStep |
|---|---|
| Make clear what the system can and cannot do | Mode selection screen shows exactly two scopes. No dashboard, no menu, no ambiguity. |
| Make clear why the system did what it did | "Why this result?" panel on every output — signals explained in plain language |
| Support efficient invocation | Example chips let users try the tool without typing anything |
| Support efficient correction | "Check another" resets without losing mode selection. Undo available at every step. |
| Mitigate social biases | No user data stored, no demographic targeting, no personalisation beyond accessibility preferences |
| Support appropriate trust | Medical disclaimer, professional referral, and AI tool disclosure on all sensitive content |
| Reduce cognitive burden | One step at a time by default. No timers. No auto-advance. User controls all pacing. |
