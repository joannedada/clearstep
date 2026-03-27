# ClearStep's Build Story

> *Microsoft Innovation Challenge, March 2026*
> *"If the user feels panic, the system has failed."*

<br>

## How This Started

I came into this challenge on March 16th excited and completely lost. I wanted to learn. I wanted to do cybersecurity work: penetration testing a new product, finding vulnerabilities, hardening something someone else built. That was the plan. Leading a team and building a full-stack AI application from scratch was not the plan.

The first two days I spent reading documentation, reading the challenge brief, trying to understand what was actually being asked. By the 18th I had finally found someone to join, a senior engineer I desperately needed. But he had one condition: he would not start building unless the team was bigger and the responsibilities were spread out. That told me he had real experience and knew what he was signing up for. It also meant I was back to searching.

What followed was the hardest part of the whole experience. Not the code, not the bugs, not the sleepless nights. Finding teammates. I searched through platforms, chats, and channels for days. By March 20th I finally had a third person. The team felt complete. Then at 8PM that same night, the developer left. Time constraints. The team was back to two.

Joanne, who had joined as cloud and infrastructure, mentioned someone else who might be able to help. Fatima joined the next day. Three members again, but without a developer, and with the challenge already a third of the way through.

I made a decision. I would lead. I would build it myself.

I had no prior experience building a production Flask application. I had never integrated ten Azure services. I had never done prompt engineering under a safety constraint. I chose to do all of it because the alternative was letting the project die, and that was not something I was willing to do.

<br>

---

## What We Built and When

### March 20 at Night

The team structure collapsed at 8PM. By the time I made the decision to take over development, it was late. I started from scratch: Flask app, project structure, first working route. The first few hours were spent reading documentation while simultaneously writing code. This is not a comfortable way to learn but it is an effective one.

### March 21–22: The Foundation

Core pipeline took shape. Azure AI Content Safety integration came first. The safety layer had to exist before anything else. Prompt Shields followed. Then Claude. The first time the full pipeline ran end to end and returned a structured JSON response, I understood why people build things.

The validator came next. `validate_response()` started simple and grew into the most important function in the codebase. Every edge case I discovered went into the validator as a hard enforcement rule: model misclassifying medical content, risk_level returning Safe when warnings existed, frequency stacked into a single task. By the end it was handling 12 distinct failure modes independently of the model.

### March 22–24: The Hard Days

File upload was the most complex feature. Not the extraction, which was straightforward with pypdf and python-docx. The security layer around it was the problem. Extension validation, MIME type validation, size validation that couldn't be spoofed via headers, filename sanitisation, then three layers of content screening before any text was returned. Each layer uncovered a new edge case. Each edge case became a test.

The frontend came entirely from scratch. No framework. No build step. Vanilla HTML, CSS, and JavaScript in a single file. The task engine state machine was the hardest frontend problem: four phases, batch delivery, undo at every step, progress tracking. Getting the phase transitions right without introducing state bugs took longer than I expected.

TTS integration happened at 2AM. I remember it because the first time it spoke back in the correct language without any configuration, I sat there for a minute.

### March 25–26: Security and Documentation

Penetration testing against the live deployed application. I came into this challenge wanting to do security work, and I got to do it. Just on something I built myself. Fourteen attack vectors tested live against the production URL. Every one blocked. The telemetry in App Insights confirmed which safety layers fired on which inputs. The evidence is in the logs, not just in the code.

Documentation sprint followed. README, ARCHITECTURE, RESPONSIBLE_AI, SECURITY, AZURE_SERVICES, DESIGN_DECISIONS, CONTRIBUTING, CONTRIBUTIONS. Each one written to be accurate to the actual implementation, not to what we intended to build. If a document said something worked, it worked. No aspirational writing.

### March 27: Submission Day

Presentation, demo video, final deployment verification, submission. The app was live. The pipeline was working. The security held.

<br>

---

## The Errors We Hit

Some of these cost hours. All of them taught something. This is not a cleaned-up version. This is what actually happened.

<br>

**`IndentationError` at line 608**

Gunicorn failed to boot on three consecutive deployments. Each crashed on the same line. The Azure log stream showed the exact line number immediately. I used Ctrl+F to jump straight there. The indentation was off by one level, something that happens when you are editing a 1,400-line file late at night. The fix took thirty seconds. Finding it without the log would have taken much longer. **Lesson: trust the Azure logs. They are fast and specific.**

<br>

**`ModuleNotFoundError: No module named 'flask_limiter'`**

Added Flask-Limiter for rate limiting. Deployed. Crashed. Deployed again. Crashed again. Third time. Still crashed. The same error every single time. The module was never added to `requirements.txt`. Azure was building the same broken virtual environment on every deploy because nothing in the build pipeline had changed. Added one line. The next deployment ran clean. This stings because it was obvious in retrospect and cost multiple deploy cycles of several minutes each.

<br>

**`selectMode is not defined` — JavaScript**

The live production app was completely broken. The root cause was a file sync problem: the deployed `index.html` and the local `index.html` were different versions. The function `selectMode` existed in one but not the other. It only surfaced in production because local testing used the correct file. Fix was uploading the right file. **Lesson: "works locally" means nothing if the deployed file is different.** After this, every deployment was verified on the live URL before anything else was touched.

<br>

**Azure OpenAI signal extraction silent failure**

The Foundry endpoint was returning a JSON structure the parser was not expecting. Graceful degradation worked exactly as designed: Layer 2 skipped, Claude ran without signal flags. But that meant results were coming back without any detected signals for hours while I debugged something that was not visibly broken. The app worked. The safety held. But the second layer of the pipeline was doing nothing. **Lesson: graceful degradation can mask real problems. Telemetry exists precisely for this. Silent failures should not be silent in the logs.**

<br>

**The `.txt` MIME bypass**

Discovered during the security review. The upload MIME validation had a condition:

```python
if content_type not in allowed_mimes and ext != '.txt'
```

That `and ext != '.txt'` was a bypass. Any file renamed to `.txt` would skip MIME validation entirely. Not intentional — it was a defensive coding decision for browsers that omit content-type on plain text, which had mutated into a security hole. Caught during code review, not live testing. Fixed by removing the exception and handling the edge case properly.

<br>

**Upload content screening order**

The upload screener was truncating to 5,000 characters after running Content Safety on the first 1,000. Content Safety was screening chars 1–1,000, but the full 5,000-character extraction was still being returned. Malicious content in chars 1,001–5,000 went unscreened. The fix was trivial: truncate first, then screen the same bounded content. The problem was that both operations existed and nobody had verified the order.

<br>

**Cosmos DB provisioning gap**

Joanne caught this. The database container existed and the connection was succeeding, but the partition key was misconfigured. Preference reads were failing silently on every request. Graceful degradation was catching the exception and falling back to localStorage without logging anything visible. The app worked. Preferences appeared to save. Nothing was actually persisting to Cosmos DB. Invisible until Joanne ran an infrastructure review. **Lesson: graceful degradation is essential for uptime but can hide configuration bugs for a long time.**

<br>

**Calendar reminder at 1AM**

"Tomorrow morning" was mapping to 1:00 AM. Discovered when I tested the feature and got a calendar event at 1AM. The time logic lived in Joanne's Azure Function. The fix required coordination: updating the Flask proxy to pass an exact ISO datetime instead of relying on the Function to calculate it, and Joanne updating the Function's time mapping. Both changes were needed. "Tomorrow morning" is now 8:00 AM.

<br>

**The flash-hide bug in upload errors**

Error messages were disappearing the moment they appeared. The sequence: upload fails → `clearUpload()` runs → `showUploadError()` runs. But `clearUpload()` was clearing the error display that `showUploadError()` was about to populate. The user saw nothing. Fix was reordering two lines. `showUploadError()` now runs before `clearUpload()`. This took longer to find than it should have because the symptom, no visible error, looked identical to a successful upload.

<br>

**`is_medical` misclassification**

Claude was returning `is_medical: false` on clearly medical content. Dosing instructions, drug names, medical disclaimers. All present in the output, model still said not medical. The keyword backstop was built because of this: if the model returns `is_medical: false` but medical keywords are detected anywhere in the output, the validator overrides to `true` and all medical safeguards apply unconditionally. **A prompt is a request. The Python validator is a guarantee.**

<br>

**`risk_level` returning Safe with real warnings**

Claude was assigning Safe to responses that contained genuine safety warnings. The prompt asked it not to. The model did it anyway. The fix was a logic check in `validate_response()`: if `risk_level == "Safe"` and real warnings exist (excluding the mandatory medical disclaimer), upgrade to `"Caution"` and fire `risk_level_upgraded` telemetry. Runs last, after all processing, so it sees the final warnings list. The model cannot assign Safe to content that carries actual safety rules.

<br>

**Warnings leaking into tasks**

The model was putting safety instructions into the task list. "Do not crush or chew" as a step. "Never double up on a missed dose" as an action item. These are warnings. Users following task lists do not read them as cautions. They read them as instructions. Pattern matching in the validator: tasks starting with "do not", "never", "avoid", "skip" get moved to the warnings array automatically, in Python, regardless of what the model returns.

<br>

**Frequency stacking**

"Take medication three times daily" was appearing as a single task. For a neurodiverse user managing a medication schedule, that is not actionable. The frequency expansion system breaks it into named instances: morning, afternoon, evening. Unmappable frequencies like "every 6 hours" or "as needed" are moved to `key_items` instead of being silently dropped or corrupted.

<br>

---

## What I Learned

I learned Flask by building a production Flask application. I learned Azure by integrating ten Azure services under a deadline. I learned prompt engineering by writing prompts that had to be deterministic enough to enforce medical safety rules. I learned penetration testing by attacking something I built and watching the defences hold.

The cybersecurity work I came here to do, I did it. Just from the other side. Designing the defence layers, testing them live, reading the telemetry to confirm they fired. That is the same knowledge, approached differently.

I also learned what it means to enforce safety in code rather than in prompts. A prompt is a request. Python is a guarantee. The difference matters when the users are vulnerable people who cannot afford a system that behaves unpredictably.

The hardest thing was not technical. It was deciding at 8PM on March 20th to take on something I had not prepared for and to see it through. The second hardest thing was the sleep deprivation. Coffee helped but it is not a substitute.

<br>

---

## The Team

None of this reaches deployment without Joanne. Every Azure resource that the application depends on, Joanne provisioned and configured it: App Service, Key Vault, Blob Storage, Cosmos DB, the Foundry signal-classifier deployment, Managed Identity, CI/CD. A production deployment on Azure is not a small thing. The infrastructure that made the live URL possible was her work.

Fatima's most meaningful contribution was the research on neurodivergent users and cognitive load. That research shaped how we thought about the problem from the start. She also brought the colour system to the table — she had it in a slide as a suggestion, and it became one of the most distinctive parts of the product. The five accessibility palettes, each designed for a specific neurological need, trace back to that conversation.

I searched a lot of platforms to find this team. I am glad I did.

<br>

---

## After This

I need sleep. A few days at minimum.

It was worth it.

<br>

---

*Leishka Pagán - March 27, 2026*
