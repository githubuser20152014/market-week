Run the Framework Foundry Global Investor Edition generator with review checkpoints before publishing and before distributing.

Model assignment:
- Data collection (Step 0) → Haiku sub-agent (`/global-fetch`)
- Content creation + user review (Steps 1–2) → Sonnet (this agent)
- Publishing (Step 3) → Haiku sub-agent (`/global-publish`)
- Substack + social post display (Steps 4–5) → Sonnet (this agent)

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
cd weekly-newsletter && python generate_global_newsletter.py --date DATA_DATE
```

If DATA_DATE differs from PUB_DATE (e.g. Saturday publish with Friday data):
```bash
cd weekly-newsletter && python generate_global_newsletter.py --date DATA_DATE --pub-date PUB_DATE
```

Because Step 0 already wrote the fixtures, the generator will detect them and run without `--live`.

After running, read the generated Markdown file at `weekly-newsletter/output/global_newsletter_PUB_DATE.md` and display its full contents to the user for review.

**Step 2 — Review checkpoint (content):**

Ask the user:
> "Here's the Global Investor Edition for [PUB_DATE]. Does everything look good, or would you like any changes before I publish?"

Wait for the user's response. If they request changes, edit the `.md` file directly, then show the updated sections and ask again.

**Step 3 — Publish to web (only after user confirms content):**

Once the user approves, spawn a Haiku sub-agent to run the publish step:
- Use the `global-publish` skill with PUB_DATE as the argument
- Model: haiku

If STATUS is "error", display the PUBLISH_NOTES and stop.

**Step 4 — Show Substack content:**

Read the file at the path from SUBSTACK_FILE and display its full contents to the user. Tell the user:
> "The site is live. Here's the Substack HTML — paste this into the Substack editor:"

Then show the full HTML content.

**Step 5 — Show social posts:**

Read and display the X thread (X_THREAD_FILE) and LinkedIn post (LINKEDIN_FILE) one at a time. Tell the user:
> "Here are your social posts for [date]:"

Show X thread first, then LinkedIn post.

If $ARGUMENTS is empty, use today's date for all steps.
