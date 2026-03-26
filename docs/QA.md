# ClearStep — Q&A
### Design Decisions, Tradeoffs, and Judging Criteria

---

## Five Things to Remember

> **1. Product thesis**
> ClearStep treats cognitive overload as a safety problem, not a convenience problem.

> **2. Innovation**
> Use the model for reasoning, use code for guarantees.

> **3. Responsible AI**
> The model cannot produce a medically unsafe, misclassified, or structurally invalid output that reaches the user.

> **4. Security**
> Defences are enforced before, during, and after model execution — not through prompt rules alone.

> **5. Azure**
> 11 Azure services + Microsoft Foundry — each with a specific architectural role. Not decorative integrations.

---

## The Problem

**Who is this actually built for?**
People with ADHD, autism, dyslexia, low digital literacy, or anyone experiencing cognitive overload — which includes elderly users, non-English speakers, and people under stress. These users are disproportionately harmed by dense, unstructured information: medical instructions, government forms, scam messages, onboarding documents. They are also the users most likely to act on bad information because they struggle to parse good information.

**Why is cognitive overload a real problem, not just UX friction?**
Cognitive overload is not discomfort — it causes decision paralysis, missed deadlines, ignored medical instructions, and vulnerability to manipulation. For a neurodiverse user, a confusing government letter is not just annoying. It can mean a missed appeal, an unpaid bill, or a wrong medication dose. **ClearStep treats this as a safety problem, not a convenience problem.**

**Why does this problem need AI specifically?**
The volume and variety of overwhelming content is not reducible to templates. A medical discharge summary, a phishing email, and an onboarding pack require different decomposition logic, different safety rules, and different output structures. AI provides the reasoning layer. Azure provides the safety layer. The structure is enforced in code.

---

## The Solution

**Why two modes instead of one?**
The two problems are different in kind. "Is this safe?" requires risk assessment and signal detection. "Make it simple" requires extraction, sequencing, and cognitive pacing. Merging them into one flow would compromise both. Judges evaluate Mode 1 and Mode 2 as separate, complementary capabilities — not alternatives.

**Why not just use a chatbot?**
ClearStep is not a conversational assistant. It enforces structured output — separating actions, warnings, and context into fixed fields — so users can follow steps under pressure without interpretation. A chatbot response to "explain this medical instruction" returns a paragraph. ClearStep returns a validated, sequenced task list with warnings separated and key facts labelled. That difference matters for users who cannot parse prose under stress.

**Why one step at a time instead of showing all steps?**
Showing all steps at once recreates the overwhelm the user came to escape. The step engine delivers one action at a time, with a progress bar, undo, and optional reminders. For long documents, steps are batched in groups of five — the user completes a meaningful unit before the next set appears. This is a cognitive safety decision, not a UX preference.

**Why no timers or enforced deadlines?**
The challenge brief mentions "time-boxed tasks." ClearStep deliberately replaces imposed timers with optional calendar reminders. Countdown timers add urgency and anxiety for users already in cognitive overload. The reminder system is entirely user-initiated — they choose when, not the app. This is a direct response to how neurodiverse users experience enforced pacing.

**How does the reading level feature actually work?**
Three levels — Big, Normal, Small — control font size, line height, and AI output density. The model is prompted to write differently at each level: 8-word maximum meanings at Simple, 15-word at Detailed. The AI output changes, not just the display. Preferences persist across sessions via Azure Cosmos DB and are applied automatically on return.

---

## Safety and Responsible AI

**How do you prevent unsafe or misleading outputs?**
We use layered safeguards: Azure Content Safety and Prompt Shields run before any model call, and all outputs are validated in Python. Risk levels, medical safeguards, and structure are enforced in code — not left to the model.

Specifically: if the model returns `is_medical: false` for a medical input, a keyword backstop in the validator overrides it. If the model assigns `Safe` to content with real warnings, the validator upgrades the risk level. If the model puts a safety rule in the task list, the validator moves it to warnings. The model is the first line of reasoning. Python is the enforcement layer.

**How does crisis handling work?**
If Azure Content Safety detects self-harm content at severity 4, the pipeline short-circuits immediately. A hardcoded Python response is returned with the 988 Suicide and Crisis Lifeline. Claude is never called. This cannot be altered by prompt injection, model behaviour, or any input. It is the one response in the system that is completely outside model control.

**How does medical content get special treatment?**
When `is_medical` is true, the validator enforces: mandatory disclaimer always appended, warnings list cannot be empty, medical badge blocked from showing "CLEAR", leaked safety rules moved from tasks to warnings, dosing numbers and timing copied verbatim. These rules run in Python after every model call — the model cannot bypass them.

**How do you handle prompt injection?**
Three layers. Azure Prompt Shields detects jailbreak attempts at infrastructure level before any model call. The user message is delivered inside XML delimiters in the prompt — quote characters in user input cannot escape the prompt context. Schema validation rejects any response that breaks the expected structure. We tested 14+ attack vectors and all return High Risk or Caution, never compliance.

**How was security tested?**
The system was tested across 14+ attack vectors including prompt injection, schema manipulation, file upload abuse, and safety bypass attempts. **Defences are enforced before, during, and after model execution — not through prompt rules alone.** Results are documented in `docs/SECURITY.md`.

**How does this comply with the Microsoft RAI Standard v2?**
Every principle is mapped with specific implementation evidence in `docs/RESPONSIBLE_AI.md`. The short version: Accountability through Blob Storage logging and 22+ App Insights events. Reliability through hardcoded crisis responses and Python enforcement. Fairness through five accessibility palettes and automatic multilingual support. Transparency through the "Why this result?" panel. Privacy through zero message storage. Human Oversight through professional deference and no auto-advance in the step engine.

---

## Azure and Technical Depth

**Why 11 Azure services?**
Each service was chosen for a specific job it does better than the alternatives. Content Safety runs before any LLM — because a hardened infrastructure safety layer is more reliable than a prompt instruction. Azure OpenAI runs signal extraction because a cheap, fast, zero-temperature classifier is the right tool for binary flag detection. Azure AI Language handles multilingual support automatically so users don't need to configure anything. None of the services overlap. Full rationale: `docs/AZURE_SERVICES.md`.

**What is Microsoft Foundry's role?**
Foundry hosts the signal-classifier (gpt-4o-mini) used in Layer 2 of the pipeline. It provides controlled capacity, version management, and deployment-level monitoring for the model that extracts the five boolean risk flags injected into Claude's prompt. The separation of classification (Foundry/Azure OpenAI) from reasoning (Anthropic Claude) is a deliberate architectural decision — not all tasks need the same model.

**Why Anthropic Claude for the main reasoning layer?**
Claude provides better nuanced reasoning for medical and safety content than alternatives at this task. Temperature is set to 0 for determinism. The model is not the only safety layer — it is the reasoning layer. Safety is enforced before and after.

**Why vanilla HTML/CSS/JS instead of a framework?**
Zero dependency surface. Instant load on any device. No build step. No framework version vulnerabilities. For a tool used by people under cognitive stress on potentially slow connections or old devices, load time and reliability matter more than developer convenience.

**How does the file upload work safely?**
Six layers of validation before any text reaches the AI pipeline: extension check (blocked list + allowed list), MIME type validation per extension, byte-count size check, filename sanitisation via `secure_filename()`, Azure Content Safety screening, and Prompt Shield screening. Files are never stored — extracted in memory and discarded.

**What happens if an Azure service is down?**
Every Azure dependency is wrapped in try/except with graceful degradation. Key Vault falls back to environment variables. Content Safety skips and logs. Azure OpenAI skips — Claude runs without signal flags. Language detection defaults to English. Cosmos DB falls back to localStorage. The app never fails because a non-core service is unavailable.

---

## Innovation

**What's genuinely new here?**
Three things. First, a separation of trust (Mode 1) and comprehension (Mode 2) as complementary cognitive load problems — not combined into one chatbot flow. Second, medical instruction decomposition that expands frequency ("three times daily") into named task instances and enforces a complete safety validation pipeline in Python — not just in the prompt. Third, a layered safety architecture where the AI is the reasoning layer and Python is the enforcement layer — the model cannot produce an unsafe output that reaches the user.

**Why does the two-mode structure matter for this population?**
Neurodiverse users face two distinct threat types: manipulation (scams, pressure tactics, deceptive language) and complexity (instructions, forms, medical directions). Most tools address one. ClearStep addresses both — and keeps them separate because the reasoning, output structure, and safety rules for each are fundamentally different.

**How does the system adapt to the user?**
Accessibility preferences (colour palette and reading level) persist across sessions via Cosmos DB and apply automatically. Language detection makes multilingual support invisible — no selector, no configuration. The reading level setting changes how the AI writes, not just how the text displays. The system does not require the user to understand how it adapts — it just does.

---

## Judging Criteria

**Solution Performance — does it work?**
Yes. The live demo is deployed at Azure App Service. Both modes are functional. The AI pipeline, file upload, text-to-speech, calendar reminders, and preference persistence all work in production. The system degrades gracefully on Azure service failures.

**Innovation — new scenario or approach?**
Yes. The combination of trust assessment and cognitive load reduction in one system, the medical instruction decomposition pipeline, and the Python enforcement layer over model output are all novel approaches to this problem space.

**Responsible AI — adherence to Microsoft RAI Standard v2?**
Yes. Full mapping documented in `docs/RESPONSIBLE_AI.md`. Key differentiator: safety behaviour is enforced in code, not just prompted. **The model cannot produce a medically unsafe, misclassified, or structurally invalid output that reaches the user.**

**Azure Breadth — full advantage of the Azure platform?**
Yes. **11 Azure services + Microsoft Foundry, each with a specific architectural role. Not decorative integrations** — every service is active in the production pipeline and documented in `docs/AZURE_SERVICES.md`.

---

## Tradeoffs and Scope

**Why are some features marked as intentionally scoped?**
This is a focused hackathon MVP. Core functionality and safety systems are complete. Infrastructure-level features — distributed rate limiting, authenticated preferences, full-document content safety screening — are intentionally deferred to prioritise reliability and clarity in the demo. All deferred items are documented and can be upgraded without changes to the core system design.

**What is the hardest problem you solved?**
Medical instruction decomposition. The challenge: "Take 1 tablet three times daily with food for 7 days" must become three named task instances, a duration key item, and a warnings list — with the model's output validated and corrected in Python if it fails. This required layered enforcement: prompt rules, a frequency expansion validator, a keyword backstop for is_medical misclassification, and risk_level logic enforcement. Getting that pipeline consistent and correct was the hardest engineering problem in the build.

**What would you build next?**
Azure Computer Vision OCR is scaffolded and ready — pending endpoint validation once the resource is live. After that: session history for returning users, and a browser extension for "Is This Safe?" directly from email clients.

**What did you learn?**
That prompt rules are not enforcement. Every place we relied on the model to follow a rule, we eventually found a failure case. Every place we enforced the rule in Python, the failure case disappeared. The architecture lesson: **use the model for reasoning, use code for guarantees.**
