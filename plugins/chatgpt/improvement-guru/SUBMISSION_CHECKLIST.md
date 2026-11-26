# Before submitting: decisions and steps for the publisher

Nothing in this package has been submitted, published or signed up for, and no money has been spent.

## Decisions

1. **Publisher identity.** Verify as an individual (Moeed Ahmed) in the OpenAI Platform organisation settings. The directory shows the verified name, whatever the package says.
2. **Support contact.** Confirm the proposed route (public GitHub Issues on this repository) or choose another, then replace the placeholders in `SUPPORT.md`, `PRIVACY.md` and `TERMS.md`.
3. **Privacy policy and terms.** Review both drafts. They must be published at public HTTPS links that name the same publisher. The proposed links are these files on GitHub after merge. Reviewers may or may not accept GitHub-hosted policies; a simple page on a personal website is the fallback.
4. **Clinician review.** Review the wording in the skill, the worked example and the listing text.
5. **Listing text and icon.** Review the name, short description, long description, starter prompts, icon and category (proposed: Education & Research rather than Healthcare, because this is an educational planning aid).
6. **Countries.** The package sets no country restriction: UK-first content, usable anywhere. The alternative is the UK only.
7. **Skills-only now.** OpenAI says a server cannot currently be added to an existing skills-only listing, so a later version with a server may need a new listing.
8. **Eligibility.** OpenAI says skills-only listings may face additional eligibility requirements, which are not published.

## Steps

1. Merge the pull request so the privacy and terms links work.
2. Run every prompt in `REVIEW_TESTS.md` in ChatGPT with the plugin installed, and record the results.
3. Build the ZIP: `python3 scripts/build_chatgpt_plugin.py`.
4. Upload the ZIP in the Plugins dashboard, fix any findings, wait for the skill scans (up to 2 hours), complete the policy attestations and submit for review.
5. After approval, choose when to publish.

## Requirements checked on 26 November 2026

- Package and submit: https://developers.openai.com/plugins/deploy/submission
- Submission rules and errors: https://developers.openai.com/plugins/deploy/submission-errors
- Package layout: https://developers.openai.com/plugins/build/plugins
- Skills: https://developers.openai.com/plugins/build/skills
- Plugin guidelines: https://developers.openai.com/plugins/plugin-guidelines
