# xeloba.ge Facebook — playbook for the scheduled run

This repository drives the automatic posting on the Facebook Page **„ხელობა • Xeloba“**
(Windsor.ai connector `facebook_organic`, account `210126072182800`).
The owner (ხელობა) asked for posts to go out **without asking for approval**.
Strategy doc: https://claude.ai/artifact/RPAV8j795Rsq8n967DWEr2

## Files

| Path | What it is |
| --- | --- |
| `calendar.json` | Posts by date (Tbilisi). **29.11–28.12.2026: one post every day** (ids 2–11 + 31–50); after that one every 3 days until 2027-02-21. Fields: id, date, pillar, topic, format (`photo` / `reel` / `text`), cta, cta_url, optional `notes` (key points to use — follow them) |
| `posted.json` | Log of what was already published. Never post an id that is in here. Entries with a non-numeric id are extra posts the owner asked for. |
| `tools/render.py` | Renders a photo card (1080×1350 JPG) or a Reel (1080×1920 MP4 + cover) from a JSON spec. Read its docstring. |
| `assets/chanchika.png` | ჭანჭიკა, the mascot (transparent PNG). Always use this image, never draw a new one. |
| `posts/` | Published media. Public URL: `https://raw.githubusercontent.com/myremontiDevs/xeloba-social./main/<path>` |

## Each run (daily, ~17:23 Asia/Tbilisi)

1. Work out today's date in **Asia/Tbilisi**. Find the `calendar.json` entry with that date.
   If there is none, or its id is already in `posted.json`, stop: nothing to do, no message.
2. Write the post in Georgian (rules below) and a render spec for `tools/render.py`.
   `text` posts get no image. For `photo`/`reel` posts, render, then **look at the image**
   (for a reel, extract 3–4 frames with ffmpeg) and fix any overflow, overlap or broken text before going on.
3. Save media as `posts/<date>-<id>.jpg` / `.mp4` (+ `-cover.jpg`), commit, push to `main`.
   Use the **commit-pinned** raw URL (`.../xeloba-social./<full commit sha>/posts/...`), not `main`:
   the `main` URL is cached ~5 minutes and can serve an older file. Check it answers HTTP 200.
4. Publish with Windsor `execute_action` (connector `facebook_organic`, account `210126072182800`):
   - `photo` → `create_photo_post` with `image_url` + `caption`, `scheduled_publish_time` = today 19:30 Tbilisi (= 15:30Z).
     If that is less than 11 minutes away, omit it (publish now).
   - `text` → `create_post` with `message` (+ `link` if cta_url), same scheduling rule.
   - `reel` → `create_reel` with `video_url` + `description` (Reels cannot be scheduled: publish now, ~17:30).
     If it fails, try `create_video_post`; if that fails too, post the cover with `create_photo_post`.
4b. **Instagram** (owner asked for daily posts on Instagram too, from 2026-11-29): publish the same media with Windsor
   `execute_action` (connector `instagram`, account `17841475649915168`):
   - `photo` → `create_image_post` with `image_url` (the commit-pinned JPG URL) + `caption`.
   - `reel` → `create_video_post` with `video_url` + `cover_url` (the `-cover.jpg`) + `caption`, `share_to_feed: true`.
   - `text` posts have no image: render a `photo` card for them first, so Instagram gets an image too.
   - Instagram caption = the Facebook text, but links are not clickable there: replace the link line with
     „👉 ბმული პროფილში“ and use up to 5 hashtags (e.g. `#ხელოსანი #რემონტი #xeloba #ხელოსნები #თბილისი`).
   - Instagram cannot schedule: publish right away. If it fails, retry once; if it fails again, note it in posted.json
     and go on — the Facebook post still counts.
5. Append `{id, date, facebook_post_id, instagram_media_id, media, format}` to `posted.json`, commit, push.
6. After id 30 is published, send the owner a short push message: the 30-post plan is finished.

If something fails that the fallbacks cannot fix, do not retry endlessly: send the owner one
short Georgian push message saying which post failed and why.

## Writing rules (Georgian)

- First line = a question or problem people recognise („ონკანი წვეთავს?“), not „xeloba.ge გთავაზობთ…“.
  The first 2 lines must work before „მეტის ნახვა“.
- Friendly, simple, „შენ“ form. ჭანჭიკა posts may joke.
- Body: tips 80–150 words, others 30–60. Short sentences.
- One CTA and one link per post. Add UTM to xeloba.ge links:
  `?utm_source=facebook&utm_medium=organic&utm_campaign=post-<id>`.
- Max 3 hashtags, e.g. `#ხელოსანი #რემონტი #xeloba`.
- **Never invent facts.** No fake reviews, client stories, prices, savings or site statistics.
  Allowed public facts: 700+ registered craftsmen, 26+ categories, posting a job and getting offers is free
  for clients, craftsmen send offers (with price and materials), renovation calculator at
  `xeloba.ge/remontis-kalkulatori`, blog at `blog.xeloba.ge`, VIP packages for craftsmen, WhatsApp channel for craftsmen.
- Practical tips must be safe and correct. For gas, electrics and anything risky, tell people to call a professional.
- Slogan when it fits: „ჭკვიანი ჭანჭიკა ირჩევს ხელობას“.

## Render spec cheat-sheet

```json
{"id": 5, "format": "photo", "kicker": "ზამთრის რჩევა",
 "title": "მილები რომ არ გაიყინოს: 4 ნაბიჯი",
 "items": ["…", "…", "…", "…"], "item_style": "number",
 "mascot": true, "bubble": "optional short line", "cta": "xeloba.ge"}
```
Items: max 5, each ≤ 40 characters. Reels: 3 items is ideal; `cta` is the end-card button text.
With 4 or more items, leave out `bubble` — the speech bubble then overlaps the last item.
Question/engagement cards: put the options as items with `item_style: "none"` and ask for answers in the caption.
