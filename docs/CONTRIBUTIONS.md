[CONTRIBUTIONS.md](https://github.com/user-attachments/files/26270336/CONTRIBUTIONS.md)
# Contributions — ClearStep
This document reflects actual implementation based on the repository, system architecture, and deployed functionality.

---

## Leishka Pagan

**Primary Contributions:**

- Designed and implemented the full backend architecture (`app.py`) — Flask application, routing, request validation, error handling, and graceful degradation across all Azure services
- Built the complete 3-layer AI pipeline: Azure Content Safety → Prompt Shields → Azure AI Language → Azure OpenAI signal extraction → Anthropic Claude reasoning → Python validation
- Integrated Azure AI Content Safety — crisis screening (SelfHarm ≥ 4 → hardcoded 988 response) and Prompt Shields jailbreak detection, both running before any LLM is invoked
- Integrated Azure OpenAI via Microsoft Foundry — signal-classifier (gpt-4o-mini) extracting 5 boolean flags injected as Claude context
- Integrated Anthropic Claude — mode-specific prompt engineering, reading level adaptation, medical hardening rules, XML message delimiting for prompt injection mitigation
- Designed and implemented `validate_response()` — the Python enforcement layer for schema validation, medical safeguards, frequency expansion, leaked warning detection, is_medical keyword backstop, and risk_level logic enforcement
- Integrated Azure AI Language — automatic language detection, multilingual prompt injection, response in detected language across all fields
- Integrated Azure AI Speech — SSML-based TTS with 10-language Neural voice map, HTML stripping, rate limiting, audio never stored
- Integrated Azure Blob Storage — timestamped audit log of every validated response, no message content stored
- Integrated Azure Cosmos DB — anonymous session-based preference persistence (palette + reading level)
- Integrated Azure Application Insights — 22+ custom telemetry events across the full request lifecycle
- Integrated Azure Key Vault — secret management via DefaultAzureCredential and Managed Identity at startup
- Built the complete frontend (`index.html`) — both modes, 5-palette accessibility system, task engine state machine, batch delivery, TTS controls, file upload flow, calendar reminders, explainability panel, fallback handling, XSS sanitisation
- Designed and enforced structured JSON output format with per-field rules across modes and reading levels
- Implemented fallback behaviour — keyword-scoring frontend fallback with visible indicator, safe medical holding state, never simulates AI decomposition
- Designed the file upload pipeline — extension and MIME validation, size check, filename sanitisation, 3-layer content screening (Content Safety + Prompt Shields + cyber regex), in-memory extraction, nothing stored
- Implemented security hardening: CORS policy, rate limiting, XML prompt delimiters, esc() XSS sanitisation on all innerHTML, 14 attack vectors tested
- Defined and documented all design decisions including: no timers (pacing as safety), no fake encouragement (clarity over positivity), word limits (cognitive safety), batch delivery, document upload rationale, colour profiles as cognitive accessibility tools
- Built interactive AI pipeline explorer (clearstep_pipeline.html) — fully offline, clickable layer-by-layer breakdown for demo use
- Built accessibility colour profiles showcase (clearstep_palettes.html) — live preview of all 5 palettes with real colours, rationale, and implementation details
- Built interactive RAI compliance map (clearstep_rai.html) — 6 Microsoft RAI Standard v2 principles each mapped to specific implementation, named component, and working code evidence
- Designed layout and architecture of the hackathon PowerPoint presentation — slide structure, content hierarchy, and visual system
- Authored all technical documentation: README, ARCHITECTURE, RESPONSIBLE_AI, SECURITY, AZURE_SERVICES, DESIGN_DECISIONS, CONTRIBUTING, QA, CONTRIBUTIONS
- Authored Innovation Studio submission page content — project description, tagline, keywords
- Authored requirements.txt — all Python dependencies with pinned versions
- Debugged and resolved: Azure endpoint mismatches, API authentication failures, environment configuration issues, frontend state machine bugs, validator logic gaps, prompt injection surface, frequency expansion reconstruction bug, is_medical misclassification, risk_level enforcement gap

**Ownership level:** Full-stack engineering, AI pipeline design and prompt engineering, safety enforcement architecture, accessibility design, security hardening, demo assets, hackathon submission content, and all technical documentation

---

## Joanne Obodoagwu

**Primary Contributions:**

- Provisioned and configured all Azure cloud infrastructure
- Deployed and managed Azure App Service (Python 3.11, Gunicorn, GitHub Actions CI/CD)
- Set up Azure Key Vault and configured all secrets
- Provisioned Azure Blob Storage container and connection
- Provisioned Azure Cosmos DB database and container
- Deployed signal-classifier (gpt-4o) through Microsoft Foundry — controlled capacity, Standard deployment type
- Configured Azure-to-Azure Managed Identity authentication
- Managed cloud integration between all provisioned resources
- Repository management and branch workflow
- Contributed to PowerPoint presentation build
- Video presentation logistics — coordinating hardware and OS setup across team members to ensure all contributors can participate in the video submission
- README review — human tone and readability pass to ensure documentation reads naturally

**Ownership level:** Azure infrastructure, resource provisioning, cloud deployment, Microsoft Foundry model deployment, repository management, video coordination, and documentation review

---

## Fatima Ahmed

**Primary Contributions:**

- Built the hackathon PowerPoint presentation using the defined slide structure, content hierarchy, and visual system
- Research support
- Accessibility input
- Feature ideation

---

## Notes

Roles are aligned with the implemented system, repository history, and deployed functionality to ensure accuracy during evaluation.
