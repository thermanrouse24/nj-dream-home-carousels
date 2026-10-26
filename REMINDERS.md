# INSTINCT AI: approval reminders (Therm's rule, Oct 26 2026: approvals he CANNOT miss)

Scheduled task "INSTINCT AI: Approval Reminders" runs at 8:47, 9:47, 10:47 and 11:47 PM and
6:47 AM Eastern. Each run:

1. Finds the posts still waiting on Therm (Content Log + Quote Bank rows "Awaiting approval" or
   "FIX sent - awaiting approval" for the posting day: tomorrow for the evening runs, today for 6:47 AM).
2. If Therm already replied to that day's approval email (APPROVE / SKIP / FIX / MANUAL / "approved",
   "post all"...), or nothing is waiting, it does nothing.
3. Otherwise it hits three channels at once, so one of them gets through:
   - a reply in the approval email thread (pushes it to the top of the inbox) with every waiting post's
     preview picture INLINE (tools/email_images.py, <img src="cid:attN">), the post times and the
     one-line reply format;
   - a phone push notification;
   - a Google Calendar event starting in 5 minutes, "APPROVE POSTS - reply to the email", with pop-up
     alerts at 0 and 1 minutes before (the calendar app rings on his phone).
4. Escalation: reminders 1 to 3 are normal; 11:47 PM is "LAST CALL tonight: reply in the next 3 hours
   or the 4:45 AM post is skipped"; 6:47 AM lists only the posts that can still go out today.

Rules: never more than one reminder per run, never after a reply, never a reminder for posts whose time
has already passed, and nothing is ever queued or posted by this task (it only reminds).
Approval emails and reminders must carry the pictures as inline attachments: Gmail's send tool strips
<img src="https://..."> links (that is why the Oct 26 approval email had no pictures).
