---
name: project-daybreak-scheduler-conflict-2026-08-10
description: A known daily 5:15 AM automation runs the Daybreak pipeline + headless polish and can overwrite an in-progress human review if a /daybreak session is active at the same time
metadata: 
  node_type: memory
  type: project
  originSessionId: 3912cfe4-bf22-4d78-96f0-bbfa2d041752
  modified: 2026-08-10T11:20:26.706Z
---

On 2026-08-10, mid-review of the Daybreak draft for 2026-08-10 during a `/daybreak` session, the `.md` on disk changed out from under an in-progress edit (reintroduced em dashes, rewrote narrative and positioning-notes wording) — content diverged from what had just been written moments earlier.

**Root cause (confirmed by user):** there is a known automated script that runs every day at 5:15 AM, which invokes `bash weekly-newsletter/publish_daybreak.sh DATE --polish`. Per the script (`weekly-newsletter/publish_daybreak.sh`), `--polish` runs a headless `claude -p ... --allowedTools Read,Edit --dangerously-skip-permissions` sub-process against the `.md` (the `headless-daybreak-polish` prompt) and stops short of `--publish`. It does not touch `daybreak_scheduler.log` via any hook — it's a direct script invocation, not `CronList`/`schtasks`-visible from this session (checked and found nothing, which is expected since it runs outside this session's scope).

**Why:** This automation is legitimate infrastructure, but it directly collides with the repo's critical invariant (`CLAUDE.md`): "the approved `.md` is the single source of truth... nothing is regenerated from raw data after human approval." If a `/daybreak` review session happens to overlap with the 5:15 AM run (or the run happens to still be mid-flight when a session starts), the polish pass can silently overwrite hand-approved edits — same failure shape as [[project_global_publish_incident_2026-07-25]], just via a scheduled script instead of a code bug.

**How to apply:** Before trusting any Daybreak `.md`/social file mid-session (especially early morning, close to 5:15 AM), check its mtime against when you last wrote it — don't assume it's stable. If it changed unexpectedly, diff against your last edit, restore the approved content, and re-verify mtime stability before continuing (don't just silently re-fix once and assume it's safe — re-check before each subsequent step). The automation itself never runs `--publish`, so the acute risk is corrupted review content, not an unapproved auto-deploy — but flag any divergence to the user rather than silently proceeding.

**Resolved 2026-08-10:** the task is a Windows Scheduled Task named `FrameworkFoundry-DaybreakPolish` (root path `\`), action `bash.exe -c "cd .../market-week && bash weekly-newsletter/publish_daybreak.sh --polish >> .../daybreak_scheduler.log 2>&1"` (no DATE arg — defaults to today). User confirmed it's expected infrastructure and asked to turn it off; disabled via `Disable-ScheduledTask -TaskName "FrameworkFoundry-DaybreakPolish" -TaskPath "\"` (reversible — re-enable with `Enable-ScheduledTask` if wanted back). No longer an active risk for future `/daybreak` sessions unless re-enabled.
