Send a welcome email to a new subscriber.

**Usage:** `/welcome-subscriber new@example.com`

$ARGUMENTS should be the subscriber's email address.

---

**Step 1 — Dry run to confirm:**

Run:
```bash
python weekly-newsletter/send_welcome.py --email $ARGUMENTS --dry-run
```

Show the output to the user and ask:
> "Ready to send the welcome email to **$ARGUMENTS**?"

Wait for confirmation before proceeding.

**Step 2 — Send (only after user confirms):**

```bash
python weekly-newsletter/send_welcome.py --email $ARGUMENTS
```

Report whether it succeeded or failed.

---

If $ARGUMENTS is empty, ask the user: "What's the subscriber's email address?"
