Run the Framework Foundry Global Investor Edition generator with review checkpoints before publishing and before distributing.

Model assignment:
- Data collection (Step 0) → Haiku sub-agent (`/global-fetch`)
- Content creation + user review (Steps 1–4) → Sonnet (this agent)
- Publishing (Step 5) → Haiku sub-agent (`/global-publish`)

**Step 0 — Fetch & Verify Market Data:**

1. Determine PUB_DATE (publication date):
   - If $ARGUMENTS is provided, use that as PUB_DATE.
   - Otherwise use today's date.
2. Determine DATA_DATE (fixture/trading date):
   - If PUB_DATE falls on a Saturday, DATA_DATE = PUB_DATE minus 1 day (Friday).
   - If PUB_DATE falls on a Sunday, DATA_DATE = PUB_DATE minus 2 days (Friday).
   - Otherwise DATA_DATE = PUB_DATE.
3. Check if all three fixtures already exist for DATA_DATE — if so, skip to Step 1:
   - `weekly-newsletter/fixtures/global_equity_DATA_DATE.json`
   - `weekly-newsletter/fixtures/global_fx_DATA_DATE.json`
   - `weekly-newsletter/fixtures/global_commodity_DATA_DATE.json`
4. If fixtures are missing, spawn a Haiku agent to run the fetcher and return a structured report:
   - Use the `global-fetch` skill with DATA_DATE as the argument
   - Model: haiku
5. Display the summary table and any flagged assets to the user.
6. If STATUS is "flagged" or any assets are listed in FLAGGED_ASSETS, ask the user to confirm or provide a manual correction before proceeding.
7. If STATUS is "ok" and no flags, inform the user the data looks clean and proceed automatically.

**Step 1 — Generate the Markdown only:**

If DATA_DATE equals PUB_DATE:
```bash
cd weekly-newsletter && python generate_global_newsletter.py --date DATA_DATE --digest-dir "C:/Users/Akhil/Documents/ContentRepo/07-Reading/news-digest"
```

If DATA_DATE differs from PUB_DATE (e.g. Saturday publish with Friday data):
```bash
cd weekly-newsletter && python generate_global_newsletter.py --date DATA_DATE --pub-date PUB_DATE --digest-dir "C:/Users/Akhil/Documents/ContentRepo/07-Reading/news-digest"
```

Because Step 0 already wrote the fixtures, the generator will detect them and run without `--live`.

After running, read the generated Markdown file at `weekly-newsletter/output/global_newsletter_PUB_DATE.md` and display its full contents to the user for review.

**Step 2 — Review checkpoint (content):**

Before displaying the draft to the user, run a pre-flight style check on the generated markdown. Check each of the following and report any violations:

- [ ] No em dashes (—) anywhere in the file
- [ ] No banned phrases: "amid concerns", "market participants", "investors remain cautious", "volatility persists", "risk sentiment"
- [ ] `one_trade_body` opens with the signal or anomaly, not the action ("Consider..." or "If conditions..." = flag it)
- [ ] Each narrative section has ≥2 **bold** callouts (flag if fewer)
- [ ] `big_theme_title` is 6–10 words and punchy (flag if generic, e.g. "Markets Navigate Crosscurrents")
- [ ] Narrative sections name specific events from the week's news (not vague price-correlation language)

If any violations are found, list them clearly, fix what can be fixed by editing the `.md` directly, then display the corrected draft.

Then ask the user:
> "Here's the Global Investor Edition for [PUB_DATE]. Does everything look good, or would you like any changes before I write the Substack post?"

Wait for the user's response. If they request changes, edit the `.md` file directly, then show the updated sections and ask again.

**Step 3 — Generate Substack post (only after user approves markdown):**

Using the approved markdown as the sole content source, write the Substack HTML and save it to `weekly-newsletter/output/global_substack_PUB_DATE.html`.

Format requirements:
- **Opening hook:** 2–3 short punchy paragraphs. Lead with the week's dominant theme, anomaly, or divergence — not a summary. First visible section ends with a kicker in `<em>italics</em>`.
- **`<h2>Here's my read:</h2>`** — the macro driver paragraph. Bold key data points. Italics on punchline phrases.
- **`<h2>The One Trade: DIRECTION <a href="https://finance.yahoo.com/quote/TICKER">$TICKER</a></h2>`** — the ticker MUST be a Yahoo Finance hyperlink, never plain text. Use "Kill switch:" not "Risk:". Italics on the consequence ("get out *fast*").
- **`<h2>What else I'm watching</h2>`** — global positioning bullets with personality. Use language like "don't you dare sell it", "stay away from", "the trade nobody is talking about".
- Bold key numbers and verdicts. Italics on punchlines. Don't over-emphasize — save it for the moments that land hardest.
- Footer: link to `frameworkfoundry.info/global/PUB_DATE/` and `frameworkfoundrymkt.substack.com`
- No em dashes (—) anywhere — use " - " instead.
- Voice: edgy, opinionated, conviction-led. State opinions as facts. Short sentences. No hedging.

Pre-flight check before displaying:
- [ ] No em dashes (—) anywhere — fix if found
- [ ] Ticker in One Trade `<h2>` is a Yahoo Finance hyperlink (not plain text)
- [ ] Uses "Kill switch:" not "Risk:"
- [ ] No banned phrases: "amid concerns", "market participants", "investors remain cautious", "volatility persists", "risk sentiment"
- [ ] Footer links to `/global/PUB_DATE/` (not `/daily/`)

Fix any violations, then display the full HTML to the user. Ask:
> "Here's the Substack draft for [PUB_DATE]. Any changes?"

Wait for the user's response and apply any requested edits before proceeding.

**Step 4 — Generate LinkedIn + X posts (only after user approves Substack):**

Using the approved markdown as sole source, write both files.

**LinkedIn post** → `weekly-newsletter/output/global_linkedin_PUB_DATE.md`

Structure:
- **Hook** (2–3 lines before the fold): contrarian read on the week's dominant global theme — "here's why you shouldn't trust it"
- **The dissenting markets**: bonds, gold, crude each get their own short paragraph. Explain *why* the non-move matters — don't just report it.
- **Corporate proof point**: one earnings result or data release that makes the macro thesis concrete
- **The second-order story**: the angle nobody is covering (commodities, supply chains, EM spillover, currency dislocations, etc.)
- **The verdict**: direct question framing — "which market got it right?" — then answer it with conviction
- **CTA**: "Full analysis in the Global Investor Edition" + `frameworkfoundrymkt.substack.com`
- **Hashtags**: 4–5, relevant to the week's global themes
- Length: ~2,000–2,800 characters

Hard rules for LinkedIn:
- **NO stock recommendations, entry/exit price levels, or directional trade calls.** No "Long $GLD", no "Entry confirm:", no "Kill switch:", no tickers with buy/sell direction.
- **CTA URL must be exactly `frameworkfoundrymkt.substack.com`** — the root domain, NOT a specific note URL (/p/...).
- CTA text: "Read on Substack →" (not "Full breakdown").
- No em dashes (—) — use " - " instead.

**X thread** → `weekly-newsletter/output/global_x_thread_PUB_DATE.md`

5 tweets, ≤280 characters each:
- **Tweet 1 — Hook**: the week's dominant global theme or anomaly; the one-line reason why it matters. Short, punchy, accusatory.
- **Tweet 2 — Dissenting markets**: what bonds, gold, and crude were saying at the same time equities celebrated. Each as a one-liner.
- **Tweet 3 — Corporate proof point**: the specific company result or data release that confirmed the macro thesis.
- **Tweet 4 — Second-order angle**: the story nobody is covering.
- **Tweet 5 — The verdict**: "one of them is wrong" close + CTA → frameworkfoundrymkt.substack.com + 3–5 hashtags.

Hard rules for X:
- **NO $CASHTAGS with directional labels.** No "Long $GLD", no "Short $IWM".
- **NO price levels, no "Entry confirm:", no "Kill switch:" language.**
- Pure analysis and macro opinion only.
- No em dashes (—) — use " - " instead.
- CTA text: "Read on Substack:" (not "Full breakdown").

Pre-flight check on both files before displaying:
- [ ] No em dashes (—) in either file — fix if found
- [ ] No stock picks or directional calls in either file
- [ ] LinkedIn CTA URL is exactly `frameworkfoundrymkt.substack.com` (not a /p/ note URL)
- [ ] X CTA says "Read on Substack:" (not "Full breakdown")
- [ ] No banned phrases in either file

Fix any violations, then display both files in full. Ask:
> "Here are the LinkedIn and X posts for [PUB_DATE]. Any changes?"

Wait for the user's response and apply any requested edits before proceeding.

**Step 5 — Publish to web (only after user approves all social posts):**

Spawn a Haiku sub-agent to run the publish step and return a report:
- Use the `global-publish` skill with PUB_DATE as the argument
- Model: haiku

If STATUS is "error", display the PUBLISH_NOTES and stop.

After the sub-agent confirms success, commit the social post files:
```bash
git add weekly-newsletter/output/global_substack_PUB_DATE.html weekly-newsletter/output/global_linkedin_PUB_DATE.md weekly-newsletter/output/global_x_thread_PUB_DATE.md
git commit -m "Add approved social posts for PUB_DATE"
git push
```

Inform the user:
> "Site is live at frameworkfoundry.info/global/[PUB_DATE]/. Social posts are saved in output/.
>
> **Next steps:**
> 1. **Publish Substack first** — paste `global_substack_PUB_DATE.html` into the Substack editor, publish the note.
> 2. Copy the live Substack note URL (the /p/... URL).
> 3. In `global_x_thread_PUB_DATE.md`, replace `frameworkfoundrymkt.substack.com` in the CTA with the live note URL.
> 4. Post the X thread using the updated URL.
> 5. Post LinkedIn as-is (root domain stays)."

If $ARGUMENTS is empty, use today's date for all steps.
