---
name: never-send-subscriber-emails-automatically
description: "User said \"do not send emails in future\" after the 2026-07-25 publish incident sent wrong content to subscribers"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e03b998a-3cab-497f-abac-389a5dd8f548
  modified: 2026-07-25T11:37:26.419Z
---

Never trigger `send_email.py` or any subscriber-facing send, for any
edition, without the user explicitly asking for that specific send in that
moment. If a correction or new email seems warranted, write it as a draft
file in `output/` and tell the user it's ready for their review — do not
send it yourself even if a previous step in the same pipeline would
normally auto-send.

**Why:** said directly after discovering `publish_weekly.sh` had
unconditionally emailed all 12 subscribers the wrong content during the
[[project_global_publish_incident_2026-07-25]] incident.

**How to apply:** treat any script or skill that sends email as a step
requiring separate, explicit user go-ahead every time, regardless of what
the script's flags or defaults do. This overrides any "publish implies
email" assumption baked into a shell script.
