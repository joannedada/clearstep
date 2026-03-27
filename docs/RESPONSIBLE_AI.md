[RESPONSIBLE_AI.md](https://github.com/user-attachments/files/26267806/RESPONSIBLE_AI.md)
# Responsible AI - ClearStep

This document maps ClearStep's implementation to the [Microsoft Responsible AI Standard v2](https://blogs.microsoft.com/wp-content/uploads/prod/sites/5/2022/06/Microsoft-Responsible-AI-Standard-v2-General-Requirements-3.pdf).

---

## Accountability

- All model outputs are schema-validated server-side before reaching the user; missing fields, wrong types, and empty task lists are caught and rejected
- Every analysis is logged to Azure Blob Storage with risk level, mode, reading level, is_medical flag, and schema validation result — no raw message content stored
- Application Insights fires 12+ custom telemetry events per request, including `leaked_warnings_detected`, `medical_disclaimer_enforced`, `upload_blocked_crisis`, `upload_blocked_harmful`, and `schema_validation_failed`, providing production evidence that safety features are firing
- File upload blocks are logged separately with category and severity, proving the upload safety layer is active independently of the analysis pipeline
- Microsoft Foundry provides deployment-level monitoring and metrics for the signal-classifier (gpt-4o-mini) used in Layer 2

---

## Reliability & Safety

- Azure AI Content Safety screens every input **before any LLM is invoked**, no prompt injection, adversarial input, or model behaviour can bypass it
- **Prompt Shields:** Jailbreak detection runs as a second infrastructure-level gate after harm screening. Detected attacks return a hardcoded High Risk response; Claude never sees the message
- Severity 4 self-harm signals short-circuit the entire pipeline — hardcoded 988 Lifeline response, model never called
- **Upload content screening:** All uploaded file content is screened through Azure Content Safety (all 4 categories at lower thresholds), Prompt Shields, and a cyber abuse regex before any text is returned to the frontend or passed to the AI pipeline. Files are never stored — extracted in memory and discarded
- Medical disclaimer enforced in Python code. If the model omits it, `validate_response()` appends it automatically and logs `medical_disclaimer_enforced`
- Conditional medical instructions ("if you miss a dose", "if it is almost time", "unless", "in case") are classified as warnings, never tasks, and enforced in both the prompt and the Python validator
- Leaked safety rules in task lists (e.g., "Do not crush tablet", "Skip dose") were detected by pattern matching and moved to the warnings array; users never see safety rules as action steps
- **Crisis response is mode-aware:** safe mode returns `signals`/`next_steps`, simple mode returns `warnings`/`tasks`/`key_items` — the frontend never receives a mismatched JSON schema regardless of which mode triggered the crisis block
- **Extraction-only rule:** The model is explicitly instructed to extract only actual steps from the document, never to invent general advice or meta-instructions. Enforced in the prompt
- **Word limits enforced in Python:** signals ≤ 3 words, warnings ≤ 8 words, key_items ≤ 4 words — hard-enforced by `_trim_items()`. Tasks are prompt-guided to ≤ 8 words but are **not** hard-truncated in Python — truncating a task mid-thought is worse than a task running slightly long. If an action cannot fit in the word limit, the model is instructed to split it into 2 tasks.
- **Frequency expansion enforced in Python:** medication instructions like "three times daily" are expanded into 3 named task instances (morning/afternoon/evening) by `validate_response()`. The model is instructed to do this, and the validator enforces it; if the model stacks frequency into a single task, the validator corrects it.
- **is_medical keyword backstop:** if the model returns `is_medical: false` but medical keywords are detected in the output (tasks, warnings, key_items), the validator overrides to `true` and all medical safeguards apply. The model's classification cannot silently bypass medical enforcement.
- **risk_level logic-enforced:** if real warnings exist (excluding the mandatory medical disclaimer), `Safe` is not a valid risk_level, the validator upgrades to `Caution`. The model cannot assign Safe to content that carries actual safety rules.
- Input length capped at 2,000 chars (messages) and 5,000 chars (documents) — enforced server-side before any API call
- Prompt injection tested across 14 attack vectors — all return High Risk or Caution, never compliance
- Fallback mode ensures the app returns nothing. A visible indicator bar is always shown when fallback runs — the app never silently presents keyword-matching as AI analysis
- Rate limiting on all write endpoints prevents API abuse, token burning, and denial-of-service
- XSS sanitisation: every model output rendered via `innerHTML` escaped through `esc()` before DOM insertion
- Generic error responses: upstream provider errors logged server-side only, never returned to users

---

## Fairness

- Accessibility is a core design requirement, not an add-on — every design decision is an accessibility decision
- Five colour palettes built for specific neurological needs:
  - Low sensory (autism): zero red, orange, or amber — all alerts use the accent green-neutral family only
  - Dyslexia-friendly: cream background reduces visual vibration from white
  - High focus (ADHD): single accent colour, no competing visual elements — all alerts use one teal-blue family
  - Dark mode: muted variants across all states, no blinding contrast shifts
  - Calm default: off-white, non-aggressive teal accent
- Three reading levels (Big / Normal / Small) control font size, line height, **and** AI output density — the model writes differently at each level
- Medical content never receives a "CLEAR" badge regardless of model output — enforced in `renderResult()` in `index.html`
- **Multilingual equity:** Azure AI Language detects input language on every request. Non-English → Claude responds entirely in that language across all fields. No configuration or extra steps required from the user
- **No enforced timers.** For users in cognitive overload, urgency adds anxiety. Optional reminders replace enforced pacing
- **File attachment:** Supports users who cannot copy/paste — they can attach .txt, .pdf, .docx, or screenshots (.png, .jpg, .jpeg). Reduces the barrier for users with motor difficulties or low digital literacy
- **Mobile-first responsive design:** Full experience works on mobile browsers — both modes, all palettes, task engine, reminders, upload

---

## Transparency

- "Why this result?" explainability panel on every output — signals explained in plain language, not technical labels
- Users always told ClearStep is an AI tool and to verify with a professional, present on every result
- Medical content always shows a persistent disclaimer bar across all three phases of step-by-step flow — never cleared by phase transitions
- The app never presents itself as a replacement for a doctor, lawyer, or financial advisor
- Reading level labels (Big / Normal / Small) — plain language, not technical jargon
- **Fallback transparency:** When AI is unavailable and keyword scoring runs instead, a visible caution bar appears: "AI unavailable — showing basic analysis only." The user always knows which type of result they received
- **Batch task notice:** When a document produces more than 5 tasks, a notice appears before the user starts: "Long document — showing 5 steps at a time. More will follow." The user is never surprised by steps appearing later

---

## Privacy

- No message content is stored anywhere — Blob Storage logs contain AI response JSON only, never input text
- **Uploaded files are never stored.** Text is extracted in memory, and the file object is discarded immediately. Nothing is written to disk or blob storage
- No user accounts, no login, no tracking, no ads
- Cosmos DB stores only: anonymous session ID (browser-generated, never linked to identity) + palette + reading level. Cosmos never receives any message or file content

---

## Human Oversight

- Medical and legal content always defers to the original document and a real professional, enforced in a prompt and persistent disclaimer bar
- Crisis response directs users to human services (988 Lifeline), the model is never involved at severity ≥ 4
- "Always consult a professional" is present in every medical result
- Step-by-step task engine never auto-advances, user controls every transition, no decision is made for them
- **Batch task control:** When more than 5 tasks exist, the user explicitly chooses to load the next set, never auto-loaded

---

## Prompt Injection Defense

- Azure AI Content Safety screens input before any prompt is constructed
- Prompt Shields detects jailbreaks at the Azure infrastructure level before any LLM is called
- Prompt explicitly instructs Claude to flag override attempts as High Risk or Caution, never comply
- Source code protection: requests for system files or backend code are flagged as Caution and redirected to safe alternatives
- User message delivered inside XML delimiters in the prompt, quote characters in user input cannot escape the prompt context
- Schema validation rejects responses that don't match the expected JSON structure
- Per-item word limits in Python (`_trim_items()`) cap signals, warnings, and key_items reduces surface area for payloads hidden in label fields
- CORS policy: Flask-CORS restricts API to the ClearStep domain only

---

## HAX Playbook Alignment

| HAX Guideline | ClearStep |
|---|---|
| Make clear what the system can and cannot do | Mode selection shows exactly two scopes. No dashboard, no ambiguity. |
| Make clear why the system did what it did | "Why this result?" panel on every output |
| Support efficient invocation | Example chips let users try without typing. File attachment for users who can't copy/paste. |
| Support efficient correction | "Check another" resets cleanly. Undo is available at every step. Batch tasks allow continuation without restart. |
| Mitigate social biases | No user data stored, no demographic targeting, personalisation limited to accessibility preferences |
| Support appropriate trust | Medical disclaimer, professional referral, AI tool disclosure on all sensitive content |
| Reduce cognitive burden | One step at a time. No timers. No auto-advance. 5-task batches prevent overload on long documents. Word limits on every output field. |
