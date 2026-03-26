# Contributions — ClearStep
This document reflects actual implementation based on the repository, system architecture, and deployed functionality.

---

## Leishka Pagan

**Primary Contributions:**

- Designed and implemented the full backend architecture (`app.py`) — Flask application, routing, request validation, error handling, and graceful degradation across all Azure services
- Built the complete 3-layer AI pipeline: Azure Content Safety → Prompt Shields → Azure AI Language → Azure OpenAI signal extraction → Anthropic Claude reasoning → Python validation
- Integrated Azure AI Content Safety — crisis screening (SelfHarm ≥ 4 → hardcoded 988 response) and Prompt Shields jailbreak detection, both running before any LLM is invoked
- Integrated Azure OpenAI via Microsoft Foundry — signal-classifier (gpt-4o-mini), extracting 5 boolean flags injected as Claude context
- Integrated Anthropic Claude — mode-specific prompt engineering, reading level adaptation, medical hardening rules, XML message delimiting for prompt injection mitigation
- Designed and implemented `validate_response()` — the Python enforcement layer for schema validation, medical safeguards, frequency expansion, leaked warning detection, is_medical keyword backstop, and risk_level logic enforcement
- Integrated Azure AI Language — automatic language detection, multilingual prompt injection, response in detected language across all fields
- Integrated Azure AI Speech — SSML-based TTS with 10-language Neural voice map, HTML stripping, rate limiting, audio never stored
- Integrated Azure Computer Vision — image OCR scaffolding (v3.2 Read API, two-step async pattern)
- Integrated Azure Blob Storage — timestamped audit log of every validated response, no message content stored
- Integrated Azure Cosmos DB — anonymous session-based preference persistence (palette + reading level)
- Integrated Azure Application Insights — 25 custom telemetry events across the full request lifecycle
- Integrated Azure Key Vault — secret management via DefaultAzureCredential and Managed Identity at startup
- Built the complete frontend (`index.html`) — both modes, 5-palette accessibility system, task engine state machine, batch delivery, TTS controls, file upload flow, calendar reminders, explainability panel, fallback handling, XSS sanitisation
- Designed and enforced a structured JSON output format with per-field rules across modes and reading levels
- Implemented fallback behaviour — keyword-scoring frontend fallback with visible indicator, safe medical holding state, never simulates AI decomposition
- Designed the file upload pipeline — extension and MIME validation, size check, filename sanitization, 3-layer content screening (Content Safety + Prompt Shields + cyber regex), in-memory extraction, nothing stored
- Implemented security hardening: CORS policy, rate limiting, XML prompt delimiters, `esc()` XSS sanitization on all innerHTML, 14 attack vectors tested
- Designed and authored all technical documentation: README, ARCHITECTURE, RESPONSIBLE_AI, SECURITY, AZURE_SERVICES, DESIGN_DECISIONS, CONTRIBUTING, QA, CONTRIBUTIONS
- Debugged and resolved: Azure endpoint mismatches, API authentication failures, environment configuration issues, frontend state machine bugs, validator logic gaps, prompt injection surface

**Ownership level:** Full-stack engineering, AI pipeline design and prompt engineering, safety enforcement architecture, accessibility design, security hardening, and all technical documentation

---

## Joanne Dada

**Primary Contributions:**

- Provisioned and configured all Azure cloud infrastructure
- Deployed and managed Azure App Service (Python 3.11, Gunicorn, GitHub Actions CI/CD)
- Set up Azure Key Vault and configured all secrets
- Provisioned Azure Blob Storage container and connection
- Provisioned Azure Cosmos DB database and container
- Deployed signal-classifier (gpt-4o-mini) through Microsoft Foundry in a controlled capacity, Standard deployment type
- Provisioned Azure Computer Vision resource
- Configured Azure-to-Azure Managed Identity authentication
- Managed cloud integration between all provisioned resources

**Ownership level:** Azure infrastructure, resource provisioning, cloud deployment, and Microsoft Foundry model deployment

---

## Fatima

**Primary Contributions:**

- Research support
- Accessibility input
- Feature ideation

---

## Notes

Roles are aligned with the implemented system, repository history, and deployed functionality to ensure accuracy during evaluation.
