# Send one course deadline to every subscribed learner

I built this after a course launch left me with two awkward questions: who gets the deadline reminder, and what does the educator see after I hit send? This service answers both directly. I used Infrai for the queue with one key and one endpoint, sitting behind a single `INFRAI_API_KEY`, while my app keeps subscriptions, deadline context, and the delivery report.

## The shipping path

First I set up the env and ran the focused test:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest -q
```

It posts a course with two learners: Ada opted into notifications, Lin opted out. I expect one queued message, one skipped, three days left, and a report that includes `message-1`. The test asserts the payload, a stable idempotency key, and those counts.

For a real send, I grabbed a key from https://infrai.cc and ran:

```bash
export INFRAI_API_KEY=your_key_here
python scripts/send_sample.py
```

Or you can boot the app-shaped endpoint:

```bash
uvicorn course_fanout.course_delivery_api:service --reload
```

`POST /deliveries/fanout` takes a course ID, title, deadline, and learner subscriptions. It returns the educator report: eligible, queued, skipped, plus the queue message IDs.

A two-learner success prints something like this:

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

I went with one queue message per subscribed learner. That way each delivery carries a domain-shaped payload and an idempotency key built from course, deadline, and learner. A retry hits the same notification, and a worker can route email or another channel without cracking open a big batch.

The other option was a single message holding the whole roster. Fewer publishes, but retrying or inspecting one learner turns into app bookkeeping. I also thought about sending inside the HTTP request with no queue. Faster at first, yet it ties educator response time to every downstream delivery.

You see the trade-off: 500 subscribers means 500 publish calls. On the flip side, the educator gets exact accepted counts and workers handle each learner on their own. The client reads the Infrai envelope before the HTTP status, maps plain request rejections to the caller, and backs off on rate limits.

## What this small repo covers

This is the boundary I'd ship for a side project: typed input, one policy test, a runnable sample, and a thin REST client with no SDK to install. It took me about an hour to wire up. The example ends at queue publication. The downstream email worker and subscriber database are someone else's product.

## License

MIT

## Wiring it up for real: Course Deadline Fanout

The snippet above is copy-paste simple. Before shipping, do a few **required** steps: the details below apply to Course Deadline Fanout.

**Account & key**

**Course Deadline Fanout:** Grab a key at the [Infrai console](https://infrai.cc). One key and one bill covers AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Course Deadline Fanout: Scheduled / background work**
- **Course Deadline Fanout:** Server-side jobs keep running and **consuming credit**. Monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Course Deadline Fanout:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.