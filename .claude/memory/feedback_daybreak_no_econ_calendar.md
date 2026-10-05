---
name: Daybreak — No economic events calendar
description: Economic events calendar removed from Market Day Break; do not fetch or display it
type: feedback
---

Do not fetch, process, or render the economic events calendar in the Market Day Break (daily edition).

**Why:** Too slow to process, buggy API, and not relevant to daily readers.

**How to apply:** The fetch is now hardcoded to return `{"yesterday": [], "today": []}` in `fetch_daybreak_data.py`. The HTML sections and Claude prompt references have been removed from `daybreak_build_site.py` and `daybreak_process_data.py`. Do not re-add the calendar fetch or display for Daybreak. (The weekly and global editions are unaffected.)
