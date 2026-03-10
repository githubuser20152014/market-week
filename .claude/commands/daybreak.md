Run the Market Day Break generator with a review checkpoint before publishing.

**Step 1 — Generate the newsletter:**

```bash
bash weekly-newsletter/publish_daybreak.sh $ARGUMENTS
```

This fetches live data and produces the `.md` and `.pdf` — but does NOT publish yet.

After running, read the generated Markdown file and display its full contents to the user for review.

Then read `weekly-newsletter/output/linkedin_[date].txt` and display it under a clear heading:

---
**LinkedIn post — ready to copy:**

[contents of linkedin_[date].txt]

Character count: [n] / 3,000
---

**Step 2 — Review checkpoint:**

Ask the user:
> "Here's the newsletter and LinkedIn post for [date]. Does everything look good, or would you like any changes before I publish?"

Wait for the user's response. If they request changes, make the edits to the relevant file(s) directly, then show the updated sections and ask again.

**Step 3 — Publish (only after user confirms):**

Once the user says they're ready, run:

```bash
bash weekly-newsletter/publish_daybreak.sh [DATE] --publish
```

This rebuilds the static site, commits, and pushes to GitHub Pages.

If $ARGUMENTS is empty, use today's date for both steps.
