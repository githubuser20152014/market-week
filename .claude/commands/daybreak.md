Run the Market Day Break generator with review checkpoints before publishing and before sending email.

Model assignment:
- Data collection (Step 0) → Haiku sub-agent (`/daybreak-fetch`)
- Content creation + user review (Steps 1–2) → Sonnet (this agent)
- Publishing + email preview (Steps 3–4) → Haiku sub-agent (`/daybreak-publish`)
- Email send (Step 5) → Haiku sub-agent (inline)

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

**Step 2 — Review checkpoint (content):**

Before displaying the draft to the user, run a pre-flight style check on the generated markdown. Check each of the following and report any violations:

- [ ] No em dashes (—) anywhere in the file
- [ ] `narrative` section is 2–3 sentences max, no boilerplate opener ("Markets showed...", "Stocks were...")
- [ ] `one_trade` thesis starts with the signal or anomaly, not the action ("Consider..." or "If conditions..." = flag it)
- [ ] No banned phrases: "amid concerns", "market participants", "investors remain cautious", "volatility persists", "risk sentiment"
- [ ] Bold callouts in plain_summary: at least 4 (if fewer, note it)

If any violations are found, list them clearly, fix what can be fixed by editing the `.md` directly, then display the corrected draft.

Then ask the user:
> "Here's the newsletter for [date]. Does everything look good, or would you like any changes before I generate the PDF and social posts?"

Wait for the user's response. If they request changes, make the edits to the `.md` file directly, then show the updated sections and ask again.

**Step 3 — Generate PDF + social posts + publish (only after user confirms content):**

Once the user approves the content, spawn a Haiku sub-agent to run the publish step and return an email preview report:
- Use the `daybreak-publish` skill with DATE as the argument
- Model: haiku

If STATUS is "error", display the PUBLISH_NOTES and do not proceed to Step 4.

**Step 4 — Review checkpoint (email):**

Using the report returned by the Haiku publish agent, display to the user:
- The email subject line (from SUBJECT)
- The email body summary (from EMAIL_SUMMARY)

Then ask the user:
> "The site is live. Here's a preview of the subscriber email — subject: '[SUBJECT]'. Ready to send to subscribers?"

Wait for the user's response. If they request changes, edit the `.md` file, then re-run Step 3 (spawn a new Haiku publish agent).

**Step 5 — Send email (only after user confirms):**

Once the user approves, spawn a Haiku sub-agent with this exact task:

> Run `bash weekly-newsletter/publish_daybreak.sh [DATE] --send-email` and report back: did it succeed or fail? If it failed, what error was shown?

Model: haiku

Report the result to the user.

If $ARGUMENTS is empty, use today's date for all steps.
