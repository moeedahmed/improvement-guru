# Source freshness audit — 1 October 2026

**DRAFT FOR CLINICIAN REVIEW — IG1: partial verification; not release approval.**

## Scope and method

Read `docs/SOURCE_POLICY.md`, `docs/RELEASE_READINESS.md`, `SAFETY.md`, all five
`standards/*.json` profiles and their loader/checks. The profiles contain 20
references to 15 distinct URLs. Every distinct URL received a direct HTTPS GET
with redirects enabled, TLS verification enabled, a browser user agent and a
25-second limit. Successful responses were checked for the expected page title,
publisher and substantive content, rather than counting a cookie/challenge page
as success. All 11 successful source requests ended at the original URL.

The built-in web reader/search supplied supplementary publisher and rights
evidence. Its retrieved/indexed content is explicitly distinguished below from
direct live GET proof. Four sources remain blocked to direct verification; this
does not establish that they are dead. A Crawl4AI browser fallback failed before
navigation with `unable to open database file`; no browser verification is claimed.
No login, permissions request, paid model call or access-control bypass was used.
Temporary fetched content was removed; only metadata and this original audit remain.

## Complete source inventory

Rights codes refer to the evidence and qualifications in the next section.
“First-party” identifies the publisher, not endorsement or governance approval.

| Source (exact profile URL) | Profiles | Direct result and publisher assessment | Rights |
| --- | --- | --- | --- |
| [NSQHS Standards](https://www.safetyandquality.gov.au/national-standards/nsqhs-standards) | australia | **Blocked:** HTTP/2 transport error; HTTP/1.1 fallback timed out after 25 seconds. Web reader returned the Commission's page, but no fresh direct/browser proof. | AU |
| [Model for Improvement](https://www.ihi.org/library/model-for-improvement) | australia, global, uk | **200:** expected IHI page; first-party method resource. It credits Associates in Process Improvement and Wiley. | IHI |
| [SQUIRE 2.0](https://www.squire-statement.org/index.cfm?fuseaction=Page.ViewPage&pageId=525) | australia, canada, global, us | **Blocked: 403** in direct GET and web reader. Official domain corroborated by [EQUATOR's guideline record](https://www.equator-network.org/reporting-guidelines/squire/); exact page content not verified. | SQ |
| [Patient Safety Essentials](https://www.healthcareexcellence.ca/programs/patient-safety-essentials/) | canada | **200:** expected Healthcare Excellence Canada course page; first-party national charity, not a regulator. | HEC |
| [Programs Directory](https://www.healthcareexcellence.ca/programs/) | canada | **200:** expected Healthcare Excellence Canada directory and publisher identity. | HEC |
| [HiQuiPs (Quality Improvement)](https://canadiem.org/hiquips/) | canada | **200:** expected CanadiEM education series. First-party educational publisher; not an official Canadian national standard or government source. | CE |
| [Global Patient Safety Action Plan 2021–2030](https://www.who.int/publications/i/item/9789240032705) | global | **200:** WHO publication page; title and ISBN 9789240032705 match. | WHO |
| [Best Practice in Clinical Audit](https://www.hqip.org.uk/guidance/best-practice-in-clinical-audit/) | uk | **200:** expected HQIP guidance, dated 14 May 2020; first-party national audit organisation. | HQIP |
| [A guide to quality improvement tools](https://www.hqip.org.uk/guidance/guide-to-quality-improvement-methods/) | uk | **200:** expected HQIP guide, published January 2021. The old “methods” URL correctly serves the updated “tools” title. | HQIP |
| [Improvement resources](https://www.england.nhs.uk/nhsimpact/improvement-resources/) | uk | **200:** expected NHS England NHS IMPACT directory; official NHS page. Linked resources have their own owners. | NHS |
| [Resources](https://nqican.org.uk/resources/) | uk | **200:** expected N-QI-CAN network directory and named links. First-party professional network, not a regulator or government standard. | NQ |
| [Patient Safety Incident Response Framework](https://www.england.nhs.uk/long-read/patient-safety-incident-response-framework/) | uk | **200:** expected NHS England framework; page displays last update 23 September 2025. | NHS |
| [PSIRF supporting guidance](https://www.england.nhs.uk/publication/patient-safety-incident-response-framework-and-supporting-guidance/) | uk | **200:** expected NHS England collection, including response guidance, standards and policy/plan templates. | NHS |
| [Toolkit for Using the AHRQ Quality Indicators](https://www.ahrq.gov/patient-safety/settings/hospital/resource/qitool/index.html) | us | **Blocked: 403** (CloudFront error). Web reader returned the official AHRQ toolkit, labelled last reviewed March 2017; retrieval does not establish fresh direct availability or current indicator specifications. | US |
| [TeamSTEPPS 3.0](https://www.ahrq.gov/teamstepps-program/index.html) | us | **Blocked: 403** (CloudFront error). Web reader returned the expected official AHRQ TeamSTEPPS 3.0 page; direct availability remains unverified. | US |

## Licence evidence and unresolved reuse

These are observations of published terms, not legal clearance. The package's MIT
licence does not relicense any external resource. A fresh `checked_on` date proves
the recorded source-page check, not permission to reproduce or adapt its contents.

- **IHI — restricted reuse, live terms 200.** [Terms of use](https://www.ihi.org/terms-use) permit limited credited sharing, prohibit modification, website reposting and commercial repackaging, and prefer links. The [source page](https://www.ihi.org/library/model-for-improvement) directs figure/related-content permissions to Wiley. No blanket open licence or Wiley permission was established.
- **SQ — licence unresolved, source blocked.** [EQUATOR](https://www.equator-network.org/reporting-guidelines/squire/) corroborates the SQUIRE website and 2.0 guideline. That record is not a licence for the blocked page/checklist; do not infer rights from a separately published journal article. Retain the existing URL and historical date pending publisher-page review.
- **WHO — CC BY-NC-SA 3.0 IGO.** The live [publication page](https://www.who.int/publications/i/item/9789240032705) identifies this licence in its structured metadata. Live [WHO copyright policy](https://www.who.int/about/policies/publishing/copyright) (200) requires attribution, non-commercial use and compatible share-alike terms, with additional adaptation/translation notices and third-party exceptions. Commercial reuse needs separate permission; none was requested.
- **HEC — restricted reuse, live terms 200.** [Website terms](https://www.healthcareexcellence.ca/terms-of-use/), sections 9–10, allow non-commercial downloading/printing and attributed short excerpts, while reserving other copying/adaptation/distribution rights. They also restrict automated access; no further crawling was attempted after reading them. No blanket open licence was found for either profile resource.
- **CE — CC notice with qualification.** The live [HiQuiPs page](https://canadiem.org/hiquips/) has an HTML `rel="license"` footer link to [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Live [terms](https://canadiem.org/about/terms-of-use-agreement/) (200) otherwise restrict reuse but expressly let specific-content licences prevail. Scope for individual articles, images and third-party material remains to be checked; commercial reuse is not cleared. The live [disclaimer](https://canadiem.org/about/disclaimer-copyright/) confirms educational rather than institutional/standard-of-care authority.
- **HQIP — copyrighted; limited local-use provision.** Both live guidance pages reserve rights. The [audit page](https://www.hqip.org.uk/guidance/best-practice-in-clinical-audit/) expressly permits checklist adaptation for local use, not blanket redistribution. Live [copyright requests policy](https://www.hqip.org.uk/about-us/our-policies/copyright-requests/) (200) describes permissions and possible commercial fees. No redistribution permission was obtained for either guide.
- **NHS — OGL v3.0 with exclusions.** Live [NHS England terms](https://www.england.nhs.uk/terms-and-conditions-2/) (200) and all three source-page footers identify [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Terms exclude logos/photographs and identified third-party material; some case studies need contributor permission. Directory inclusion does not extend OGL to external tools or every downloadable attachment.
- **NQ — licence unresolved.** No explicit reuse grant was found on the live [resources page](https://nqican.org.uk/resources/). Treat it as a discovery link, not permission to copy its linked resources. Confirm rights with each owning publisher before reuse.
- **US — specific-resource rights unresolved.** The [AHRQ policies URL](https://www.ahrq.gov/policy/electronic/index.html) also returned direct 403; web-reader access later failed. Official indexed [publishing guidance](https://www.ahrq.gov/sites/default/files/publications/files/pcguide1.pdf) describes contractor/grantee copyright exceptions. It does not prove either toolkit's exact licence. Do not assume every item on a `.gov` domain is public domain; review each resource's copyright notice before reproduction.
- **AU — policy retrieved, current verification pending.** Official indexed [Commission copyright policy](https://www.safetyandquality.gov.au/using-website/disclaimer-and-copyright) states CC BY-NC-ND 4.0 unless otherwise specified: attribution, non-commercial exact copies, separate permission for adaptation/commercial use. The web search result displayed a crawl age of two weeks; page-reader access failed. The NSQHS page retrieved by the web reader says second edition remains in use while a third edition is developed. Neither indexed statement substitutes for fresh browser/manual verification of the page and applicable document-specific terms.

## Candidate and stale historical evidence

[Health Innovation Network's homepage](https://healthinnovationnetwork.com/) returned
direct 200 with the expected publisher title. This resolves homepage access only.
`SOURCE_POLICY.md` records a blocked July fetch without naming a resource URL;
the intended resource and its licence remain unknown. No candidate was added.
No later user-supplied PDF exists in the profile inventory to audit.

The July NSQHS browser verification in `RELEASE_READINESS.md` is historical proof,
not a fresh release exception. None of the 15 profile URLs was proven obsolete or
redirected, so no speculative URL replacement is proposed.

## Reviewable metadata patch and remaining proof

- Refresh `checked_on` to `2026-10-01` for 13 references to the 11 directly verified URLs in `standards/{australia,canada,global,uk}.json`.
- Match CanadiEM's live page title: `HiQuiPs (Quality Improvement)`.
- Clarify the existing Australian `url_check.reason`: July was the last browser verification; this audit's direct checks remain blocked and current manual proof is required.
- Preserve all seven blocked references' historical dates, all URLs, safety boundaries and checker flags. `standards/us.json` has no verified-date correction to make.
- Keep licence qualifications in this audit; no schema, CLI, source selection or clinical-method changes are proposed.

**Remaining before complete verification:** fresh manual/browser review of SQUIRE,
both AHRQ pages and NSQHS (including rights notices); publisher clarification for
N-QI-CAN and intended reuse where terms are qualified. Keep references as links
and original metadata; do not bundle third-party figures, checklists or policy text
on the strength of this audit. No permission requests or publication were made.

## Local validation

`PATH="$PWD/.venv/bin:$PATH" ./scripts/verify_changed.sh` passed: 127 tests,
compileall and all offline scaffold/de-id/run-chart/skill smoke checks.
`.venv/bin/python scripts/check_sources.py --dry-run` passed: all 20 references
listed. `git diff --check` passed. No lint/typecheck command is configured in
`pyproject.toml` or CI. Tests and smoke checks use synthetic fixtures; live GETs
above were separate read-only audit requests. No release/install/deployment claim
is made. The default Python initially lacked pytest; a worktree-local `.venv`
with pytest supplied the successful gate, without changing dependencies in the repo.
