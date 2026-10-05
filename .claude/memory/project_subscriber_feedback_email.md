---
name: Subscriber feedback email — ready to send
description: Feedback email to all 12 subscribers is written, tested, and ready. Send Thursday evening.
type: project
---

Email is written, tested (formatting confirmed), and saved.

**File:** `weekly-newsletter/output/subscriber_feedback_email.md`

**Send command (Thursday evening):**
```bash
cd weekly-newsletter
python send_custom_email.py --subject "Quick question (honest answers welcome)" --message output/subscriber_feedback_email.md
```

**Why:** Switching from broadcast mode to conversation mode. Asks 3 questions: which editions they open, what's working, what's not. Includes a forwarding CTA at the bottom.

**How to apply:** When user returns, remind them the email is ready and just needs the send command run Thursday evening.
