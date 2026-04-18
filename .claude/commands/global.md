Run the Framework Foundry Global Investor Edition generator with robust data fetching and verification.

**Step 0 — Fetch & Verify Market Data:**

1. Determine DATE from $ARGUMENTS (or today if empty).
2. Check if all three fixtures already exist — if so, skip to Step 1:
   - `weekly-newsletter/fixtures/global_equity_DATE.json`
   - `weekly-newsletter/fixtures/global_fx_DATE.json`
   - `weekly-newsletter/fixtures/global_commodity_DATE.json`
3. Run the fetcher and return a structured report:
   ```bash
   python weekly-newsletter/data/fetch_and_verify_global.py --date DATE
   ```
4. Display the summary table and any flagged assets to the user.
5. If any assets are flagged (SANITY or VERIFY), ask the user to confirm or provide a manual correction before proceeding.
6. If all checks passed ([OK]), inform the user the data looks clean and proceed.

**Step 1 — Generate the Markdown only:**

```bash
cd weekly-newsletter && python generate_global_newsletter.py --date DATE
```

Because Step 0 already wrote the fixtures, the generator will detect them and run without `--live`.

After running, read the generated Markdown file at `weekly-newsletter/output/global_newsletter_DATE.md` and display its full contents to the user for review.

**Step 2 — Review checkpoint:**

Ask the user:
> "Here's the Global Investor Edition for [date]. Does everything look good, or would you like any changes before I publish?"

Wait for the user's response. If they request changes, edit the `.md` file directly, then show the updated sections and ask again.

**Step 3 — Publish (only after user confirms content):**

```bash
bash weekly-newsletter/publish_weekly.sh DATE --global-only --publish
```

This rebuilds the static site, commits the fixtures and outputs, and pushes to GitHub Pages.

**Step 4 — Send email (only after user confirms):**

```bash
cd weekly-newsletter && python send_email.py --edition global --date DATE
```

If $ARGUMENTS is empty, use today's date for all steps.
