---
name: carousel-formats
description: Build NJ Dream Home carousels in the three "carousel jobs" looks (story = connection, bold = warm-up how-to with circled screenshots of official pages, proof = buy) for Therm The Realtor. Use when the Brain picks a carousel's job or the Designer renders a spec with "style" story, bold or proof, or needs a screenshot of an official source page for a step slide.
---

# Carousel formats: story, bold, proof

Learned from the Brian Mark carousel Reel Therm sent on Oct 25 2026
(`videos/2026-10-25_brianmark_carousels.mp4`; notes in LESSONS.md). Structure only: never his
wording, his comment-keyword CTA, his claims or his images. Repo:
`thermanrouse24/nj-dream-home-carousels`. The rules are in PLAYBOOK.md ("Carousel jobs").

## 1. Brain: pick the job

| Job | Spec style | What it does | Weekly target |
|---|---|---|---|
| Connection | `"story"` | Therm's photo with a one-line subtitle on each slide. Verified Story Bank only (hooks 19 to 24) | at least 1 |
| Warm-up | `"bold"` | Huge headline cover, then numbered steps with a real screenshot of the official page, circled in red | at least 2 |
| Buy | `"proof"` | Story-bank client win only (Burlington County, DPA, $1,800 back at closing), no names, no client photo | at most 1, every 7 to 10 days |

- Don't use these styles on cartoon days (Tue/Fri, Slot A), notebook days (Mon/Thu, Slot C) or Slot B.
- Put the job in the Content Log Bucket, e.g. "Real estate 101 (bold)".

## 2. Write the spec

The full field list is in the `formats.py` docstring. Copy from `specs/examples/example_story.json`,
`example_bold.json` or `example_proof.json`. Their previews are in `specs/examples/*_preview.jpg`.

**story**: write 5 slides of `{"type": "cover"|"story", "text": "...", "photo": "therm_waterfront.jpg", "zoom": 1.0 to 1.4, "focus": [x, y]}`.
- Change the photo, zoom or focus on every slide so no two slides look the same.
- Keep each subtitle under about 14 words, in plain first-person voice.
- Use only Therm's own photos from `quote_photos/`.

**bold**:
- Cover: `{"type": "cover", "lines": ["WHITE", "~YELLOW LINE"], "badge": "NJ buyers", "photo": ...}`.
  "Swipe to learn how ->" is added automatically.
- Steps: `{"type": "step", "label": "Step 1:", "title": "...", "body": "...", "shot": "shots/<name>.png", "circle": [x, y, w, h]}`.
- `stat` slides render in the brand look and still get motion MP4s.

**proof**:
- `proof_card`: `kicker`, `lead`, `scene` (keys | savings | home | documents) and `punch`.
- `proof_big`: `lines` (put `~` on a line to make it yellow), `body`, optional `photo`.
- The disclaimer "Results vary. Every buyer's situation is different." is added automatically.
- End with "Talk to a licensed lender for your numbers."

The business card is still added as the last slide automatically.

## 3. Screenshots for bold steps (the robot)

The sandbox can't open most sites, so GitHub Actions takes the screenshot:

1. Write `shots/requests/<date>_<slot>_<n>.json`:
   `{"url": "<official page>", "find": "<exact text to circle>", "status": "new"}`.
   Optional fields: `scroll_to`, `selector`, `width` (default 1200) and `height` (default 900).
2. Commit and push. The "Screenshot official pages" workflow runs.
3. `git pull` every minute, for up to 10 minutes, until the request says `"status": "done"`.
4. Use `"shot": "shots/<name>.png"` in the slide and paste the request's `circle` into it.
   - If the circle is too big (a whole paragraph), shrink it by hand to the exact number or line.
   - If the request says `"failed"`, drop the shot and keep the step as text.

What can be screenshotted:
- Only primary sources: nj.gov, fema.gov, epa.gov, njtransit.com, consumerfinance.gov, and county and town sites.
- Never a person's profile, a listing photo, a business's photos, social media, or anything behind a login.

## 4. Render and check (Designer)

```
python3 render_carousel.py specs/<file>.json posts/YYYY-MM-DD/
python3 make_stories.py posts/YYYY-MM-DD/<id>
python3 make_sheet.py posts/YYYY-MM-DD/<id>
python3 make_card_tiktok.py posts/YYYY-MM-DD/<id>
python3 make_reel.py posts/YYYY-MM-DD/<id>
python3 animate_stat.py specs/<file>.json <n> posts/YYYY-MM-DD/<id>_<n>of6.mp4   # every stat slide
```

Open every slide and check:
- **story**: Therm's face is visible and not covered by text, and the subtitle is readable.
- **bold**: the headline fits on the cover. The red circle sits on the exact line the slide talks
  about, and the screenshot is readable at phone size.
- **proof**: the white card isn't cut off, the scene is labeled ILLUSTRATION, and the disclaimer is there.
- **All**: slide 6 is the business card. Tag pill, logo and "Therm The Realtor | eXp Realty" are on
  every slide. No em dashes, and the only CTA is "Click the link in my bio." (TikTok: DM me "HOME").

## 5. Never

- Never invent a client, result, quote or story.
- Never use anyone's photo but Therm's.
- Never screenshot a non-official page.
- Never use comment-keyword CTAs.
- Never claim "the algorithm favours carousels" as a fact.
