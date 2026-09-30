# AGENTS.md — Improvement Guru

## Project

Improvement Guru: agent-native, local-first healthcare quality-improvement (QI)
toolkit. Ships as a Python package with `improvement-guru` console entry
points: project scaffolding by source-region profile, deterministic
de-identification (PII scan/redact) of CSV exports, run-chart statistical
analysis for QI/audit data, and static agent skill guides. No database, no
web server, no bot — pure library + CLI.

## Stack

- Python 3.11–3.14, `setuptools`/`pyproject.toml` packaging
- `improvement_guru/{charts,deid,scaffold,sources,paths}.py` — engine modules
- `improvement_guru/cli.py` — CLI entry point (`improvement-guru` console script)
- `pytest` for unit tests (`tests/`)
- GitHub Actions CI: `.github/workflows/ci.yml`, matrix across
  ubuntu/macos/windows x Python 3.11–3.14

## Change safety gate

Do not claim a change is "done" or "release-ready" without a green run of
the relevant gate below. State which one you ran and paste/summarise its
output as proof.

- **Every change**: `./scripts/verify_changed.sh` — full pytest suite +
  `compileall` + `scripts/release_check.py` (in-process smoke: all 5 source
  profiles scaffold correctly, de-id scan/redact round-trips on the
  synthetic fixture, run-chart analysis produces shift signals on all 3
  synthetic examples, skill-guide frontmatter/safety anchors intact). Fast,
  fully offline. Run before calling any change done.
- **Before release/tag**: `./scripts/verify_release.sh` — `verify_changed`
  plus `release_check.py --install-smoke` (installs into a fresh
  network-isolated venv and drives the packaged `improvement-guru` console
  commands end to end) and `check_sources.py --dry-run` (source-profile URL
  list integrity, no live requests). CI (`.github/workflows/ci.yml`) runs
  the equivalent steps on every push/PR. See `docs/rollback.md` for the
  rollback playbook.

No repo here owns a database or applies schema migrations, so there is no
migration-safety policy — see `docs/rollback.md` for why.

## Safety boundaries

See `SAFETY.md`. The de-id scanner is assistive pattern-matching, not
proof of anonymisation; this is not clinical decision support or an
information-governance tool of record.

## Rules

- Complete code only, no placeholders or TODOs
- Commit messages: conventional commits (feat/fix/chore/docs)
- Never use real patient-identifiable data anywhere in this repo, including
  test fixtures — synthetic data only (NHS England `999` test-range
  convention for NHS numbers)
- Never remove the `SAFETY.md` boundaries when editing skill guides or docs

---

## Scope Guard

Complete the current task with the minimum sufficient change.

- Before editing, define the outcome, non-goals, expected files, and proof.
- Read the relevant code, tests, and configuration directly; resolve ambiguous or unverified premises first.
- Reuse existing helpers, patterns, and test setup. Fix the root cause rather than stacking workarounds.
- Add an abstraction only for an explicit requirement or a second real caller in the current task.
- Preserve behaviour outside the requested change and remove replaced code unless compatibility is explicit.
- Run the narrowest relevant existing tests and extend the nearest relevant test before creating new test infrastructure.
- Stop and re-scope before adding an unexpected dependency, service, public API, schema, storage or wire-format change, duplicate implementation, unrelated file, or speculative cleanup.
- Finish with only necessary files changed and no debug code, backup copies, scratch files, or dead paths.

## Working Modes

- Default to bounded execution inside the current approved task; keep the Scope Guard plan internal unless Moeed asks for it or a real boundary emerges.
- Use a visible plan for a material architectural decision, protected effect, or genuine scope expansion—not an arbitrary file count.
- Use one worker by default. Split only genuinely independent work, with one writer per file and branch.
- Self-correct with the named build or tests before reporting, and summarise the verified outcome plainly.

## Decision Boundaries

- Decide safe reversible implementation details within the requested outcome.
- Ask only when a material ambiguity changes the outcome or when the work crosses the controlling session's protected-action boundary.
- Treat new dependencies, database or storage mutations, schema/API changes, auth/security changes, deployment, destructive Git/process actions, and external effects as boundaries unless already explicitly authorised.
- This file never grants authority beyond the controlling session and profile policy.

---

## Compatibility

`CLAUDE.md` is a symlink to this file for Claude Code compatibility. Do not
maintain duplicate long-form agent context files.
<!-- product-standard:start (master copy: moeedahmed/skills skills/product-standard; edit there, not here) -->
## EM Gurus product standard

Applies to every EM Gurus product. Where this file says something stricter above, the stricter rule wins.

- **Build:** keep this repo's stack; meet the house quality bar (clean build, critical-path tests, no Critical/High security findings, visual checks at mobile and desktop width); put deterministic logic in code with a test that fails if it regresses.
- **Release:** a task from Moeed is already approved. Merge the latest main, run this repo's full checks, release, confirm it is actually live, then tell Moeed in one line that it is done and live so he can test. Never force-push. A feature switched off by default is fine to release.
- **Still ask first** (one tappable question, recommendation marked): deleting user data, changing stored passwords or keys, database changes that lose data, and anything sent to real users or the public.
- **Reliability:** keep a health check, error alerts and a known rollback path (last good version plus the exact command). If a release fails its checks or live proof, roll back or fix forward in the same run and say which.
- **Messages to Moeed:** first line is the point, plain English, short bullets. When done, give a short summary and close your own thread.
- **Marketing voice:** anything written as Moeed or for the public follows the `moeed-voice` skill; posting or sending it still needs his yes.
<!-- product-standard:end -->
