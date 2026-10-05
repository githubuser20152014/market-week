---
name: Email and Substack formatting standards
description: Subscriber emails must include Framework Foundry banner; Substack posts must be HTML
type: feedback
originSessionId: c0f055ba-89fc-4342-b061-32b252e61b13
---
All emails sent to subscribers via `send_custom_email.py` must include the **Framework Foundry banner** in the email body/template.

All content destined for Substack must be delivered as **HTML** (not Markdown), saved to `output/` and ready to paste into the Substack editor. Substack does not render raw Markdown.

**Why:** Markdown posts pasted into Substack lose formatting. HTML paste preserves bold, italics, links, and dividers correctly.

**How to apply:**
- When creating subscriber emails: ensure the banner is present (either in the message file or rendered by `build_email_html`).
- When creating Substack content: always produce/save an `.html` file in `output/`, not just the `.md` source.

### Substack HTML — table rendering rules (confirmed 2026-04-11)

Substack does not render HTML tables when pasted. Two fixes applied to all future Global Investor Edition Substack posts:

1. **Macro Regime Snapshot** — convert from `<table>` to `<ul>` list. Format: `<li><strong>Variable · SIGNAL</strong> - note text</li>`
2. **Data Appendix** — remove all data tables entirely. Replace with a single CTA line linking to the web edition:
   `<p><em>Full data tables (...): <a href="URL">frameworkfoundry.info/global/YYYY-MM-DD</a></em></p>`

**Why:** HTML tables get stripped or mangled when pasted into Substack's editor. `<ul>`, `<p>`, `<strong>`, `<h3>`, `<hr>`, `<a>` all paste cleanly.
