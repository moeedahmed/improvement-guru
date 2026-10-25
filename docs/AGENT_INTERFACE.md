# Agent interface

Any agent or scheduler can drive Improvement Guru through its command line. There is no server, no MCP tool surface, no environment variables and no settings file: every input is a command-line argument or a file path, and every command runs offline.

Agents should only schedule, route and call these commands. Keep engine logic in this repo, and keep private settings (recipients, keys, state) in the agent's own workspace.

## Pin a version

Run a tagged release, not `main`, so an engine change cannot silently alter a live job.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install "git+https://github.com/moeedahmed/improvement-guru.git@v0.1.0"
.venv/bin/improvement-guru sources list
```

`python3 -m improvement_guru <command>` is equivalent to `improvement-guru <command>`.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Success (for `deid scan`: no supported patterns found) |
| 1 | `deid scan` only: one or more findings reported |
| 2 | Usage or input error; the reason is printed to stderr as `Error: ...` |

## Commands

| Command | Inputs | Output (stdout) | Writes |
| --- | --- | --- | --- |
| `improvement-guru new <project-name> [--profile global\|uk\|us\|canada\|australia]` | New folder name; optional source profile (default `global`) | One created path per line | A new project folder; refuses to overwrite an existing one |
| `improvement-guru sources list` | none | `id<TAB>name` per profile | none |
| `improvement-guru sources show <profile>` | Profile id | Formatted source profile | none |
| `improvement-guru charts run-chart <input.csv> --value-column <col> --out <annotated.csv> [--date-column <col>] [--baseline-points N] [--run-length N] [--trend-length N]` | CSV; numeric column; defaults `--run-length 6`, `--trend-length 5` | `output_path<TAB>rows=N<TAB>median=X<TAB>shifts=N<TAB>trends=N` | A new annotated CSV with `qip_` columns; refuses to overwrite |
| `improvement-guru deid scan <file.csv\|file.txt>` | File | `line:column<TAB>FINDING_TYPE<TAB>masked-preview` per finding, or `No supported identifier patterns found.` | none |
| `improvement-guru deid redact <input> --out <output>` | Input file; new output path | Output path | A redacted copy; never modifies the input; refuses to overwrite |

Finding types: `NHS_NUMBER`, `POSSIBLE_NHS_NUMBER`, `UK_POSTCODE`, `DOB_LIKE_DATE`, `UK_PHONE_NUMBER`, `EMAIL_ADDRESS`. The scan is assistive pattern-matching, not proof of anonymisation; see `SAFETY.md`.

## Rule packs and settings

- Source profiles (`standards/*.json`) are the country and curriculum rule packs. Choose one per project with `--profile`.
- Run-chart thresholds are arguments (`--run-length`, `--trend-length`), not constants an agent must patch.
- De-identification detectors are UK-focused today; other countries need a new detector set in this repo.

## Static skill guides

`skills/*.md` are guide files an agent can copy whole into its own skill directory. They are not auto-loaded and contain no executable logic.

## Connection test and example answers

`tests/test_agent_interface.py` drives the real command line the way an agent does and checks every documented exit code, stdout shape and `Error: ...` message against the good example answers in `tests/golden/agent_answers.json`. It is offline, uses only the synthetic examples, and runs in `./scripts/verify_changed.sh` and CI. If a command's output changes on purpose, update this page and that file together.

## Failure alerts

The engine has no service, so it sends no alerts itself. The agent that calls it turns a non-success result into an alert in the project that owns the product, with this plain header. Where alerts go is the agent's one shared setting, not an engine setting.

| Header line | Fill with |
| --- | --- |
| Product | `Improvement Guru` and the pinned version |
| What happened | The command run and its `Error: ...` line from stderr |
| Users affected | `No` for an input error (exit 2) the caller can correct; `Yes` if the same command fails for every input after a version change |
| Suggested fix | Exit 2: correct the input named in the message. A run that fails after a version bump: go back to the last good tag in `docs/rollback.md` |

`deid scan` exit 1 means findings were reported. That is a normal result to hand to the user, not a failure.

## No crash reporting

Improvement Guru sends nothing off the machine: no telemetry and no crash reports. That is a public promise, so no error tracker (such as Sentry) is added to the engine. Failures reach the owner only through the calling agent's alert above, or a GitHub issue the user chooses to file.
