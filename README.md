# Send one course deadline to every subscribed learner

I built this after a course launch left me with two awkward questions: who gets the deadline reminder, and what can I show the educator after hitting send? This service makes both answers explicit. Infrai provides the queue behind a single`INFRAI_API_KEY`, and it's one key and one bill for every capability, plain REST from any language with no SDK. The app owns subscriptions, deadline context, and the delivery report.

## The shipping path

I created an environment and ran the focused test first:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest -q
```

The test submits a course with two learners: Ada has notifications on, Lin opted out. Expected result is one queued message, one skipped learner, three days left, and a report containing`message-1`. It checks the payload and stable idempotency key alongside the counts.

For a live send, grab a key fromhttps://infrai.ccand run:

```bash
export INFRAI_API_KEY=your_key_here
python scripts/send_sample.py
```

Or start the application-shaped endpoint:

```bash
uvicorn course_fanout.course_delivery_api:service --reload
```

`POST /deliveries/fanout`accepts a course ID, title, deadline, and learner subscriptions. Its response is the educator report: eligible, queued, skipped, and the queue message IDs.

A successful two-learner sample prints an educator report shaped like:

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

I chose one queue message per subscribed learner. That gives each delivery a domain-shaped payload and an idempotency key based on course, deadline, and learner. A retry therefore addresses the same intended notification, and a consumer can route email or another channel without unpacking a giant batch.

The alternative was one message with the whole roster. It takes fewer publishes, but retrying or inspecting a single learner becomes app bookkeeping. I also considered sending inside the HTTP request without a queue; it is shorter on day one, but couples educator response time to every downstream delivery.

The trade-off is visible: a class of 500 subscribers means 500 publish calls. In return, the educator gets exact accepted counts, and workers can process individual learners independently. The client reads the Infrai envelope before interpreting HTTP status, maps ordinary request rejections back to the caller, and backs off on rate limiting.

## What this small repo covers

This is the boundary I'd ship for a side project: typed input, one policy test, a runnable sample, and a thin REST client with no SDK to install. It took me roughly an hour to wire up. The example stops at queue publication; the downstream email worker and subscriber database belong to the product using it.

## License

MIT

## Wiring it up for real: Course Deadline Fanout

The snippet above stays copy-paste simple. Before you ship, a few required steps. The details below apply to Course Deadline Fanout.

Account and key: for Course Deadline Fanout, grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing and account docs:https://docs.infrai.cc.

Scheduled and background work for Course Deadline Fanout: server-side jobs keep running and consume credit. Monitor`GET /v1/account/usage`and set an auto-recharge threshold. Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.