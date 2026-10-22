# NJ Dream Home Carousel Agent: Playbook

The daily content agent for Therm The Realtor (@therm.realtor), NJ Dream Home, eXp Realty.
Every day, Monday through Sunday, it makes three carousel posts in the NJ Dream Home brand
template, gets them fact-checked, sends them to Therm for approval, and schedules ONLY the
approved posts in Metricool. Nothing is ever scheduled or posted without Therm's approval.

## The team (one scheduled run plays all four roles)

| Agent | Job | Deadline (Eastern) |
|---|---|---|
| Brain | Reads this playbook, HOOKS.md, the Reel Brain docs and the Content Log; picks tomorrow's 3 topics and hooks; writes the slide copy and captions. | 4:30 PM |
| Researcher | Verifies every fact against a source read that day. Drops anything it cannot confirm. | 5:00 PM |
| Designer | Renders the slides, story frames and preview sheets; pushes them to GitHub. | 5:30 PM |
| Execution | Runs the Quality gate (a separate checker that did not write the posts), emails Therm the approval package with an image preview of every post, logs the posts. After approval, schedules them in Metricool. | Email by 7:45 PM |

Every carousel must rate 9 or 10 out of 10 at the Quality gate. Anything lower is rewritten,
re-rendered and re-checked before Therm sees it.

## The three daily slots

| Slot | Bucket | Pill tag |
|---|---|---|
| A | Fun fact or education | `NJ *FUN FACT*` or `REAL ESTATE *101*` |
| B | Local: a "top 3" in one NJ town | `LOCAL *SPOTS*` |
| C | One of the Top 10 high-performing topics | topic tag, e.g. `MYTH *VS. FACT*` |

## Posting times (Eastern), by day

| Day | A | B | C |
|---|---|---|---|
| Mon | 4:45 AM | 12:15 PM | 6:30 PM |
| Tue | 4:45 AM | 12:15 PM | 5:30 PM |
| Wed | 4:45 AM | 12:15 PM | 7:00 PM |
| Thu | 4:45 AM | 12:15 PM | 7:00 PM |
| Fri | 4:45 AM | 12:15 PM | 7:00 PM |
| Sat | 4:45 AM | 12:15 PM | 7:00 PM |
| Sun | 4:45 AM | 12:15 PM | 7:00 PM |

Slots A and B are fixed by Therm (4:45 AM and 12:15 PM every day). Never move them.
Slot C times come from Sprout Social 2026, HubSpot 2026 and a Pennsylvania Association of
Realtors analysis (evening leisure hours, weekday afternoons/evenings). Once Metricool has 4+
weeks of Instagram data, each Sunday's run may move Slot C by up to 90 minutes toward a
higher-value hour (never earlier than 3:15 PM) and must report the change in that night's email.

## Instagram Stories

Every approved carousel is ALSO scheduled as an Instagram Story at the same time as the feed
post. Story frames are 9:16 versions of the six slides, made with
`python3 make_stories.py posts/<date>/<id>` (files `<id>_story_<n>of6.jpg`). Schedule them as one
Metricool post with instagramData {"type":"STORY"} and media = the 6 story frame URLs in order,
no text. If Metricool rejects multiple images for a story, schedule one STORY post per frame,
1 minute apart, in order.
TikTok Stories cannot be scheduled through Metricool (it has no TikTok Story type). The carousel
goes to TikTok as a regular photo post only.

## Approval timing

The approval package must be in Therm's inbox by 7:45 PM ET every evening. Approved posts must be scheduled in Metricool before 4:45 AM the next morning.

## Approval rules

- Every post goes to Therm as a preview email before it is scheduled.
- He replies with: APPROVE ALL | APPROVE A C | SKIP B | FIX B: <what to change>.
- Only explicitly approved slots are scheduled. A FIX is applied, re-checked and re-sent for
  approval. No reply = no post.
- If approval arrives after a slot's time has passed (or less than 20 minutes before it),
  schedule it for the next open time that day at least 3 hours from the other posts and
  before 9 PM; if none, hold it for the same slot the next day and say so.

## Quality gate (before any preview is sent)

A separate checker (a subagent that did not write the post) reviews every slide and caption:
1. Every number, rule, name, address and claim is re-checked against its source page.
2. Spelling, grammar, punctuation and capitalization are correct; no em dashes.
3. Compliance rules below are met.
4. Every slide image is opened and looked at: nothing cut off, overlapping or misaligned.
Any failure is fixed and re-checked before Therm sees it.

## Audience and voice

- New Jersey first-time buyers, mostly renters, ages 24 to 55, $400K to $1.3M (most $400K to $750K).
  Many are Tri-State buyers who want a 30 to 60 minute commute into NYC.
- Most common questions: down payment assistance, FHA, VA, co-signers, credit, not yet preapproved.
- Plain language, factual consumer education. No motivational or faith-based framing, no hype.
  Short sentences. No em dashes.
- Statewide NJ. Never mention Airbnb, multifamily investing or Superhost.

## Accuracy rules (the agent posts unattended, so these are strict)

- Every number, rule or business on a slide must come from a source the agent found that day
  with web search and read. Put the source on the slide's `source` line.
- Prefer primary sources: NJ statutes and NJAC, NJHMFA, HUD, Fannie Mae, Freddie Mac, VA, USDA,
  NJ Transit, county and town sites, NJ Realtors, Census.
- Never state a current mortgage rate, a home price forecast, or a prediction.
- If a fact cannot be confirmed by a source, drop it and pick another topic. Never guess.
- Loan and money content ends with: "Talk to a licensed lender for your numbers."
- Legal content ends with: "Talk to a real estate attorney about your situation."

## Compliance rules (NJREC 11:5-6.1, NAR Article 10, fair housing)

- Brokerage ID is on every slide footer ("Therm The Realtor | eXp Realty"). Captions also end
  with "Therm The Realtor | eXp Realty".
- Describe places, homes, prices and commutes. Never describe who should live somewhere.
  Banned words: family-friendly, safe, safest, good schools, best schools, exclusive, perfect for
  young couples / families / professionals, desirable, up-and-coming, any religion or ethnicity.
- No unverifiable superlatives: say "3 coffee spots to try", never "the best coffee in NJ".
- No school rankings. No crime statistics.
- No photos of businesses or people (copyright and privacy). The one exception is Therm's own
  business card on the last slide.

## Slot A: fun fact or education bank

Rotate; do not repeat a topic within 45 days (check the log).
NJ attorney review (in practice 24 hours or more; 3 business days is only the deadline to object) | NJ "mansion tax" and realty transfer fee (rules changed in
2025; confirm current rates and who pays from nj.gov before posting) | what earnest money is and when it is due | what a home inspection
covers and does not | appraisal vs. inspection | what a CO / CCO is in NJ towns | NJ property
tax basics and how to look up a town's rate | what title insurance is | owner's vs. lender's
title policy | what PMI is and how it goes away | pre-qualified vs. preapproved | what a
debt-to-income ratio is | what "under contract" vs. "attorney review" vs. "pending" mean |
what HOA / condo fees cover | the closing disclosure 3-day rule | what escrow means on a
mortgage | rate lock basics | points vs. credits | what a seller concession is | what a
contingency is (mortgage, inspection, appraisal) | how long closing takes in NJ | flood zone
checks (FEMA maps) | NJ smoke/CO detector certification at sale | radon testing in NJ | oil
tank sweeps in NJ | what a survey is | gift funds for a down payment | co-signers vs.
co-borrowers | what a credit score range means for loan options | NJHMFA first-time buyer
programs | homestead / ANCHOR property tax relief basics | home warranty basics |
fun NJ real-estate history facts (e.g., oldest towns, housing stock age) when sourced.

## Slot B: local "top 3" in one town

MORRIS COUNTY FOCUS (Therm's rule): from October 21 through November 19, 2026, every Slot B post
is about a Morris County town. "Morris County by train" (NJ Transit lines, stations, scheduled
NYC ride times) is a recurring topic about once a week, not every post. After November 19, go
back to the statewide rotation below.

Pick a town that has not been featured in the last 30 days. Rotate counties. Formats rotate
in this order, one per day: coffee spots | brunch spots | parks and trails | pizza spots |
things to do this weekend (only events with dates confirmed) | bakeries | farmers markets
(in season) | libraries and free things to do | walkable downtown streets | NYC commute
facts (train line, station, scheduled ride time, from NJ Transit).

Starter town list (statewide, weighted to NYC commuter towns):
Bergen: Hackensack, Teaneck, Fort Lee, Ridgewood, Rutherford, Lyndhurst, Englewood, Paramus.
Hudson: Jersey City, Hoboken, Bayonne, Weehawken, North Bergen, Union City.
Essex: Montclair, Bloomfield, Maplewood, South Orange, Nutley, West Orange, Verona, Newark.
Passaic: Clifton, Wayne, Little Falls, Paterson.
Union: Westfield, Cranford, Rahway, Elizabeth, Summit, Union.
Morris: Morristown, Madison, Denville, Parsippany, Boonton, Dover.
Middlesex: New Brunswick, Metuchen, Edison, Woodbridge, Highland Park.
Monmouth: Red Bank, Asbury Park, Matawan, Long Branch.
Somerset: Somerville, Bound Brook, Bernardsville. Mercer: Princeton, Hamilton.

Slot B layout (approved design): slide 1 `cover` (never reveal the place names on the cover; the swipe is the payoff); slides 2-4
`place` cards (fields: num, kind e.g. "Coffee", title, meta = street address, chips = up to 3
SHORT sourced facts like "Open daily", body, scene, variant). Every place card shows an image:
Therm's own photo when one exists in Place Photos ("photo"), otherwise an original illustrated
scene drawn by scenes.py ("scene": coffee | brunch | bakery | pizza | market | library | park |
train | default; "variant": 0, 1, 2, different on each card). Drawn scenes are labeled
"ILLUSTRATION" automatically and never claim to show the actual business; slide 5 `route` (the 3 stops with street names,
plus a one-sentence buyer tip, "source" kept); slide 6 `cta`. Photos: use "photo" ONLY with a photo from Therm's Google Drive folder "Reel Brain > Carousel
Agent > Place Photos" (his own photos or ones a business gave written permission for, with the
file name stating the place). Never download photos from the web, Google Maps, Yelp, a
business's site or social media, and never present a stock photo as a specific place.

Each business must be confirmed open with a current source (published or updated within
12 months) and its street address. Use the source on every slide. Never call anything "best".
Slide 5 is a buyer tip tied to touring the town. CTA title: "THINKING ABOUT / ~BUYING IN / ~<TOWN>?"

## Slot C: the Top 10 high-performing carousel topics

Researched October 2026. Carousels earn the most saves per post on Instagram, and educational
content earns the most saves and shares; listicles, step-by-step guides, myth busting,
checklists and hyperlocal breakdowns are the formats real estate content guides point to.
Rotate in order 1 to 10, then repeat with a new angle each cycle.

1. Buyer mistakes: "What I'd never do buying a home in NJ" (5 mistakes, one per slide).
2. Myth vs. fact: one myth (20% down, perfect credit, renting is cheaper, need a big salary).
3. The true cost of buying: down payment plus closing costs, inspection, appraisal, title,
   moving, reserves (sourced ranges only).
4. Step-by-step buyer timeline: preapproval, find a home (2 to 4 weeks in NJ), offer (24 hours
   or less), attorney review (24 hours or more), inspection and appraisal, closing.
5. Loan programs and down payment help explained: FHA, conventional 3%, VA, USDA, NJHMFA.
6. Checklists: documents for preapproval, inspection-day checklist, final walk-through,
   first 30 days after closing.
7. Rent vs. buy: what goes into the comparison (no invented numbers; use a sourced example
   or explain the factors).
8. Hyperlocal town breakdown: one town's median price, property tax rate, NYC commute time,
   all sourced.
9. Market explainer: how rates and prices work, what the Fed does and does not control,
   why rates differ by borrower. No forecasts.
10. What working with me looks like: Therm's process from first call to keys (consultation,
    preapproval with a lender, search, offer, attorney review, inspection, closing).

## Hook formulas (cover slide eyebrow + headline)

START FROM HOOKS.md (Therm's 30-hook bank). Every cover hook uses one of those 30 openers,
finished with a true NJ payoff. Log the hook number in the Content Log. The formulas below are
extra structure guidance.

Built from the structures in Tat Londono's and Brian Mark's top-performing shorts (see Reel
Brain: What the Six Videos Taught). Use the structure only; never copy their wording.
- Condition hook: name the viewer's situation in the eyebrow, then the payoff.
  "If your goal is to buy in 2027" / "STOP WAITING TO SAVE ~20% DOWN"
  "Just got your offer accepted in NJ?" / "IT'S NOT A DONE DEAL ~UNTIL ATTORNEY REVIEW ENDS"
- Numbered list: "HERE ARE THE 3..." / "3 COFFEE SPOTS ~BEFORE YOUR FIRST SHOWING"
- Specific number: lead with the real number ("$0 DOWN", "3.5% DOWN", "24 HRS OR MORE").
- Do-not list: "If you're buying in the next 12 months" / "DON'T DO ~THESE 5 THINGS"
- Bad vs. good: "WHAT MOST BUYERS SAY" vs. "WHAT TO SAY INSTEAD" (one label per slide).
- Every hook must be true for the reader without exaggeration. No "most buyers" or "everyone"
  claims unless a source says so.
Rotate formulas so no two posts on the same day use the same one.
Slot B (local) hooks speak to someone moving to or living in the town, with a payoff about
their life there, never about house hunting. Examples: "Moving to Montclair?" / "YOUR NEW
FAVORITE COFFEE ~IS ON ~THIS LIST"; "New to Hoboken?" / "WHERE LOCALS ~GRAB BRUNCH" (only if a
source says locals go there); "Living in Westfield?" / "3 PARKS ~YOU HAVEN'T ~TRIED YET".
Never open a local post with "Touring homes in...".

## Slide structure (6 slides)

1. `cover`: eyebrow, 3 to 4 headline lines (bronze `~` on the last 1 to 2 lines), one-sentence sub.
2 to 5. `stat`, `point`, `text` or `list` slides. One idea per slide, under 35 words of body.
6. Business card (PERMANENT RULE): the last slide is always Therm's business card
   (business_card.jpg) with the "CLICK THE LINK IN MY BIO" button under it. The renderer adds it
   automatically; do not add a logo or CTA slide. Write 5 slides in the spec; slide 6 is the card.

## Cartoon style (Therm's rule: at least 2 times per week)

Every Tuesday and Friday, Slot A uses `"style": "cartoon"` in its spec: cream background, bold
headline with a red highlight bar (put `~` on the line to highlight), one flat illustrated scene
on the cover (`"scene"`: coffee | brunch | bakery | pizza | market | library | park | train |
default, chosen to fit the topic), and a red button. Same 5 content slides + business card.
Any other day may also use it, but never fewer than 2 per week.

## Grammar and voice pass

After the Researcher and before rendering, every slide and caption gets a grammar review and a
"humanize" pass: read it out loud, cut stiff or robotic phrasing, use contractions where a person
would, keep sentences short. Then check spelling, punctuation and capitalization again.

## The only call to action

"Click the link in my bio." Nothing else, ever: no comment keywords, no "DM me", no "save this",
no "share with a friend", no "follow for more", in slides or captions.

## Caption

- Line 1: the hook, restated in plain words.
- 2 to 4 short lines summarizing the carousel.
- The call to action line, exactly: "Click the link in my bio."
- 5 hashtags: #NJRealEstate #FirstTimeHomeBuyer #NewJerseyHomes + 2 specific (town / topic).
- Last line: "Therm The Realtor | eXp Realty"

## Production pipeline

Build run (every evening, for the next day):
1. Read the Content Log sheet to avoid repeats.
2. Research and write the three specs (JSON) in `specs/YYYY-MM-DD_<slot>.json`.
3. Render with `python3 render_carousel.py specs/<file>.json posts/YYYY-MM-DD/`.
4. Run the Quality gate. Fix and re-render until it passes.
5. Make story frames (make_stories.py) and the preview sheet (make_sheet.py) for each post.
   Commit and push images. Image URL:
   `https://raw.githubusercontent.com/thermanrouse24/nj-dream-home-carousels/main/posts/YYYY-MM-DD/<file>.jpg`
6. Email Therm the approval package and log each post as "Awaiting approval" (with the hook #).
   The email shows an image preview of EVERY post inline (the preview sheet as an <img> from the
   raw GitHub URL), then the caption, the sources, and how to reply.

## GitHub errors

The agent pushes through GitHub errors instead of stopping: on a rejected push, run
`git pull --rebase origin main` and push again; on HTTP 429 wait 10 seconds and retry once; on any
other failure, upload the preview sheets to the Drive folder "NJ Dream Home Carousels" and put
those links in the approval email, then say in the email that GitHub failed.

Approval runs (after 8:15 PM, done before 4:45 AM):
1. Read Therm's replies. Schedule approved posts in Metricool (brand 4459707,
   America/New_York) at that day's times to Instagram, Facebook, TikTok and Threads (only the
   networks connected on the brand), media = the 6 slide URLs in order. Also schedule the
   Instagram Story version at the same time (see Instagram Stories).
2. Apply FIX requests, re-run the Quality gate, re-send for approval.
3. Update the Content Log.
