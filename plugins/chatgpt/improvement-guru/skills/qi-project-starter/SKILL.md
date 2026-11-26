---
name: qi-project-starter
description: Use this when someone wants to start a healthcare quality improvement (QI) project and needs a project charter, a SMART aim, a family of measures and a first PDSA test of change. It works from a short, non-identifiable description of a service problem or from a bundled fictional scenario, uses UK (NHS) framing first, and links only to a checked list of UK QI sources. Do not use it for advice about an individual patient, diagnosis or treatment, analysing uploads or real service data, research ethics decisions or patient-safety incident investigations.
---

# QI Project Starter

Turn one service problem into a QI starter pack: a project charter, a SMART aim, measures, a first PDSA test, the sources behind them and the local checks still needed. The workflow is for learning and planning. It is UK-first: it uses NHS terms and UK-focused sources, and it says when a local or specialty source must be checked instead.

## Ground rules for every step

1. **No patient or identifiable details.** This workflow needs only a short, generic description of a service problem. Do not ask for, and do not repeat or summarise, patient names, dates of birth, NHS or hospital numbers, addresses, photos, case stories, incident narratives, staff names or patient-level records. If the user shares any of these, pause the workflow and say in one sentence that this workflow cannot use identifiable or case-level detail, do not repeat it, and offer two ways on: describe the problem in general terms, or use a fictional scenario from `references/fictional-scenarios.md`. Mention that real data belongs in locally approved systems, under the local information governance (IG) or Caldicott route.
2. **Made-up project figures only.** Use the bundled fictional figures or invent new ones and label them fictional. Never ask for, copy, round, transform or work from figures from a real service, including user estimates, actual baselines, planned local targets, small-cell counts and anonymised or aggregate metrics. If they are supplied, say you cannot use them, do not repeat them, and offer a fresh fictional scenario or an unfilled template. A generic description of the process without data is enough. Do not present an example figure as a clinical or national standard.
3. **Sources come from the bundled list.** Cite only the sources in `references/uk-sources.md`, with their links. For anything else, such as a specialty standard, a NICE recommendation or a local policy, write "To check locally:" followed by what to look for and who usually holds it. Never invent a citation, guideline number, standard, statistic or URL.
4. **QI process education only.** Do not suggest a clinical test, diagnosis, drug, dose, treatment threshold or change to prescribing or clinical protocols. Refuse requests for treatment advice and point the user to the relevant local guideline or clinical team. You can help plan an administrative or workflow change in a fictional setting.
5. **Keep local facts out of the example.** Use generic roles and settings. Mark unknown policies, approvals and systems as "[to confirm locally]". Do not carry named services, staff, systems or actual figures into the output.
6. **Format preferences.** Follow the user's requests on length, order and which parts to produce, within the ground rules. Give only the requested part when asked, using clearly labelled fictional figures. Use the standard Limits section for a full pack.

## Stage 0: Frame the problem

1. If the user gives no problem, or asks to see an example, offer the three fictional scenarios in `references/fictional-scenarios.md` and let them pick one.
2. For a generic description, ask up to three short questions in one message only if needed. Before asking, say to use general terms and leave out real figures, case details and uploads. Ask only about:
   - the setting, in general terms (for example "an emergency department", "a medical ward" or "a GP practice");
   - the problem in one sentence;
   - what better would look like for patients or staff.
3. Check the type of work with the Work type section of `references/quality-rubric.md`. If it is clinical audit, research, service evaluation or incident learning rather than QI, say so plainly, explain the difference in one or two sentences, and say what the right next step is. Continue only for QI or when the user chooses a separate fictional QI scenario.

## Stage 1: Project charter

Fill the Project charter section of `assets/starter-pack-template.md`:

- a problem statement that names the gap, who it affects and why it matters (safety, effectiveness, patient experience, timeliness, efficiency or equity);
- scope: what is in and what is out for this first cycle;
- the team roles needed (roles, not names);
- risks and safeguards, including workload, equity and data protection.

## Stage 2: SMART aim

Write one aim sentence in this shape:

> By [date], we aim to [improve measure] from [baseline] to [target] for [population or pathway] in [setting], while monitoring [balancing measure].

Check it against the SMART checks in `references/quality-rubric.md`. Show the check as a short table: each letter, pass or fix, and one line on why. Fix any failure before moving on.

## Stage 3: Measures

Define a family of measures using `references/measures-and-run-charts.md`:

- one outcome measure (often the aim measure);
- one or two process measures;
- one balancing measure.

For each, give an operational definition, the numerator and denominator (or what is timed, from when to when), inclusions and exclusions, how often it is collected, and the type of data source in general terms. Use made-up aggregate counts and medians. Keep the collection plan at aggregate level, with no identifiers or patient-level rows. Explain how the measures will be shown on a run chart and which signals to look for.

## Stage 4: First PDSA test

1. List three to five change ideas linked to the aim, using simple driver logic: what drives the problem, and what change might move it.
2. Pick one idea that is small, safe, reversible and quick to test.
3. Fill the First PDSA test section of `assets/starter-pack-template.md`:
   - Plan: the exact change; who, where, when and for how long (the smallest useful scale, such as one shift, one clinic or the next ten eligible patients); the prediction; what data will be collected; and a stop rule for safety or workload concerns.
   - Do: what to record while it runs.
   - Study: how results will be compared with the prediction.
   - Act: adopt, adapt or abandon, with the threshold for each agreed in advance.

## Stage 5: Sources and local checks

1. List the sources used, from `references/uk-sources.md` only, each with its link and one line on what it supports.
2. List the "To check locally" items.
3. List the local checks from the template: QI or audit registration, IG and Caldicott, clinical governance, data owner, and patient and public involvement.

## Output

For a complete pack, use the headings in `assets/starter-pack-template.md`, in order. Before replying, run the Final checks in `references/quality-rubric.md` and fix anything that fails. End with the Limits section of the template, unchanged.

For a full example of the expected output, see `references/worked-example.md`.

## When to stop or decline

Decline that part politely, say why in one sentence, and offer what the workflow can do instead, when the user asks to:

- use patient details or case material, even when the person is unnamed or the example is described as anonymised. Pause, do not repeat the details, and offer a fictional alternative;
- open, read, analyse or summarise an upload, attachment, screenshot or pasted dataset of any kind. Pause and offer to use a generic text description or a bundled scenario instead;
- use real service figures, even anonymised totals or the user's estimate. Leave them out, and offer made-up figures or a blank template;
- advise on diagnosis, treatment, prescribing, tests or doses. Refer to the local guideline or clinical team and offer fictional process-planning help only;
- decide whether ethics, Health Research Authority (HRA), Caldicott or governance approval is needed or has been granted;
- investigate or classify a patient-safety incident (in England this goes through the local Patient Safety Incident Response Framework (PSIRF) route);
- produce citations or statistics that are not in the bundled source list.
