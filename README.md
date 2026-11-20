# Improvement Guru

**An MIT-licensed, open-source command-line toolkit for doctors and QI teams starting a quality improvement project or clinical audit.**

- Creates nine files, including a source map.
- Adds shift and trend annotations to a CSV of synthetic or fully de-identified measurements.
- `deid scan` reports supported identifier patterns. `deid redact` can write a separate copy.

Once installed, the CLI runs locally without an account, telemetry, AI calls or internet access.

This is an educational scaffold. It is not an information governance tool of record, not clinical decision support, not a governance approval tool, and not reliable de-identification for real patient data.

## Start here

Needs Python 3.11 or newer, Git, and internet access for the install.

macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "git+https://github.com/moeedahmed/improvement-guru.git@v0.1.0"
improvement-guru new my_audit --profile uk
improvement-guru sources show uk
```

Windows

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install "git+https://github.com/moeedahmed/improvement-guru.git@v0.1.0"
.venv\Scripts\improvement-guru new my_audit --profile uk
.venv\Scripts\improvement-guru sources show uk
```

When you have your own figures

Use only synthetic or already fully de-identified files.

```bash
improvement-guru charts run-chart synthetic_figures.csv --value-column value --out annotated.csv
improvement-guru deid scan synthetic_export.csv
```

![Improvement Guru hero image showing agent-native healthcare QI scaffolding, run charts, source profiles, local checks, and safety verification.](docs/assets/improvement-guru-hero.jpg)

## Install

### Install the released version

Improvement Guru is not on PyPI yet. Install the tagged release from GitHub:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install "git+https://github.com/moeedahmed/improvement-guru.git@v0.1.0"
.venv/bin/improvement-guru sources list
```

On Windows, run `py -m venv .venv`, then `.venv\Scripts\python -m pip install "git+https://github.com/moeedahmed/improvement-guru.git@v0.1.0"` and `.venv\Scripts\improvement-guru sources list`.

On Windows, upgrade with `.venv\Scripts\python -m pip install --upgrade "git+https://github.com/moeedahmed/improvement-guru.git@<newer-tag>"` and uninstall with `.venv\Scripts\python -m pip uninstall improvement-guru`.

To upgrade, run `.venv/bin/python -m pip install --upgrade "git+https://github.com/moeedahmed/improvement-guru.git@<newer-tag>"`. To uninstall, run `.venv/bin/python -m pip uninstall improvement-guru`.

### Install from a checkout (for contributors)

From a local checkout:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

> **Homebrew Python / modern Linux note:** If you see `error: externally-managed-environment` (PEP 668), create a virtual environment first:
>
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> python3 -m pip install -e ".[dev]"
> ```
>
> Alternatively, install with `--break-system-packages`, though a venv is strongly recommended.

You can also run the CLI from a checkout with `python3 -m improvement_guru ...`. If your environment maps `python` to Python 3.11 or newer, `python` is fine.

## Quickstart

Run these commands from inside an Improvement Guru checkout after installing the local package:

```bash
improvement-guru new demo_qip_project
improvement-guru new uk_demo --profile uk
improvement-guru sources list
improvement-guru sources show global
improvement-guru charts run-chart examples/synthetic_ed_flow_qip.csv --value-column median_time_to_initial_assessment_minutes --date-column week --baseline-points 4 --out /tmp/ed_flow_run_chart.csv
improvement-guru deid scan examples/synthetic_ward_audit.csv
improvement-guru deid redact examples/synthetic_ward_audit.csv --out /tmp/synthetic_ward_audit_redacted.csv
python3 -m pytest -q
```

The scan command exits `1` when findings are present and `0` when no supported patterns are found. The redact command refuses to overwrite the input file and refuses to overwrite an existing output file.

Actual `improvement-guru deid scan examples/synthetic_ward_audit.csv` output:

```text
3:28	EMAIL_ADDRESS	a***@example.nhs.uk
3:53	UK_POSTCODE	SW1A ***
3:62	DOB_LIKE_DATE	**/**/1978
3:73	UK_PHONE_NUMBER	071******89
3:86	NHS_NUMBER	999******8
3:99	POSSIBLE_NHS_NUMBER	999******0
4:27	EMAIL_ADDRESS	b***@example.nhs.uk
4:52	UK_POSTCODE	EC1A ***
4:61	DOB_LIKE_DATE	****-**-**
4:72	UK_PHONE_NUMBER	447*******23
4:88	NHS_NUMBER	999******0
5:28	EMAIL_ADDRESS	g***@example.nhs.uk
5:54	UK_POSTCODE	W1A ***
5:62	DOB_LIKE_DATE	**-**-1990
5:73	UK_PHONE_NUMBER	020******58
5:87	NHS_NUMBER	999******6
```

Actual run-chart command output:

```text
/tmp/ed_flow_run_chart.csv	rows=12	median=41.5	shifts=4	trends=6
```

The annotated CSV begins:

```csv
week,median_time_to_initial_assessment_minutes,notes,qip_index,qip_value,qip_baseline_median,qip_side,qip_run_length,qip_shift_signal,qip_trend_direction,qip_trend_length,qip_trend_signal
2026-W01,42,synthetic baseline,1,42,41.5,above,1,no,,1,no
2026-W02,41,synthetic baseline,2,41,41.5,below,1,no,down,2,no
```

## Commands

### Create a project scaffold

```bash
improvement-guru new <project-name> [--profile global|uk|us|canada|australia]
```

Creates a new folder containing:

- QIP charter
- PDSA log
- Driver diagram
- Data collection specification
- Audit standards worksheet
- IG/Caldicott checklist
- De-id checklist
- QIP registration checklist
- source map for the selected profile

Existing project folders are never overwritten.

### Inspect source profiles

```bash
improvement-guru sources list
improvement-guru sources show uk
```

Source profiles live in `standards/`. They provide primary source anchors and boundaries for different jurisdictions. They do not replace local governance.

### Analyse a run chart CSV

```bash
improvement-guru charts run-chart <input.csv> --value-column <column> --out <annotated.csv>
```

Optional flags:

- `--date-column <column>` validates a date/period column exists.
- `--baseline-points <n>` calculates the median from the first `n` rows.
- `--run-length <n>` changes the threshold for same-side shift signals.
- `--trend-length <n>` changes the threshold for consecutive improvement/worsening trend signals.

By default a shift is flagged at 6 or more consecutive points on the same side of the baseline median (a point exactly on the median resets the count) and a trend at 5 or more consecutive points each strictly higher or each strictly lower than the one before (`--run-length`, `--trend-length`; both must be at least 2).

The command writes a new annotated CSV with `qip_` columns for baseline median, side of median, run length, shift signal, trend direction, trend length, and trend signal. It is a lightweight helper for synthetic or properly de-identified learning data, not a statistical process control package.

### Scan for supported identifier patterns

```bash
improvement-guru deid scan <file.csv|file.txt>
```

Reports findings to stdout as:

```text
line:column    FINDING_TYPE    masked-preview
```

Supported deterministic detectors are currently UK-focused:

- Valid NHS number using the modulus-11 checksum.
- Invalid or format-only 10-digit NHS-like number as `POSSIBLE_NHS_NUMBER`.
- UK postcode.
- DOB-like date with a four-digit year. Two-digit-year dates such as `12/03/78` are out of scope.
- UK phone number.
- Email address.

The scanner does not attempt free-text name detection.

### Write a redacted copy

```bash
improvement-guru deid redact <input> --out <output>
```

The input file is read as UTF-8 text and is never modified. The output path must be different from the input path and must not already exist.

## Public-Safe Use

Use the included fixture only for testing. Do not put real patient-identifiable data into this kit. If a QIP or audit requires real patient data, use locally approved NHS systems, agreed minimisation controls, and your organisation's IG process.

## Agent Skill Guides

The `skills/*.md` files are static guide material with frontmatter fields for `name` and `description`. To use one in an agent runtime, copy the whole file into that agent's skill directory and keep the frontmatter plus refusal, pause, source, and safety sections intact. This repo does not auto-load those skills or provide an agent runtime.

## How Improvement Guru Fits

Improvement Guru is not trying to replace mature QI platforms or statistical packages at this stage.

- **Life QI** is the closest product benchmark: a paid QI project platform with dashboards, reporting, organisation portfolios, and community features. Improvement Guru is local-first, open-source, and scaffold-focused.
- **QI Macros** is the closest Excel/SPC benchmark: strong charts, Pareto, fishbone, templates, and statistics inside Excel. Improvement Guru is not an Excel add-in and does not yet compete on SPC depth.
- **IHI, NHS IMPACT, HQIP, SQUIRE, AHRQ, and Healthcare Excellence Canada** are source and training benchmarks. Improvement Guru links users back to source-grounded methods rather than copying guidance.
- **runcharter, qicharts, and spccharter** are open-source R charting benchmarks. Improvement Guru's run-chart helper is deliberately lightweight; stronger SPC support may come later.

The wedge is: agent-native, local-first QIP scaffolding with source-grounded country profiles, synthetic-safe examples, deterministic safety checks, and release-tested CLI workflows.

## Roadmap

The next useful improvements are practical, not platform theatre:

- Stronger run-chart and SPC support while staying CSV-first and transparent.
- More polished synthetic project packs for ED flow, sepsis documentation, analgesia time, and other common healthcare QI themes.
- More source profiles and local-governance prompts, with clear boundaries between QIP, audit, service evaluation, research, and incident learning.
- Better agent workflow hooks so coding and clinical agents can inspect the same scaffold, source map, safety checks, and release proof.
- A lightweight public launch page after the GitHub repo is settled; not a hosted QI platform yet.

## Limitations

- Pattern matching can miss identifiers and can produce false positives.
- The de-id scanner treats CSV as text; it does not understand CSV headers, cell types, or jurisdiction-specific identifiers outside the listed patterns.
- Redaction replaces matched text with bracketed labels and may change field length or formatting.
- Free-text names, addresses beyond postcodes, hospital numbers, record numbers, rare diagnoses, small-cell disclosure, and contextual re-identification are outside this MVP.
- The scaffold helps structure QIP thinking; it does not approve, register, govern, or clinically validate a project.

## Release Readiness

Run the local release smoke check before any public-facing release work:

```bash
python3 -m pytest -q
python3 -m compileall improvement_guru tests scripts
python3 scripts/release_check.py --install-smoke
python3 scripts/check_sources.py --dry-run
```

The smoke check proves UK and international profile scaffolds, source display, synthetic de-id scan/redact, the NHS 999 fixture convention, synthetic run-chart analysis, static skill-guide frontmatter and safety anchors, absence of tracked generated artifacts, and the installed `improvement-guru` console command path. See `docs/RELEASE_READINESS.md`.

## Architecture

The repo is the kit. The `skills/` directory contains static agent skill guides for use in an agent context; they are not auto-loaded by an agent runtime. The `improvement_guru/cli.py` CLI handles deterministic local file work. The `examples/` directory holds synthetic fixtures and demo QIP datasets. The `standards/` directory holds global and country source profiles. See `docs/ARCHITECTURE.md`.

## Source Freshness

Before release, re-check source URLs:

```bash
python3 scripts/check_sources.py --dry-run
python3 scripts/check_sources.py
```

## Contributing

See `CONTRIBUTING.md` before adding country profiles, source anchors, de-identification detectors, or agent skill guides. Contributions must use synthetic examples only and should keep country-specific rules out of the global core.

## Security

Do not include real patient, staff, organisation-sensitive, incident-identifiable, credential, or secret material in bug reports. See `SECURITY.md`.

## Incident Learning

Incident learning is adjacent to QIP, not identical to QIP. UK PSIRF is handled as a UK incident-learning module rather than the universal core. See `docs/INCIDENT_LEARNING.md`.
