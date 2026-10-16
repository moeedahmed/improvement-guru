# Changelog

All notable changes to Improvement Guru will be documented here.

## 0.1.0 - 2026-10-13 (draft, unpublished)

- Renames the product from QIP Guru to Improvement Guru: distribution `improvement-guru`, import package `improvement_guru`, CLI `improvement-guru` (the `qip` command and `qip.py` script are replaced by `improvement-guru` and `python3 -m improvement_guru`).
- Includes global, UK, US, Canadian, and Australian source profiles.
- Includes static agent skill guides for QIP planning, PDSA, audit standards, SMART aims, and incident-learning triage.
- Includes synthetic ED flow, sepsis documentation, and analgesia-time demo datasets.
- Adds lightweight run-chart CSV annotation for synthetic or properly de-identified QIP data.
- Includes deterministic assistive de-id scanning/redaction for synthetic CSV/text examples.
- Hardens NHS-number and UK-phone scanning so matches cannot span newlines.
- Keeps valid-checksum NHS fixture numbers in the NHS England synthetic `999` test range convention, with one invalid-checksum row for `POSSIBLE_NHS_NUMBER`.
- Adds parseable frontmatter to static agent skill guides.
- Adds local release checks for scaffolding, source profiles, synthetic de-id proof, NHS fixture range checks, run-chart proof, skill-guide frontmatter/safety anchors, tracked generated artifacts, and installed console-command smoke testing.
- Adds GitHub Actions CI, a bug-report template, and a code of conduct.
- Refreshes source-profile verified dates from the 2026-10-01 source audit (docs/source-freshness-audit-2026-10-01.md); four sources (NSQHS, SQUIRE, AHRQ Quality Indicators toolkit, TeamSTEPPS) could not be re-checked directly and keep their earlier dates.

No PyPI upload or external announcement has happened in this pass.
