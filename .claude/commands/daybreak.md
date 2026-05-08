Run the Market Day Break generator with review checkpoints before publishing.

Model assignment:
- Data collection (Step 0) → Haiku sub-agent (`/daybreak-fetch`)
- Content creation + user review (Steps 1–4) → Sonnet (this agent)
- Site publish (Step 5) → Haiku sub-agent (`/daybreak-publish`)

**Step 0 — Fetch & Verify Market Data:**

1. Determine DATE from $ARGUMENTS (or today if empty).
2. Check if `weekly-newsletter/fixtures/daybreak_DATE.json` already exists — if so, skip to Step 1.
3. Spawn a Haiku agent to run the fetcher and return a structured report:
   - Use the `daybreak-fetch` skill with DATE as the argument
   - Model: haiku
4. Display the summary table and any flagged assets to the user.
5. If STATUS is "flagged" or any assets are listed in FLAGGED_ASSETS, ask the user to confirm or provide a manual correction before proceeding.
6. If STATUS is "ok" and no flags, inform the user the data looks clean and proceed automatically.

**Step 1 — Generate the Markdown only:**

```bash
bash weekly-newsletter/publish_daybreak.sh $ARGUMENTS
```

Because Step 0 already wrote the fixture, the script will detect it and run without `--live`.

After running, read the generated Markdown file and display its full contents to the user for review.

**Step 2 — Review checkpoint: markdown**

Before displaying the draft to the user, run a pre-flight style check on the generated markdown. Check each of the following and report any violations:

- [ ] No em dashes (—) anywhere in the file — fix by replacing with " - "
- [ ] `narrative` section is 2–3 sentences max, no boilerplate opener ("Markets showed...", "Stocks were...", "In a session marked by...")
- [ ] `one_trade` thesis starts with the signal or anomaly, not the action ("Consider..." or "If conditions..." = flag it)
- [ ] Uses "Kill switch:" not "Risk:" in the One Trade block
- [ ] No banned phrases: "amid concerns", "market participants", "investors remain cautious", "volatility persists", "risk sentiment"
- [ ] Bold callouts in plain_summary: at least 4 (if fewer, note it)

Fix any violations by editing the `.md` directly.

**Narrative tone check — apply after fixing violations:**

Rewrite **The Brief** and **What it means for you** sections if they read as plain financial reporting. The approved tone is cheeky, irreverent, dark humor: short punchy sentences, a sarcastic observation after each data point, dry wit on the macro themes. Guidelines:
- Lead with the market's contradiction or absurdity, not a neutral summary
- After stating a number, add the pointed observation ("because small-caps are the canaries of domestic credit, and right now they are canaries with a cough")
- Dark humor on geopolitical and earnings catalysts — treat them as darkly comic, not tragic
- "The smart money voted with its wallet and the wallet voted for gold" style conclusions
- Short sentences. Never more than two clauses. Sarcasm over hedging.
- All numbers and tickers must stay accurate — tone changes the delivery, not the data
- Reference: `C:\Users\Akhil\Documents\ContentRepo\00-Dashboard\Vibe-Check.md` for the exact voice

**Title generation — run after narrative tone check:**

Generate 5 title options and write them to `weekly-newsletter/output/title_DATE.txt` (one per line, numbered). Do NOT pick one — present all 5 and ask the user to choose.

Title rules:
- Must contain at least one specific number from the day's data (price, %, bps, count)
- Must be punchy: short sentences, period-separated, no em dashes
- Should expose a contradiction, dark irony, or absurdity in the session
- Dark humor and wit are features, not bugs
- Style reference — the 2026-05-08 approved title: *"The Ceasefire Had a Great 24 Hours. Gold Hit $4,727 Anyway."*
- More examples of the pattern:
  - "[Thing that should have worked] had [timeframe]. [Asset/number] didn't care."
  - "[N] markets voted [X]. [1 market/number] voted [Y]. [Event] settles it."
  - "[Ironic observation with number]. [Darker punchline with number]."
  - "[$Number]. [Dark observation]. [Escalating punchline]."

Display the 5 options. Wait for user to pick one before proceeding. Write the chosen title back to `title_DATE.txt` (single line, no number prefix).

Display the corrected draft with the chosen title, then ask:
> "Here's the newsletter for [date]. Does everything look good, or would you like any changes before I write the social posts?"

Wait for the user's response. If they request changes, make the edits to the `.md` file directly, then show the updated sections and ask again.

**Step 3 — Generate Substack post (only after user approves markdown):**

Using the approved markdown as the sole content source, write the Substack HTML and save it to `weekly-newsletter/output/substack_DATE.html`.

Format requirements:
- **Title + subtitle at the top** (added only after the user has approved the final title):
  ```html
  <h1>[APPROVED TITLE]</h1>
  <p><em>The Morning Brief · Market intelligence at the open</em></p>
  ```
- **Opening hook:** 2–3 short punchy paragraphs. Lead with the accusation or anomaly — not a summary. First visible section ends with a kicker in `<em>italics</em>`.
- **`<h2>Here's my read:</h2>`** — the macro driver paragraph. Bold key data points. Italics on punchline phrases.
- **`<h2>The One Trade: DIRECTION <a href="https://finance.yahoo.com/quote/TICKER">$TICKER</a></h2>`** — the ticker MUST be a Yahoo Finance hyperlink, never plain text. Use "Kill switch:" not "Risk:". Italics on the consequence ("get out *fast*").
- **`<h2>What else I'm watching</h2>`** — positioning bullets with personality. Use language like "don't you dare sell it", "stay away from", "the trade nobody is talking about".
- Bold key numbers and verdicts. Italics on punchlines. Don't over-emphasize — save it for the moments that land hardest.
- Footer: link to `frameworkfoundry.info/daily/DATE/` and `frameworkfoundrymkt.substack.com`
- No em dashes (—) anywhere — use " - " instead.
- Voice: cheeky, irreverent, dark humor. State opinions as facts. Short sentences. No hedging. Lead with the absurdity or contradiction, not the summary. Sarcastic observations after data points. The 2026-05-08 edition is the reference for narrative tone; the April 23 2026 edition is the reference for One Trade structure.

Save the file, then display the full HTML to the user. Ask:
> "Here's the Substack draft for [date]. Any changes?"

Wait for the user's response and apply any requested edits before proceeding.

**Step 4 — Generate LinkedIn + X posts (only after user approves Substack):**

Using the approved markdown as sole source, write both files.

**LinkedIn post** → `weekly-newsletter/output/linkedin_DATE.txt`

Structure:
- **Hook** (2–3 lines before the fold): contrarian read on yesterday's move — "here's why you shouldn't trust it"
- **The dissenting markets**: bonds, gold, crude each get their own short paragraph. Explain *why* the non-move matters — don't just report it.
- **Corporate proof point**: one earnings result that makes the macro thesis concrete
- **The second-order story**: the angle nobody is covering (ag, fertilizer, food, supply chain, etc.)
- **The verdict**: direct question framing — "which market got it right?" — then answer it with conviction
- **CTA**: "Full analysis in today's Morning Brief" + `frameworkfoundrymkt.substack.com`
- **Hashtags**: 4–5, relevant to the day's themes
- Length: ~2,000–2,800 characters

Hard rules for LinkedIn:
- **NO stock recommendations, entry/exit price levels, or directional trade calls.** No "Long $GLD", no "Entry confirm:", no "Kill switch:", no tickers with buy/sell direction.
- **CTA URL must be exactly `frameworkfoundrymkt.substack.com`** — the root domain, NOT a specific note URL (/p/...).
- CTA text: "Read on Substack →" (not "Full breakdown").

**X thread** → `weekly-newsletter/output/x_DATE.txt`

5 tweets, ≤280 characters each:
- **Tweet 1 — Hook**: the market did something; here's the one-line reason why. Short, punchy, accusatory.
- **Tweet 2 — Dissenting markets**: what bonds, gold, and crude were saying at the same time equities celebrated. Each as a one-liner.
- **Tweet 3 — Corporate proof point**: the specific company result that confirmed the macro thesis.
- **Tweet 4 — Second-order angle**: the story nobody is covering.
- **Tweet 5 — The verdict**: "one of them is wrong" close + CTA → frameworkfoundrymkt.substack.com + 3–5 hashtags.

Hard rules for X:
- **NO $CASHTAGS with directional labels.** No "Long $GLD", no "Short $IWM".
- **NO price levels, no "Entry confirm:", no "Kill switch:" language.**
- Pure analysis and macro opinion only.
- CTA text: "Read on Substack:" (not "Full breakdown").

Pre-flight check on both files before displaying:
- [ ] No stock picks or directional calls in either file
- [ ] LinkedIn CTA URL is exactly `frameworkfoundrymkt.substack.com` (not a /p/ note URL)
- [ ] X CTA says "Read on Substack:" (not "Full breakdown")
- [ ] No em dashes (—) in either file — fix if found

Fix any violations, then display both files in full. Ask:
> "Here are the LinkedIn and X posts for [date]. Any changes?"

Wait for the user's response and apply any requested edits before proceeding.

**Step 5 — Publish to web (only after user approves all social posts):**

Before running the publish command, save the full approved content of all three social post files in memory (you will need to restore them after the publish command runs).

Spawn a Haiku sub-agent to run the publish step and return a report:
- Use the `daybreak-publish` skill with DATE as the argument
- Model: haiku

If STATUS is "error", display the PUBLISH_NOTES and stop.

After the sub-agent confirms success, immediately restore the approved social post files (the publish command regenerates these from scratch and overwrites them):
- Write the approved Substack content back to `weekly-newsletter/output/substack_DATE.html`
- Write the approved LinkedIn content back to `weekly-newsletter/output/linkedin_DATE.txt`
- Write the approved X content back to `weekly-newsletter/output/x_DATE.txt`

Then run:
```bash
git add weekly-newsletter/output/substack_DATE.html weekly-newsletter/output/linkedin_DATE.txt weekly-newsletter/output/x_DATE.txt
git commit -m "Restore approved social posts for DATE"
git push
```

Inform the user:
> "Site is live at frameworkfoundry.info/daily/[DATE]/. Social posts are saved in output/.
>
> **Next steps:**
> 1. **Publish Substack first** — paste `substack_DATE.html` into the Substack editor, publish the note.
> 2. Copy the live Substack note URL (the /p/... URL).
> 3. In `x_DATE.txt`, replace `frameworkfoundrymkt.substack.com` in the CTA with the live note URL.
> 4. Post the X thread using the updated URL.
> 5. Post LinkedIn as-is (root domain stays)."

If $ARGUMENTS is empty, use today's date for all steps.
