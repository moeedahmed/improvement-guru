# Release Readiness Gate

This gate is for shaping Improvement Guru toward a public-safe release. Passing it does not mean the project is published, clinically approved, or safe for real patient data.

Follow the [release process](RELEASE_PROCESS.md) for the branch-to-PR route, required CI checks and release permission.

## Current Product Verdict

Improvement Guru is the public brand and repo/toolkit. The current release shape is:

- repo/toolkit: yes
- static skills: yes
- local CLI: yes
- synthetic run-chart helper: yes
- source profiles: yes
- engine: no
- hosted service: no
- clinical decision support: no
- governance approval tool: no

## Hard Release Boundaries

Do not publish or promote a release unless these statements remain true:

- Only synthetic examples are included.
- Real patient data is explicitly out of scope.
- The scanner is described as assistive pattern matching, not reliable de-identification.
- Local QI, audit, clinical governance, IG, Caldicott, ethics, and publication routes remain required where relevant.
- Incident learning is separate from QIP unless converted into a measured improvement project.
- No LLM calls, external API calls, MCP calls, hosted services, dashboards, background jobs, or agent runtime claims have been added.

## Required Local Proof

Run from the repo root:

```bash
python3 -m pytest -q
python3 -m compileall improvement_guru tests scripts
python3 scripts/release_check.py --install-smoke
python3 scripts/check_sources.py --dry-run
```

The source freshness dry-run lists URLs only. Before an actual public release, run the networked source check and manually review any blocked, redirected, or failed source:

```bash
python3 scripts/check_sources.py
```

The Australian Commission NSQHS Standards page is browser-verified as live on 2026-07-05. It may still report a `NOTE` in the command-line source checker because the official site can time out for CLI clients; this is expected and should not block release when the browser verification remains current.

## Synthetic Demo Proof

The release smoke check must demonstrate all of the following without real patient data:

- UK scaffold generation with UK source-map content.
- International scaffold generation from global, US, Canadian, and Australian profiles.
- Source display for profiles through the CLI/source formatting path.
- Synthetic run-chart annotation for ED flow, sepsis documentation, and analgesia-time demo datasets.
- Synthetic identifier scan on `examples/synthetic_ward_audit.csv`.
- Valid-checksum NHS-number fixtures use the NHS England synthetic `999` test range convention.
- Redacted output written to a new file without modifying the input.
- Static agent skill guides present with parseable `name`/`description` frontmatter plus source-profile and safety pause anchors.
- No generated artifacts are tracked by `git ls-files`.
- Local install smoke in a temporary venv, proving the packaged `improvement-guru` console command can find installed data files and run outside the source tree.

Equivalent release-smoke command:

```bash
python3 scripts/release_check.py --install-smoke
```

`deid scan` exits with status `1` when supported synthetic identifiers are found. That is expected for the included synthetic fixture.

## Repository Preflight

Before any external/public action, verify:

- public repo/toolkit name: Improvement Guru
- Python distribution name: `improvement-guru`
- Python import package: `improvement_guru`
- CLI command: `improvement-guru`
- no `.egg-info`, cache, build, dist, venv, or generated smoke-output files are included
- no valid-checksum NHS fixture number outside the `999` test range is included
- no real patient, staff, organisation-sensitive, or incident-identifiable data is included
- `python3 scripts/release_check.py --install-smoke` passes in the extracted checkout

## Launch Lessons

Three lessons carried over from Teaching Guru launches. They apply to every
Improvement Guru tag or GitHub release.

1. **One release at a time.** Only one tag or GitHub release is in progress at
   once. Do not start a second until the first is published and checked live,
   or rolled back with the [rollback playbook](rollback.md). Overlapping
   releases left a Teaching Guru release stuck on hold.
2. **Readiness check before launch.** This gate is the readiness check. Run the
   required local proof and tick every item in the checklist below on the exact
   release commit, on the day of release. An unticked item blocks the release;
   a check written down but not run does not count.
3. **Done means users actually got it.** A release is done only when a user can
   get it: the GitHub release page is public, and a fresh install from the
   published tag runs `improvement-guru --help` and the synthetic demo outside
   the source tree. A created tag or green CI alone is not done.

## Public Release Checklist

- [ ] README leads with Improvement Guru positioning and no-engine boundary.
- [ ] `SAFETY.md` says the kit is educational and not reliable de-identification for real patient data.
- [ ] `docs/PRODUCT_POSITIONING.md` is current.
- [ ] Source profile URLs have been re-checked and `checked_on` dates updated where needed.
- [ ] Browser/manual verification is documented for any official source that reports an expected CLI `NOTE`.
- [ ] All examples are synthetic and marked as synthetic.
- [ ] Valid-checksum NHS-number examples use the NHS England synthetic `999` test range convention, with only one invalid-checksum row retained for `POSSIBLE_NHS_NUMBER`.
- [ ] Synthetic run-chart examples are included and do not imply live clinical performance benchmarking.
- [ ] No generated `.egg-info`, cache, build, or virtual environment files are included in the release diff.
- [ ] Tests, compileall, source dry-run, and install smoke pass locally.
- [ ] Package/distribution naming is `improvement-guru`; import remains `improvement_guru`; CLI command is `improvement-guru`.
- [ ] Founder/product review has approved public copy.
- [ ] Medic/clinical safety review has approved boundaries and non-claims.
- [ ] No other tag or GitHub release is in progress (launch lesson 1).
- [ ] Every item in this checklist was checked on the exact release commit today (launch lesson 2).
- [ ] After publishing: the release page is public and a fresh install from the published tag runs outside the source tree (launch lesson 3).

## Remaining Before Public Release

- Extract into the intended public repository target without generated caches or local workspace-only files.
- Re-check official source URLs near the release date.
- Review public README wording for non-claims before any announcement.
- Confirm the intended open-source release target, license posture, and contribution policy.
