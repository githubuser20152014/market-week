---
name: feedback-push-manually
description: "User pushes source commits to GitHub themselves via `! git push`; do not try to push or loosen auto-mode for it"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 2e7a6b01-8829-44a0-ba1e-5c2afac40f78
  modified: 2026-10-05T09:54:39.416Z
---

Commit when asked, but leave `git push` of source/memory commits to the user (they type `! git push`). Do not retry a denied push or add an `autoMode.allow` rule to enable it.

**Why:** On 2026-10-05 the auto-mode classifier denied a push ("Out-of-Place Publication"); `Bash(git push:*)` was already allowed in settings.local.json. Offered an autoMode allow rule, user declined: "No, keep pushing manually".

**How to apply:** After committing, say the commit is local and hand over `! git push`. Does not affect the Daybreak `--publish` flow, where the Haiku publish agent pushes site content. See [[feedback_publish_timing]].
