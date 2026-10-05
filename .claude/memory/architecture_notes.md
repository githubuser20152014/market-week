---
name: architecture-notes-chart-pdf-prefixes-site-rebuild-fundaa-dates
description: "Misc pipeline implementation details — chart/PDF filename params, site rebuild steps, fundaa date filter, stale fixture warning"
metadata: 
  node_type: memory
  type: project
  originSessionId: e03b998a-3cab-497f-abac-389a5dd8f548
  modified: 2026-07-25T11:37:52.647Z
---

### generate_price_chart(prefix=)
`data/chart.py` accepts a `prefix` param (default `"chart"`). Always pass
`prefix="intl_chart"` when calling from `generate_intl_newsletter.py` to
avoid clobbering the US chart for the same date.

### generate_pdf(filename=)
`data/pdf_export.py` accepts a `filename` param (default `newsletter_{date}.pdf`).
Always pass `filename=f"intl_newsletter_{date_str}.pdf"` from the intl generator
to avoid clobbering the US PDF for the same date.

### Newsletter generation order
Running both generators for the same date is safe **only if** the above params
are used. The intl generator used to rename outputs, deleting the US files.

### Hosting
GitHub Pages serves the site. Porkbun DNS forwards `frameworkfoundry.info` to
GitHub Pages (NOT Cloudflare Pages). A `git push` to `origin/master` is all
that's needed to deploy.

### Site rebuild workflow
1. `generate_newsletter.py --date YYYY-MM-DD --pdf --live --no-verify`
2. `generate_intl_newsletter.py --date YYYY-MM-DD --pdf --live` (if intl needed)
3. `build_combined_site.py`
4. Commit `site/`, updated `output/` files, new `fixtures/` files
5. Push → GitHub Pages deploys automatically

**Critical:** Always use `--live` when generating for a new week — both
generators auto-save live yfinance data as fixtures so `build_combined_site.py`
uses the same verified prices. Without `--live`, the builder falls back to
the nearest old fixture and shows stale/wrong prices. See also
[[project_global_publish_incident_2026-07-25]] for a case where the fixture
lookup silently regenerated content instead of reusing an approved edition.

### Site links must use explicit index.html paths
`build_combined_site.py` generates links as `us/YYYY-MM-DD/index.html` (not
trailing slash) — trailing-slash directory links don't auto-load index.html
over `file://` protocol.

### "What This Means" section
Both US and intl newsletters have a plain-English investor summary after
"The Week in Brief". US: `generate_plain_english_summary()` in
`data/process_data.py`. Intl: `generate_intl_plain_english_summary()` in
`data/intl_process_data.py`. Template var `plain_summary` (both editions).
Site rendering: `build_site.py` (US), `intl_build_site.py` (intl).

### Fundaa date filter — allows 1 day ahead
`parse_fundaa_articles()` in `build_combined_site.py` filters articles to
`date <= today + timedelta(days=1)`, letting a Friday article go live
Thursday without waiting for the calendar to roll over.

### Stale fixture warning
`fetch_data.py` prints a WARNING if the closest fixture is >2 days from the
requested date — means data is stale, use `--live` or create a new fixture.

### Price verification (--verify flag)
`generate_newsletter.py --live --verify` cross-checks yfinance prices against
FRED + Stooq before generating. Raises `PriceDiscrepancyError` if any asset
diverges >2%.
