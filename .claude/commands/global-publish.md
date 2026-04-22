Run the Global Investor Edition publish step and return a summary report.

**Input:** DATE passed via $ARGUMENTS (format: YYYY-MM-DD). Required.

**Task:**

1. Run the publish command:
   ```bash
   bash weekly-newsletter/publish_weekly.sh $ARGUMENTS --global-only --publish
   ```

2. Monitor the output for any errors (look for lines containing "ERROR", "FAILED", "Traceback", or non-zero exit codes).

3. Check which output files were generated:
   - Substack HTML: `weekly-newsletter/output/global_substack_$ARGUMENTS.html`
   - X thread: `weekly-newsletter/output/global_x_thread_$ARGUMENTS.md`
   - LinkedIn post: `weekly-newsletter/output/global_linkedin_$ARGUMENTS.md`

4. Return a structured report in this exact format:
   ```
   STATUS: ok|error
   DATE: YYYY-MM-DD
   SUBSTACK_FILE: [path or "not generated"]
   X_THREAD_FILE: [path or "not generated"]
   LINKEDIN_FILE: [path or "not generated"]
   PUBLISH_NOTES:
   [any warnings or errors from the publish command — or "none"]
   ```

**Do not ask the user anything. Do not confirm with the user. Just run the command and return the structured report.**

If the publish command fails, set STATUS: error and describe the error in PUBLISH_NOTES.
