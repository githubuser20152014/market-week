Fetch and verify market data for a single Global Investor Edition.

**Input:** DATE passed via $ARGUMENTS (format: YYYY-MM-DD). Required.

**Task:**

1. Run the fetcher:
   ```bash
   python weekly-newsletter/data/fetch_and_verify_global.py --date $ARGUMENTS
   ```

2. Read the terminal output carefully. Look for:
   - A summary table of global equity, FX, and commodity prices
   - Verification flags — lines marked WARN or MISMATCH between yfinance and secondary sources
   - Any "outside sanity bounds" messages

3. Return a structured report in this exact format:
   ```
   STATUS: ok|flagged|error
   DATE: YYYY-MM-DD
   FLAGGED_ASSETS: [comma-separated list, or "none"]
   SUMMARY:
   [paste the full terminal summary table here]
   NOTES:
   [any verification warnings, discrepancies, or sanity bound violations — or "none"]
   ```

**Do not ask the user anything. Do not confirm with the user. Just run the command and return the structured report.**

If the script errors out before saving fixtures (e.g., network failure), set STATUS: error and describe the error in NOTES.
