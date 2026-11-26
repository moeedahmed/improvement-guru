# Before submitting: decisions and steps for the publisher

Nothing in this package has been submitted, published or signed up for, and no money has been spent.

## Decisions

1. **Publisher identity.** Verify as an individual (Moeed Ahmed) in the OpenAI Platform organisation settings. The directory shows the verified name, whatever the package says.
2. **Support contact.** Confirm public GitHub Issues (draft default) or approve help@portfolioguru.app. If email is selected, confirm the inbox is appropriate for this product, update the public policy and support copy, and point the listing's support URL at the public support page.
3. **Privacy policy and terms.** Approve publishing both pages at their GitHub HTTPS URLs on main. The terms link targets the Terms of use heading. Check both URLs signed out after publication and before submitting. Publishing date may differ from the revision date stated on the pages. If the portal cannot use the GitHub pages, agree a replacement location first.
4. **Clinician review.** Use the clinician wording note at the end of REVIEW_TESTS.md.
5. **Listing text and icon.** Review the name, short description, long description, starter prompts, icon and category (proposed: Education & Research rather than Healthcare, because this is an educational planning aid).
6. **Countries.** The package sets no country restriction: UK-first content, usable anywhere. The alternative is the UK only.
7. **Skills-only now.** OpenAI says a server cannot currently be added to an existing skills-only listing, so a later version with a server may need a new listing.
8. **Eligibility.** OpenAI says skills-only listings may face additional eligibility requirements, which are not published.

## Steps

1. After approval to push, update draft PR #21. Publish the two policy pages after separate approval and verify their listing URLs.
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

## Local assumptions

- The 90-day period applies to private support records after closure. It allows follow-up on fixes without keeping routine correspondence indefinitely. Public GitHub posts can remain visible as troubleshooting records under GitHub's own policy. Confirm the maintainer can honour the private retention period and respond to privacy requests before publishing. [ICO storage limitation](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/storage-limitation/).
- Public GitHub Issues remains a draft default. No support decision or public release is recorded by this change.
