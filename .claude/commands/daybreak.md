Run the Market Day Break generator with review checkpoints before publishing and before sending email.

**Step 0 — Fetch & Verify Market Data:**

1. Determine DATE from $ARGUMENTS (or today if empty).
2. Check if `weekly-newsletter/fixtures/daybreak_DATE.json` already exists — if so, skip to Step 1.
3. Run the automated fetcher and verifier:
   ```bash
   python weekly-newsletter/data/fetch_and_verify_daybreak.py --date DATE
   ```
4. This script will display a summary table and any verification flags (discrepancies between yfinance and FRED/Stooq).
5. Review the summary in the terminal. If any prices look suspicious or are flagged, ask the user to confirm or provide a manual correction.
6. Once the data is confirmed in the terminal (by typing 'y'), the script saves the fixture to `weekly-newsletter/fixtures/daybreak_DATE.json`.

**Step 1 — Generate the Markdown only:**

```bash
bash weekly-newsletter/publish_daybreak.sh $ARGUMENTS
```

Because Step 0 already wrote the fixture, the script will detect it and run without `--live`.

After running, read the generated Markdown file and display its full contents to the user for review.

**Step 2 — Review checkpoint (content):**

Ask the user:
> "Here's the newsletter for [date]. Does everything look good, or would you like any changes before I generate the PDF and social posts?"

Wait for the user's response. If they request changes, make the edits to the `.md` file directly, then show the updated sections and ask again.

**Step 3 — Generate PDF + social posts + publish (only after user confirms content):**

Once the user approves the content, run:

```bash
bash weekly-newsletter/publish_daybreak.sh [DATE] --publish
```

This generates the PDF and social posts (LinkedIn, X, Substack) from the approved Markdown, rebuilds the static site, commits, pushes to GitHub Pages, and saves an email preview HTML to `output/email_preview_[DATE].html`.

**Step 4 — Review checkpoint (email):**

Read `weekly-newsletter/output/email_preview_[DATE].html` and display the email subject line and a summary of its contents. Then ask the user:

> "The site is live. Here's a preview of the subscriber email — subject: '[subject]'. Ready to send to subscribers?"

Wait for the user's response. If they request changes, edit the `.md` file, then re-run Step 3 to regenerate all outputs.

**Step 5 — Send email (only after user confirms):**

Once the user approves, run:

```bash
bash weekly-newsletter/publish_daybreak.sh [DATE] --send-email
```

If $ARGUMENTS is empty, use today's date for all steps.
