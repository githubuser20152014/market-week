# The Blueprint Launch Sequence
*Wednesday, 2026-03-19 — evening*

---

## Step 1 — Build and deploy the site

```bash
cd /c/Users/Akhil/Documents/cc4e-course/market-week/weekly-newsletter
python build_combined_site.py
```

Then commit and push:

```bash
git add site/investing-101/ \
        site/assets/asset-allocation-growth.png \
        site/index.html \
        data/generate_asset_allocation_chart.py \
        content/articles/investing-101-asset-allocation.md \
        build_combined_site.py

git commit -m "Launch The Blueprint — Issue #1: Asset Allocation"

git push origin master
```

Wait ~2 minutes for GitHub Pages to deploy.

**Verify:** open https://frameworkfoundry.info/investing-101/asset-allocation/ in a browser and confirm:
- [ ] Page loads
- [ ] Header reads "The Blueprint · Practical Investing Guides"
- [ ] Chart image appears
- [ ] Subscribe form is visible at the bottom
- [ ] Breadcrumb links back to home correctly

---

## Step 2 — Send subscriber email

Content: `messages/blueprint_launch.md` (Email / Subscriber version)

- [ ] Copy subject line: *Something new on Wednesdays — starting tonight*
- [ ] Paste body into email sender
- [ ] Confirm article link resolves: frameworkfoundry.info/investing-101/asset-allocation/
- [ ] Send to full subscriber list

---

## Step 3 — Post on social media

Content: `ContentRepo/wednesday-series/social-asset-allocation.md`

Post in this order — allow a few minutes between each:

- [ ] **X** — paste the 4-tweet thread (🧵 1/4 through 4/4)
- [ ] **LinkedIn** — paste the LinkedIn version
- [ ] **Substack** — paste the HTML version into the Substack editor (Notes or post)
- [ ] **WhatsApp** — paste the WhatsApp version into relevant groups

---

## Done

- [ ] Confirm all social posts are live
- [ ] Check site analytics / open rates the next morning
