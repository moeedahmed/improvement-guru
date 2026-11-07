# Project record and next step

`improvement-guru new synthetic-project` creates the usual scaffold and a
local `project.json`. The record starts at schema version 1, with today's
creation date, an unset route, stage `start`, an empty aim, measures, PDSA
cycles, weekly counts and optional audit details. It makes no AI or network
calls. Existing scaffold folders need a record before using these commands.

## Commands

```sh
improvement-guru new synthetic-project
improvement-guru project next synthetic-project
improvement-guru project set-route synthetic-project --route qi
improvement-guru project set-aim synthetic-project --aim "Improve synthetic completion from half to three quarters within eight weeks"
improvement-guru project add-measure synthetic-project --name Completion --kind outcome --definition "Weekly completed items divided by eligible items"
improvement-guru project add-measure synthetic-project --name Uptake --kind process --definition "Weekly prompt uses divided by eligible items"
improvement-guru project add-measure synthetic-project --name Rework --kind balancing --definition "Weekly repeated items divided by eligible items"
improvement-guru project set-stage synthetic-project --stage test
improvement-guru project add-pdsa synthetic-project --change-idea "Try a synthetic prompt" --prediction "Completion will rise"
improvement-guru project close-pdsa synthetic-project --id 1 --result "Compare the observed result with the prediction" --decision adapt
improvement-guru project set-stage synthetic-project --stage measure
improvement-guru project add-counts synthetic-project --week 2026-11-02 --numerator 3 --denominator 4
improvement-guru project next synthetic-project
```

`project next` defaults to the current directory. All editing commands take a
project directory. Routes are `audit`, `service-evaluation`, `qi`, `research`.
The doctor sets the route after local confirmation. Stages are `start`, `test`,
`measure`, `audit`, `write-up`. They are recorded explicitly.

Repeated `add-measure` with the same name and kind updates its definition.
An omitted definition remains empty and prompts a next step. PDSA IDs are
positive integers assigned in order. Opening a cycle requires a prediction.
Closing an open cycle requires a result and `adopt`, `adapt` or `abandon`.

Weekly counts are whole-number numerators and denominators with
`0 <= numerator <= denominator` and `denominator > 0`. Dates must be
`YYYY-MM-DD`. Duplicate weeks are rejected. Counts are stored as entered and
analysed in date order, using each week's numerator divided by denominator.
There is one weekly series per record. No raw patient rows are accepted.

Audit details can be edited directly in the `audit` object in `project.json`.
The optional keys are `standard`, `source`, `sample_rules`,
`baseline_compliance` and `reeaudit_date` (the schema spelling). Baseline
compliance can be text with explicit units, or a finite number whose units
are explained in the standard. The date uses `YYYY-MM-DD`.

Writes use a temporary file in the project folder followed by atomic
replacement. CLI edits hold `.project.lock` to refuse competing writers.
If a process is forcibly terminated, verify it has stopped before removing
its leftover lock and retrying. Avoid editing JSON manually during a CLI edit.
Invalid input, missing files and unsupported schemas exit 2 with an error.
Successful commands exit 0. Scanner refusals exit 1 and leave the record intact.

## One next step

Route confirmation, a SMART aim, all three measure kinds (including balancing)
and operational definitions come first. The remaining rules follow the stage.

- `start` and `test` prompt for a small PDSA with a prediction, then an open
  cycle's result and decision, then movement to measurement.
- `measure` prompts for more counts until ten off-median points exist, then
  review of named signals or continued collection and the next test.
- The audit route or `audit` stage prompts for missing audit details,
  including a re-audit date, then re-audit against the same standard.
- `write-up` prompts for methods, results, limitations and next action once
  the common prerequisites and any audit details are present.
- A confirmed research route prompts for the local research protocol and
  approvals after the common prerequisites.

Each response prints one step, its reason and the disclaimer below.

## Run-chart rules

The centre line is the median of the complete weekly proportion series.
A Shift requires six points above or below the median. On-median points are
skipped without breaking the shift. A Trend requires five rising or falling
points. Equal consecutive values are skipped without increasing the count.
Fewer than ten usable points, after removing on-median values, reports
`too few points (N of at least 10) to call a signal` and no signals.
Signals are named with their threshold count and first qualifying week span.

A signal means variation unlikely to be chance, not proof that the change
caused it. This is a run chart, not SPC. The existing CSV chart command keeps
its existing configurable thresholds, tie resets and absence of this minimum
point gate.

## Safety and identifier scanning

Before `add-counts` saves anything, creation dates, weekly dates and audit
re-audit dates are strictly validated as `YYYY-MM-DD` structured fields.
The existing `deid.scan_text` scans a copy of the record with only these
structured dates replaced by a neutral placeholder. The saved dates are
unchanged. Free text (including the name, aim, measure names and definitions,
PDSA fields and audit text) and the directory argument are still scanned.
Any finding refuses the write.

The check is assistive and not a guarantee of anonymisation. It cannot
reliably detect names or all free-text identifiers. Never enter real
patient-identifiable data. Follow [SAFETY.md](../SAFETY.md), local IG/Caldicott
requirements and approved data-handling arrangements.

Not clinical decision support or governance approval. Confirm your route and register the project locally.
