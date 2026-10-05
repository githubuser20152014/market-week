---
name: Test email address
description: When user says "send me a test email", use cmgogo.miscc@gmail.com
type: feedback
---

When the user says "send me a test email", always send to **cmgogo.miscc@gmail.com** (double 'c' at the end of misc).

**Why:** User confirmed this is their test inbox. The single-'c' address (cmgogo.misc@gmail.com) is incorrect.

**How to apply:** Any `--to` override for test sends should use this address unless the user specifies otherwise.
