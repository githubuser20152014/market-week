Run the Market Day Break generator with review checkpoints before publishing and before sending email.

**Step 1 — Generate the Markdown only:**

```bash
bash weekly-newsletter/publish_daybreak.sh $ARGUMENTS
```

This fetches live data and produces **only the `.md` file** — no PDF, no social posts yet.

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
