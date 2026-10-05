---
name: Publish timing - ask before building or deploying to web
description: Never run build scripts or deploy to the web without explicit user instruction
type: feedback
---

Do not run build scripts (build_combined_site.py, build_site.py, etc.) or take any action that would publish content to frameworkfoundry.info without the user explicitly asking to publish.

**Why:** User does not want content going live on the web until they decide it's ready. Writing and committing a content file is fine; building and deploying it to the site is a separate, explicit step.

**How to apply:** After writing a new article or content file, stop there. Do not suggest or run any build/deploy steps unless the user says "publish", "build the site", "go live", or similar.
