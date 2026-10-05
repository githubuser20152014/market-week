---
name: The Blueprint series
description: Wednesday investing guide series on Framework Foundry — audience, naming, file locations, launch status, article pipeline
type: project
---

Framework Foundry's Wednesday content series is called **The Blueprint**.

**Why:** Midweek cadence to complement the weekly newsletter. Builds a foundational investing library and keeps subscribers engaged between Saturday editions.

**Audience:** Late 40s / early 50s. Investing-illiterate but not financially illiterate. Already have 401(k)/IRA accounts they haven't looked at closely. Closer to retirement, so stakes are higher than for younger beginners.

**Branding:** Header tagline on article pages reads "The Blueprint · Practical Investing Guides" (replaces standard "Economic Intelligence · Research for the Serious Investor" tagline).

## Key Files (ContentRepo)
- **Audience persona:** `ContentRepo/wednesday-series/audience-persona.md` — always read this before drafting any Blueprint article
- **Article pipeline:** `ContentRepo/wednesday-series/article-pipeline.md` — working titles, briefs, publish dates, and on-deck ideas for the full series
- **Published issues:** `ContentRepo/wednesday-series/Issues/` — all article drafts live here

## Articles

### Issue #1 — "The one decision that controls 90% of your returns"
**Topic:** Asset allocation
- Live URL: frameworkfoundry.info/investing-101/asset-allocation/
- Article draft: `ContentRepo/wednesday-series/Issues/asset-allocation-the-one-decision.md`
- Site source: `content/articles/investing-101-asset-allocation.md`
- Chart: `data/generate_asset_allocation_chart.py` → `site/assets/asset-allocation-growth.png`
- Social copy: `ContentRepo/wednesday-series/social-asset-allocation.md`
- Subscriber email: `messages/blueprint_launch.md`
- Launch checklist: `messages/blueprint_launch_sequence.md`
- **Published:** Wednesday 2026-03-19

### Issue #2 — "You probably have 12 funds. You need 2."
**Topic:** Two-fund portfolio, index funds, expense ratios introduced
- Article draft: `ContentRepo/wednesday-series/Issues/two-fund-portfolio.md`
- Site source: `content/articles/investing-101-two-fund-portfolio.md`
- Chart: `data/generate_fund_overlap_chart.py` → `site/assets/fund-overlap.png`
- Social copy: `ContentRepo/wednesday-series/social-two-fund-portfolio.md`
- **Publish date:** Wednesday 2026-03-26
- **Status:** Written, social copy done — DO NOT publish until explicitly instructed. Site output intentionally excluded from repo. To publish: run build_combined_site.py, commit site/investing-101/two-fund-portfolio/, push.

### Issue #3 — "Your 70/30 portfolio is probably 82/18 right now"
**Topic:** Rebalancing — what it is, why it happens, how to do it
- **Publish date:** Wednesday 2026-04-02
- Brief: see `ContentRepo/wednesday-series/article-pipeline.md`

### Issue #4 — "The fee that's quietly costing you $80,000"
**Topic:** Expense ratios — compounding cost drag, how to find yours
- **Publish date:** Wednesday 2026-04-09
- Brief: see `ContentRepo/wednesday-series/article-pipeline.md`

## Pending: Add "The Blueprint" to subscriber email banner
The subscriber email banner currently shows only the Framework Foundry branding.
Before sending Issue #2, update the email template (`data/email_sender.py` or equivalent)
to include "The Blueprint" in the banner so Blueprint emails are visually distinct.

## WhatsApp message template (use for every issue)

```
https://frameworkfoundry.info/investing-101/{slug}/

*The Blueprint · Issue #{N} — out now*

*A new Wednesday series from Framework Foundry: practical investing guides for people who want to understand what they're doing and why. Not theory. Not jargon. Frameworks you can actually use.*

---

[2–3 paragraphs of body content, with one bold key stat]

---
*The Blueprint runs every Wednesday. Also on the site: daily market briefings and the weekly macro newsletter — https://frameworkfoundry.info*
```

Notes:
- URL goes first so WhatsApp renders the og:title preview ("article title") at the top
- Series description line stays the same every week
- Reference file for Issue #1: `ContentRepo/wednesday-series/social-asset-allocation.md`

## How to apply
- Always read `audience-persona.md` and the relevant section of `article-pipeline.md` before drafting
- Read all previously published issues in `ContentRepo/wednesday-series/Issues/` before drafting a new one
- Follow the same file naming pattern (`investing-101-{slug}.md` in content/articles)
- Use `series: The Blueprint` in frontmatter
- Add the article URL to the `url` frontmatter field so the Investing panel on the landing page links correctly
- Every article must include a concrete worked example with ages + dollar figures, define all foundational terms, end with one specific action, and close with a specific tease for the next issue
