# Improvement Guru for ChatGPT (skills-only plugin)

A free, skills-only package for the ChatGPT plugin directory. One workflow, **QI Project Starter**, uses made-up figures to turn a fictional or generic service problem into a QI starter pack: a project charter, a SMART aim, measures and a first PDSA test, with links to a checked list of UK-focused sources and the local checks still needed.

**Status:** draft for the publisher's review. It has not been submitted, published or tested inside ChatGPT.

## What is in the package

- `plugin.json`: the manifest (Agent Plugins schema, with OpenAI listing fields under `extensions.com.openai`).
- `skills/qi-project-starter/SKILL.md`: the workflow.
- `skills/qi-project-starter/references/`: the checked UK-focused sources, measures and run-chart rules, the quality rubric, three fictional scenarios and a worked example.
- `skills/qi-project-starter/assets/starter-pack-template.md`: the output template.
- `assets/logo.svg` and `assets/icon.svg`: the listing and composer icons.
- `PRIVACY.md`, `TERMS.md` and `SUPPORT.md`: drafts for review.

Kept in this folder but left out of the ZIP: `REVIEW_TESTS.md` (test prompts to run before submitting) and `SUBMISSION_CHECKLIST.md` (what the publisher must decide or do first).

## What it leaves out

No server (MCP), no account or sign-in, no payments, no email capture, no analytics, no real project data and no patient data.

## Why it is more than a prompt

- Fixed stages with checks between them: work-type check, charter, SMART check table, family of measures, PDSA with thresholds set in advance.
- A fixed output template and a quality rubric the model runs before replying.
- Sources only from a bundled, checked list; anything else is marked "To check locally".
- Run-chart rules that match the Improvement Guru toolkit's own tested code.
- Clear stop points for patient details, clinical advice, patient-level data, ethics decisions and incident investigation.

## Build the ZIP

From the repository root:

```bash
python3 scripts/build_chatgpt_plugin.py
```

This checks the package against the directory's published limits and writes the ZIP to `dist/` (ignored by git). Nothing is uploaded.

See `SAFETY.md` at the repository root for the project's safety boundaries.
