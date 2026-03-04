Run the Market Day Break generator and publish to GitHub Pages.

From the repo root, run:

```bash
bash weekly-newsletter/publish_daybreak.sh $ARGUMENTS
```

This will:
1. Fetch live market data and save a fixture
2. Generate the Markdown brief and PDF
3. Rebuild the static site
4. Commit and push to deploy to frameworkfoundry.info/daily/

If $ARGUMENTS is empty, the script defaults to today's date.
