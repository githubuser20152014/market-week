# Global Investor Edition — Weekly Checklist

Run every **Saturday** for the prior week's Friday close date (YYYY-MM-DD).

---

## Step 1 — Generate content

```bash
# Fetch prices via Perplexity + build fixtures, then generate markdown
/global
```
- [ ] Review generated `output/global_newsletter_DATE.md` in full
- [ ] Approve content (or request edits)

---

## Step 2 — Publish to web

```bash
bash weekly-newsletter/publish_weekly.sh DATE --global-only --publish
```
- [ ] Verify live at `https://frameworkfoundry.info/global/DATE/`

---

## Step 3 — Build Substack HTML

```bash
cd weekly-newsletter && python data/build_global_substack.py --date DATE
```
- [ ] Open `output/global_substack_DATE.html` and paste into Substack HTML editor
- [ ] Set Substack title to the article subtitle (the punchy one, not "Framework Foundry Weekly")
- [ ] Publish on Substack
- [ ] Copy the Substack post URL (needed for social posts)

---

## Step 4 — Send subscriber email

```bash
# Test first
cd weekly-newsletter && python send_email.py --edition global --date DATE --to cmgogo.miscc@gmail.com

# Then send to all
python send_email.py --edition global --date DATE
```
- [ ] Check test email looks good before sending to all
- [ ] Confirm: Sent X subscribers, 0 failed

---

## Step 5 — Social posts

Ask Claude: *"Create X thread and LinkedIn post for the Global Investor Edition DATE."*
Claude will ask for the Substack URL — paste it in at that point (URL changes every issue).

- [ ] Review `output/global_x_thread_DATE.md` — post as thread on X
- [ ] Review `output/global_linkedin_DATE.md` — post on LinkedIn

---

## Step 6 — Commit

```bash
git add weekly-newsletter/send_email.py \
        weekly-newsletter/output/global_substack_DATE.html \
        weekly-newsletter/output/global_x_thread_DATE.md \
        weekly-newsletter/output/global_linkedin_DATE.md \
        weekly-newsletter/output/title_global_DATE.txt \
        weekly-newsletter/output/email_preview_DATE.html
git commit -m "Publish Global Investor Edition DATE"
git push
```
- [ ] Pushed to GitHub Pages

---

## Done ✓

All distribution channels complete:
- Web: `frameworkfoundry.info/global/DATE/`
- Substack: published
- Email: sent to all subscribers
- X: thread posted
- LinkedIn: post published
