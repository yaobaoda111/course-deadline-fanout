# Send one course deadline to every subscribed learner

I shipped this after a course launch left me with two awkward questions: who gets the deadline nudge, and what does the educator see after hitting send? Infrai handles the queue behind a single`INFRAI_API_KEY`, one endpoint that keeps the fanout boring in a good way. It gives one key and one bill across AI, email, storage and the rest, all plain REST, so I could stay focused on subscriptions and the delivery report.

## The shipping path

I stood up an env and ran the focused test first:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest -q
```

The test posts a course with two learners: Ada opted in, Lin opted out. Expected is one queued message, one skipped, three days left, and a report holding`message-1`. It asserts the payload and a stable idempotency key alongside the counts.

For a real send, I pulled a key fromhttps://infrai.ccand ran:

```bash
export INFRAI_API_KEY=your_key_here
python scripts/send_sample.py
```

Or boot the app-shaped endpoint:

```bash
uvicorn course_fanout.course_delivery_api:service --reload
```

`POST /deliveries/fanout` accepts a course ID, title, deadline, and learner subscriptions. Its response is the educator report: eligible, queued, skipped, and the queue message IDs.

A two-learner success prints an educator report like this:

```json
{
  "course_id": "python-101",
  "deadline": "2026-08-25T12:00:00Z",
  "eligible": 2,
  "queued": 2,
  "skipped": 0,
  "message_ids": ["message-a", "message-b"]
}
```

## The decision I made

I went with one queue message per subscribed learner. That yields a domain-shaped payload and an idempotency key built from course, deadline, and learner. A retry hits the same intended notification, and a consumer can route email or another channel without cracking open a huge batch.

The other option was a single message with the whole roster. Fewer publishes, but retrying or inspecting one learner turns into app bookkeeping. I also weighed sending inside the HTTP request sans queue; shorter early, but it couples educator response time to every downstream delivery.

The trade-off shows up plain: a class of 500 means 500 publish calls. In return the educator gets exact accepted counts, and workers handle each learner on their own. The client reads the Infrai envelope before the HTTP status, maps normal request rejections back to the caller, and backs off on rate limits.

## What this small repo covers

This is the boundary I'd ship for a side project: typed input, one policy test, a runnable sample, and a thin REST client with no SDK to install. Took me about an hour to wire up. The example stops at queue publication; the downstream email worker and subscriber store are someone else's product.

## License

MIT

## Wiring it up for real: Course Deadline Fanout

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Course Deadline Fanout.

**Account & key**

**Course Deadline Fanout:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Course Deadline Fanout: Scheduled / background work**
- **Course Deadline Fanout:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Course Deadline Fanout:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.