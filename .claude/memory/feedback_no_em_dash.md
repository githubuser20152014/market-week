---
name: No em dashes in newsletters
description: Replace em dashes with spaced hyphen in all newsletter output — apply immediately after generation, before showing user
type: feedback
originSessionId: a85b9ce0-aa4c-46a0-bc74-49271a0e2702
---
Never use em dashes (—) in any newsletter output. Replace with a spaced hyphen ( - ) instead.

**Why:** User preference, repeatedly reinforced. Em dashes slip through Claude API generation and must be caught every time.

**How to apply:** After every generation step (MD file, Substack HTML, LinkedIn, X, email), scan for — and replace with " - " before presenting to the user. Applies to all editions (Daybreak, Global, US weekly, Fundaa) — prose, headers, table cells, footers, everything. When running a Python post-process, also collapse any resulting double spaces ("  -  " → " - ").
