# Release process

## Change route

Route every change through a branch and pull request (PR). `main` moves only
through a green PR merge in normal operation. Before pushing, run
`./scripts/verify_changed.sh` locally. Adopted from Portfolio Guru: PR-only
changes, proof for the exact merge result, an offline release gate, and a
fail-closed rule: no green checks, no merge.

## Required CI proof

[CI](../.github/workflows/ci.yml) runs 12 GitHub-hosted jobs: Ubuntu, macOS and Windows, each on Python
3.11–3.14. Every job runs `pytest`, `compileall`,
`scripts/release_check.py --install-smoke` and
`scripts/check_sources.py --dry-run`.

All 12 required checks must pass on the PR's merge result with up-to-date
`main`, enforced through strict required-check protection. If `main` moves,
update the PR and wait for fresh green checks before merging; branch-only or
older green results are insufficient.

## Release permission and recovery

Before any tag, run `./scripts/verify_release.sh` locally on the intended
release commit. This offline gate adds an isolated package-install smoke test
and source-list dry-run to the change gate; it does not prove live source URLs.
Complete the separate public-release checks in [Release readiness](RELEASE_READINESS.md).
Create a tag or GitHub release only after Moeed explicitly says yes to that
release. This process authorises no PyPI upload or deployment.

Follow the [rollback playbook](rollback.md) for a bad commit or published
version. Route revert and fix commits through the same branch-to-PR checks.

## Deliberately omitted

- Serial coordinator or queue: there is no deployment or shared single runner;
  GitHub-hosted runners are free for this public repository and run in parallel.
- Dedicated live/deploy checkout: nothing is deployed.
- Preview flags or an ungated route: there is no user-visible service or account
  flow requiring them.
- Self-hosted runner and custom Python-path handling: CI uses hosted runners
  with `actions/setup-python`.
- Watchdog or extra notifications: there is no queue to stall. Failed CI is
  visible on the PR and through GitHub notifications; delivery of alerts to an
  owning agent thread has not been established or proved.
- Service-health checks or service rollback: there is no service to monitor or
  restart; package and commit recovery uses the rollback playbook.

## Enforcement limits and break-glass

GitHub merge queue is unavailable on this repository's plan. Strict required
checks provide the up-to-date-main gate; there is no serial merge coordinator.
Branch protection is not enforced against administrators, who can bypass it.
The PR-only rule is therefore not server-enforced against administrators.
An administrator may use this discretionary break-glass bypass, but must
record the reason and validation evidence on the PR. This exception does not
grant permission to tag, publish or deploy.
