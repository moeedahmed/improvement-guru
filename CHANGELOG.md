# Changelog

All notable changes to Improvement Guru will be documented here.

## Unreleased

- `deid scan` now prints one plain `Error:` line and exits 2 for a missing file, a folder, an unreadable file, or a file that cannot be decoded as UTF-8, instead of a Python traceback. `deid redact` gives the same clearer message for a file that is not UTF-8 text.
- `new` now prints a plain error when the parent folder does not exist or the project name is empty. `new`, `sources list`, and `sources show` name the failing bundled file or profile in a plain error.
- Fixes `improvement-guru` not finding its source profiles and templates after `pip install --user`.
- Adds `improvement-guru --version`.
- `improvement-guru deid`, `charts`, and `sources` with no subcommand now print their own help.
- `charts run-chart --help` now shows the default run and trend lengths, and a "column not found" error hints when the file does not look comma-separated.
- README: adds an install command for the tagged release, states the default shift and trend rules, and corrects the PyPI status.
- Docs: aligns the contributor, release-readiness and rollback notes with the current release process.

## 0.1.0 - 2026-10-16

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

The package is not published on PyPI.
