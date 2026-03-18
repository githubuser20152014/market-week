# Global Investor Edition — Launch Sequence
*Week of March 17–21, 2026*

---

## Friday, March 20 — Evening

- [ ] Send announcement email to subscribers (`send_custom_email.py`)
- [ ] Post WhatsApp version to group
- [ ] Post LinkedIn version

---

## Saturday, March 21 — Morning

- [ ] Generate live newsletter
  ```bash
  python generate_global_newsletter.py --date 2026-03-21 --live
  ```
- [ ] Review output in `output/global_newsletter_2026-03-21.md` — check narrative, spot-check 2–3 prices against a live source
- [ ] Build and publish site
  ```bash
  python build_combined_site.py
  ```
- [ ] Verify `site/global/2026-03-21/index.html` exists and renders correctly in browser
- [ ] Verify Global hero card appears on `site/index.html` landing page
- [ ] Commit and push
  ```bash
  git add -A
  git commit -m "Publish Global Investor Edition — 2026-03-21"
  git push
  ```
- [ ] Confirm live at frameworkfoundry.info

---

## Notes

- The announcement email is at `messages/global_edition_announcement.md`
- US and International archive pages remain live — do not delete
- If the Claude API call fails during generation, re-run — the fixtures will already be saved so only the LLM call repeats
- WTI Crude and CHF/USD had anomalous yfinance values in the test run — spot-check these specifically
