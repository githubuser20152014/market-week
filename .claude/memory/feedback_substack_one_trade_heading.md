---
name: Substack One Trade heading — ticker must be Yahoo Finance hyperlink
description: In the Substack HTML h2 heading for The One Trade, the ticker must always be an anchor tag linking to Yahoo Finance, not plain text
type: feedback
---

In the Substack note HTML, the One Trade heading must use this format:

```html
<h2>The One Trade: Long <a href="https://finance.yahoo.com/quote/TICKER">$TICKER</a></h2>
```

**Why:** User flagged that `$TICKER` appearing as plain text in the heading is not acceptable. The ticker must be clickable and linked to its Yahoo Finance quote page.

**How to apply:** Whenever writing the Substack One Trade h2, always wrap the `$TICKER` in `<a href="https://finance.yahoo.com/quote/TICKER">$TICKER</a>`. Apply to all future Daybreak editions.
