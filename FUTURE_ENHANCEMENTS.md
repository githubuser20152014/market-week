# Framework Foundry Weekly — Future Enhancements

> **How to use this list:** Add new ideas with `[IDEA]`, promote to `[PLANNED]` when scoped, and `[IN PROGRESS]` when actively being built. Check the box when shipped. Keep items concise — link to code or MEMORY.md for implementation detail.

---

## 1. In Progress / Partially Built

- [ ] **Market IQ Flashcards — live data integration** `[IN PROGRESS]` `[HIGH]`
  - Mockup at `output/market-iq-flashcards_mockup.html` (hardcoded values, review only)
  - Needs auto-pull from existing fixtures / FRED / yfinance pipeline
  - Update cadences: CPI monthly (~2nd Tue, BLS), FFR 8×/yr (FOMC days), NFP monthly (1st Fri, BLS), PCE monthly (~last Fri, BEA), Yield Curve monthly snapshot

- [ ] **Market IQ → newsletter auto-linking with hover previews** `[IN PROGRESS]` `[HIGH]`
  - Post-render regex pass in `build_site.py` / `build_combined_site.py`
  - Maintain term→anchor mapping dict (abbreviations + full names + press shorthand, e.g. "PCE" / "personal consumption expenditures")
  - Add `id` anchors to each flashcard block (e.g. `id="cpi"`) in live page
  - Clicking a term navigates to its flashcard in the Market IQ section (same-site anchor link)
  - Hovering shows a tooltip popup with the flashcard's one-line definition + current value
  - Tooltip implementation: CSS + JS tooltip (no library needed); embed card summary data as `data-` attributes on each `<a>` tag at build time so the tooltip works without a network request
  - Tooltip should be keyboard-accessible (`:focus` triggers same as `:hover`)

- [ ] **Expat Investing section** `[IN PROGRESS]` `[MEDIUM]`
  - UI tab stub exists in `build_combined_site.py` (greyed out)
  - Needs content: cross-border tax considerations, currency hedging, PFIC rules, FBAR filing thresholds
  - Potentially a dedicated template / section in intl edition

---

## 2. Content & Analysis Enhancements

- [ ] **Sector ETF performance table** `[PLANNED]` `[HIGH]`
  - Weekly % change for XLK, XLF, XLE, XLU, XLV, XLI, XLB, XLY, XLP, XLRE
  - Sector rotation narrative in US weekly edition

- [ ] **Macro regime quadrant** `[PLANNED]` `[HIGH]`
  - 2×2 grid: inflation vs. growth → Reflation / Stagflation / Goldilocks / Deflation
  - Auto-classify current regime from CPI trend + GDP/PMI data
  - Color-coded label in newsletter header

- [ ] **CME FedWatch probabilities** `[PLANNED]` `[HIGH]`
  - Live Fed rate cut/hike odds for next 1–3 FOMC meetings
  - Pull from CME FedWatch API or scrape; display as bar or table

- [ ] **Earnings calendar integration** `[PLANNED]` `[MEDIUM]`
  - Highlight major S&P 500 earnings during peak seasons (Q1–Q4)
  - Source: Finnhub `/calendar/earnings` endpoint (already available)

- [ ] **Historical context overlays** `[PLANNED]` `[MEDIUM]`
  - "S&P 500 is X% above its 200-day MA"
  - "Yield curve has been inverted for N weeks"
  - Compute from fixture history; add to "What This Means" section

- [ ] **Breadth indicators** `[IDEA]` `[MEDIUM]`
  - Advance/decline line, % of S&P 500 stocks above 50-day MA, new 52-week highs/lows
  - Useful signal for confirming or diverging from index moves

- [ ] **Options sentiment** `[IDEA]` `[LOW]`
  - Put/call ratio, VIX term structure (spot vs. 3-month)
  - Source: CBOE data feed or free proxies

---

## 3. Distribution & Subscriber Engagement

- [ ] **RSS / Atom feed** `[PLANNED]` `[HIGH]`
  - Auto-generate `feed.xml` in `build_combined_site.py` on each site rebuild
  - Covers both US and intl editions; one feed per edition or combined

- [ ] **Self-service subscriber signup form** `[PLANNED]` `[MEDIUM]`
  - Formspree endpoint; appends email to `config/subscribers.txt`
  - Add form to site homepage / footer

- [ ] **Periodic feedback email to subscribers** `[IDEA]` `[MEDIUM]`
  - Send a short survey email to subscribers every 4–8 weeks asking what they find useful, what's missing, and overall satisfaction
  - Include a simple rating link (e.g. 1-click thumbs up/down or 1–5 star link) plus an open-text reply option
  - Track responses in a lightweight CSV or Google Form; use results to prioritize enhancements
  - Schedule via GitHub Actions cron or a manual trigger; reuse existing SMTP delivery code

- [ ] **Welcome / thank-you email on signup** `[IDEA]` `[MEDIUM]`
  - Automatically send a welcome email when a new subscriber joins
  - Include: brief intro to Framework Foundry Weekly, what to expect, link to latest edition
  - Trigger from signup form submission (Formspree webhook or a lightweight Flask/FastAPI endpoint)
  - Use existing SMTP email delivery code; add a `send_welcome_email(address)` helper

- [ ] **Unsubscribe link in email footer** `[PLANNED]` `[MEDIUM]`
  - One-click, token-based unsubscribe (generate token per subscriber)
  - Required for CAN-SPAM / GDPR compliance

- [ ] **Email open rate / click tracking** `[IDEA]` `[MEDIUM]`
  - Migrate from raw SMTP to Postmark or Mailchimp for analytics
  - Track open rates and link clicks per edition

- [ ] **Shareable weekly summary card** `[IDEA]` `[LOW]`
  - Auto-generate OG image / PNG snippet (top 3 moves + macro headline)
  - Use `Pillow` or a headless browser; attach to social post copy

- [ ] **Social media auto-post** `[IDEA]` `[LOW]`
  - Generate LinkedIn / Twitter/X text snippet from newsletter brief section
  - Manual review + post, or auto-post via API

---

## 4. Site / UX

- [ ] **Site-wide navigation** `[IDEA]` `[HIGH]`
  - Persistent nav bar on every page: Home | US Edition | International | Daily Brief | Market IQ | Archive
  - ~~"Back to Home" / breadcrumb link at the top and bottom of each newsletter edition page~~ ✅ shipped 2026-03-15
  - "Next edition →" / "← Previous edition" links at the bottom of each page for sequential reading
  - Active page highlighted in nav bar
  - Inject nav HTML in `build_site.py`, `intl_build_site.py`, and `build_combined_site.py` so all editions share the same header/footer
  - Mobile: collapse nav into a hamburger menu on narrow viewports

- [ ] **Interactive charts** `[PLANNED]` `[HIGH]`
  - Replace static matplotlib PNGs with Chart.js or Plotly (hover, zoom, tooltips)
  - Maintain static PNG fallback for email edition

- [ ] **Dark mode toggle** `[PLANNED]` `[MEDIUM]`
  - CSS custom properties + `prefers-color-scheme` media query auto-detection
  - Manual toggle button stored in `localStorage`

- [ ] **Archive search / browse** `[PLANNED]` `[MEDIUM]`
  - Filter archive by date range, edition type (US / intl / daily), or keyword
  - Client-side JS filter over generated index JSON

- [ ] **Historical chart overlays** `[IDEA]` `[MEDIUM]`
  - Compare this week vs. prior weeks on the same interactive chart
  - Pull from stored fixture history

- [ ] **Mobile-responsive polish** `[PLANNED]` `[MEDIUM]`
  - Current layout untested on narrow viewports
  - Audit tables, chart widths, and nav on 375px baseline

- [ ] **Canonical URLs and sitemap.xml** `[PLANNED]` `[LOW]`
  - Auto-generate `sitemap.xml` in `build_combined_site.py`
  - Add `<link rel="canonical">` to each edition page for SEO

- [x] **Visitor comments** `[SHIPPED]` `[MEDIUM]`
  - Implemented via Formspree comment form on main index and daily hub pages (2026-03-13)
  - Future upgrade: embed [Giscus](https://giscus.app/) (GitHub Discussions-backed) for threaded replies and reactions on individual edition pages

---

## 5. Data & Infrastructure

- [ ] **GitHub Actions cron automation** `[PLANNED]` `[HIGH]`
  - `.github/workflows/daily.yml` — runs `generate_newsletter.py --daily` each weekday
  - `.github/workflows/weekly.yml` — runs full US + intl generation each Monday
  - Eliminates manual shell runs; secrets stored in GitHub Actions environment

- [ ] **Market alert emails** `[PLANNED]` `[MEDIUM]`
  - Trigger email blast if S&P 500 moves ±2% intraday
  - Scheduled check (GitHub Action every 30 min during market hours)

- [ ] **Additional FRED macro indicators** `[PLANNED]` `[MEDIUM]`
  - ISM Manufacturing PMI, Retail Sales MoM, Housing Starts, Weekly Jobless Claims
  - Add to `fetch_data.py` FRED pull; display in US weekly "Key Indicators" table

- [ ] **Commodity focus data** `[PLANNED]` `[MEDIUM]`
  - Crude oil WTI & Brent, natural gas, copper, silver
  - Expand `config/indices.json` with commodity symbols; add to intl or standalone section

- [ ] **Data quality dashboard** `[IDEA]` `[LOW]`
  - Internal HTML page: fixture age, API success rate log, price discrepancy history
  - Auto-generate on each site rebuild; not public-facing

- [ ] **Automated fixture validation on CI** `[IDEA]` `[LOW]`
  - GitHub Action that validates fixture JSON schema and flags missing/stale fields
  - Runs on every push; blocks merge if fixture is malformed

---

## 6. International Expansion

- [ ] **Latin America coverage** `[IDEA]` `[MEDIUM]`
  - EWZ (Brazil), EWW (Mexico), ECH (Chile), iShares MSCI LatAm ETF
  - New intl section or standalone LatAm edition

- [ ] **India coverage** `[IDEA]` `[MEDIUM]`
  - SENSEX / NIFTY 50 (via yfinance: `^BSESN`, `^NSEI`)
  - Add to intl edition alongside existing Asia block

- [ ] **Commodity-focused edition** `[IDEA]` `[LOW]`
  - Targeted at oil exporters, metals, and agricultural commodity investors
  - Reuse intl template; swap index block for commodity block

- [ ] **Multi-language support** `[IDEA]` `[LOW]`
  - Template i18n layer (Jinja2 `gettext` or simple dict substitution)
  - Start with Spanish for LatAm edition; English default unchanged
