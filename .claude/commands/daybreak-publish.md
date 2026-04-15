Run the Market Day Break publish step and return an email preview summary.

**Input:** DATE passed via $ARGUMENTS (format: YYYY-MM-DD). Required.

**Task:**

1. Run the publish command:
   ```bash
   bash weekly-newsletter/publish_daybreak.sh $ARGUMENTS --publish
   ```

2. Monitor the output for any errors (look for lines containing "ERROR", "FAILED", "Traceback", or non-zero exit codes).

3. Read the generated email preview:
   - File: `weekly-newsletter/output/email_preview_$ARGUMENTS.html`
   - Extract the email subject line (look for `<title>` tag or a heading near the top)
   - Summarize the email body in 2-3 sentences (what's the lead story, what's the one trade)

4. Return a structured report in this exact format:
   ```
   STATUS: ok|error
   DATE: YYYY-MM-DD
   SUBJECT: [the email subject line]
   EMAIL_SUMMARY:
   [2-3 sentence summary of the email body — lead story + one trade + any notable callouts]
   PUBLISH_NOTES:
   [any warnings or errors from the publish command — or "none"]
   ```

**Do not ask the user anything. Do not confirm with the user. Just run the command and return the structured report.**

If the publish command fails before generating the email preview, set STATUS: error and describe the error in PUBLISH_NOTES.
