# CLAUDE.md — Constelly

## What this is
**Constelly** (playconstelly.com) is a daily browser puzzle game (Wordle-model: one puzzle per day,
same for everyone, free to play, no login). The player sees a set of numbered dots and must connect them with lines to reveal a hidden
picture. Each number is the **degree** of that dot — the exact count of lines that must touch it in
the finished picture (not a sequence order). The subject of each picture varies: animals, plants
and everyday objects, all under a "constellation" visual theme (dots on a dark/starfield-style
background). Real astronomical constellations were dropped (2026-09-25): hard to read, not fun.
Each puzzle has a **clue** shown while solving — a witty line that hints at the picture without
naming it (hot-air balloon: "I can see my house from here...", starfish: "No, this is Patrick!").

Built solo, in about a week, by an experienced data scientist/software engineer who is new to
frontend/web deployment/monetization — so the whole project is optimized for **low complexity and
low running cost** over scalability or cleverness.

## Core mechanic (confirmed)
- Each dot shows a number = required number of connected lines (its degree in the target graph).
- Player draws lines between dots by selecting/dragging from one dot to another. Wrong lines *can*
  be drawn — there's no structural blocking and no immediate error flag on a single wrong line.
- **Per-dot feedback, evaluated once a dot's line count is reached:** when the number of lines
  touching a dot equals that dot's printed number, the dot is evaluated —
  - if all of that dot's lines are correct (match the solution) → the dot lights **bright yellow**
  - if any of that dot's lines are wrong → the dot lights **red**
  - a dot with fewer lines than its number still needs stays neutral (no color) until its count is
    reached
  - the player can still remove/redraw lines touching a red dot to fix it and re-trigger evaluation
- The player has no attempts limit and no fail state. A **Hint** button reveals one correct,
  currently-missing line at random.
- Scoring/results are based on **time to solve** + **number of hints used** — not on mistakes made.
- Puzzle is solved when every dot is yellow (drawn line set exactly matches the target edge set) —
  at that point the **entire constellation lights bright yellow** as the win state.
- **Hard cap (confirmed):** a line that would push a dot past its number is rejected (shake).
- **Countdown numbers (confirmed):** a dot displays how many lines it *still needs* — a "2" becomes
  "1" after one line touches it. When it reaches 0 the number disappears and only the yellow/red
  colour remains. Removing a line brings the number back.

## Controls (confirmed)
- **Draw (default mode):** tap-tap or drag between dots. Tapping a line does **nothing** in this mode.
  **Tap chains (2026-09-25):** after tap-tap connects A→B, B stays selected, so tapping C draws
  B→C, and so on. The chain ends when the reached dot is full (no lines left), on a tap on the
  selected dot or empty space, or when the puzzle is solved. Drags don't chain.
- **Eraser:** toggle button (eraser icon). While on, tapping a line erases it. It turns off when
  the button is pressed again **or** when the player taps a dot (so they can draw again right away).
  In eraser mode, line hit-testing must take priority over the dots' tap areas — otherwise short
  lines, whose length is mostly covered by the dots' tap areas, can't be erased.
- **Undo:** reverts the last *action* — a drawn line or an erased line. Repeated presses step
  back through history (action stack). Disabled when there's nothing to undo.
- **Start over:** asks for confirmation, then clears all lines. Timer keeps running, hint count is
  kept, and hinted lines stay on the board (so it can't be used to reset the score).
- **Hint:** as above. Hinted lines are **locked** (can't be erased or undone, survive start over)
  and drawn in a slightly paler gold than the win yellow.

## Content & puzzle authoring
- Puzzles are **hand-authored**, not procedurally generated. For each puzzle the author places:
  1. dot positions (x, y)
  2. each dot's degree number
  3. the target line set (the "answer") connecting them into the final picture
- A separate lightweight tool (build this *after* the core game works) takes the hand-authored
  layout and cleans up/proportions the final revealed artwork — it must **only** adjust visual
  proportions of the drawing, never add, remove, or move dots, and never change degree numbers.
  Treat this as a "beautify the line art" pass, not a puzzle generator.
- No image-recognition/auto-vertex-extraction pipeline is in scope for v1.
- **What makes a good puzzle (confirmed):** the degree numbers only matter where lines *branch*.
  A drawing that is one long loop of degree-2 dots (the first Apple, Snail, Pine) is dull: you just
  follow the outline. Good ones (Car, Crab, Teapot) have internal detail — windows, legs, spokes,
  veins — so a dot's number tells you something. `tools/puzzle_quality.py` checks this: longest run
  of consecutive degree-2 dots <= 5, and >= 25% of dots with degree >= 3. Run it with the validator.
- **Detached detail lines are good:** a puzzle may contain line groups that don't touch the main
  outline (drum sticks, donut sprinkles, a cherry on the cupcake, a snowman's buttons, an eye).
  They read well and give the degree numbers something to say. Robot and Rocket are the model.
- **Geometry rules when drawing** (all enforced by `tools/validate_puzzles.py`): a dot that lies on
  a straight run between two connected dots must be *on* that path, not floating next to it; keep
  ~15 grid units between dots and ~8 units between a dot and any line it isn't part of (for a
  drawing ~100 units wide).
- **Authoring workflow:** `tools/author_puzzles.py` is the source of truth — each puzzle is drawn
  as named points + paths on a free grid and auto-fitted onto the board; it regenerates
  `puzzles/puzzles.json`. Then run `tools/validate_puzzles.py`; `tools/preview_puzzles.py` renders a
  contact sheet (matplotlib). Publish order = `ORDER` list; never reorder already-played puzzles.
- **Visual editor (local only):** `python tools/editor.py` → http://127.0.0.1:8001/tools/editor.html.
  Draw/move dots and lines on the board, load any puzzle from the list, live checks (same rules
  as the validator + puzzle_quality, on the fitted drawing), trace over a reference image,
  player view, play-test via `?p=N`. Save rewrites that puzzle's `P(...)` block in
  author_puzzles.py via `ast` line ranges (new puzzles: block above `ORDER` + inserted into
  `ORDER` at a chosen future position), then runs author_puzzles/validate/quality. Saved coords
  are the fitted board ×100, so re-saving an unchanged puzzle gives identical JSON. Ids of
  existing puzzles are read-only; played puzzles show a warning and need a confirm for shape
  changes. Also edits the clue and the "redrawn" flag (the `REDRAWN` list). The server binds
  127.0.0.1 and rejects foreign Host/Origin headers; the page is
  public on Pages but inert there (no API). No delete — remove a puzzle by hand.
- **Target size (updated 2026-09-25):** **18–26 dots** — the owner found the 10–20-dot drawings
  too basic and often unrecognisable. The bar: a stranger names the solved picture in 3 seconds;
  draw it like a clean line-art icon, exaggerate the 2–4 defining features, add internal detail.
- **Clue (`clue=` in P()):** ≤ 80 chars (aim ≤ 40), witty, family-friendly, must not contain a
  word of the title or id (validator + editor enforce), no song lyrics. Shown in the HUD between
  the timer and the Hint button (max two lines); hidden when a puzzle has none.
- **Line colours (`colors=` in P()):** `colors={"green": ["a b c"], "red": ["d e"]}` (path
  syntax; unlisted lines are yellow). puzzles.json gets `"colors": {"a|b": "green"}` (keys as
  `edgeKey` in js/game.js). Palette: yellow, orange, red, pink, purple, blue, cyan, green, white,
  brown — hex in `--c-*` (css/style.css) and `PALETTE` (author_puzzles.py), names in the schema
  enum; the validator checks CSS and schema agree. Colours show **only in the win state** (each
  line glows in its own colour via the `#win-glow` SVG filter), never while solving — they'd
  give away which lines are right. Editor: palette swatches → click/drag over lines to paint.
  Coloured so far (2026-09-25): the first 10 in ORDER; the rest are still all-yellow.
- **Redraw status:** `REDRAWN` in author_puzzles.py lists puzzles drawn to the new standard
  (73 as of 2026-09-25); they come first in `ORDER`. The other 28 sit at the end of `ORDER` and
  still need a redraw: 17 have a weak new attempt with a clue (bat, bee, bird, deer, frog, grapes,
  horse, icecream, lemon, lizard, mailbox, monkey, panda, seagull, skateboard, sunflower, tiger),
  11 are old drawings without a clue (candle, car, castle, donut, hedgehog, key2, microphone,
  snowflake, strawberry, television, tent). The editor shows an "old" badge and a checkbox.

## Puzzle data format (starting point — adjust as needed)
```json
{
  "id": "2026-10-01",
  "title": "unrevealed until solved, or optional subtle theme hint",
  "category": "animal | plant | object",
  "clue": "optional: shown while solving, hints without naming it",
  "dots": [
    { "id": "a", "x": 0.32, "y": 0.14, "degree": 2 },
    { "id": "b", "x": 0.55, "y": 0.10, "degree": 1 }
  ],
  "edges": [["a", "b"], ["a", "c"]]
}
```
Coordinates are fractions of the board **width** (not pixels) so the drawing scales cleanly across
screen sizes. The board is portrait 3:4, so `x` is 0–1 and `y` is 0–4/3 (≈1.333); one unit is the
same length on both axes. One puzzle = one JSON object; all puzzles ship as a static array/file, not a database.

## Daily rotation — no backend needed
- Puzzle for "today" = `puzzles[dayIndex]` where `dayIndex` = number of days since a fixed launch
  date, computed client-side from the date. No server, no cron job, no database.
- Decide launch date early since it's the epoch for this calculation.
- **Confirmed:** the puzzle resets at 00:00 UTC, regardless of the player's local time zone.
  `dayIndex` should be computed from the player's device clock converted to UTC, not local
  midnight — a player in Denmark (UTC+1/+2) will see the new puzzle at 1am or 2am local time.

## Tech stack (recommended, matches "simple/low-cost/not a frontend person")
- Plain HTML + CSS + vanilla JS (or a minimal framework only if it clearly reduces effort) as a
  single-page app. Canvas or SVG for drawing the dots/lines — SVG is easier to reason about for
  hit-testing dot clicks and is simplest to style.
- **No backend, no database.** Puzzle data is a static JSON/JS file shipped with the site.
- **No user accounts.** All player state (today's progress, hint count, elapsed time, streak,
  history of past results) lives in `localStorage`.
- Hosting: a free static host (GitHub Pages, Cloudflare Pages, Netlify, or Vercel static export) —
  pick whichever the developer is already comfortable deploying to from Claude Code.
- Mobile: not a separate app — the same responsive web page, touch-friendly dot selection, working
  well on a phone browser from early on (per the "quickly accessible on mobile" requirement).

## Monetization (planned, not day-1 priority)
- Ads: Google AdSense, client-side only, no backend required.
- ~~Tip jar~~: decided against (2026-09-25).
- **Flag, don't skip:** serving ads to an EU-based audience from Denmark almost certainly requires
  a cookie-consent banner (GDPR/ePrivacy), even for a hobby project. Build this in before ads go
  live, not after.

## Build plan (target: playable in ~1 week)
1. ✅ Core playable loop as a single HTML page: render one hardcoded puzzle, let the player connect
   dots, detect the solved state. No daily rotation, no stats, no styling polish yet.
2. ✅ Puzzle data format finalized + day-index-based daily selection. 30 real puzzles authored
   (animals, plants, objects; 9–20 dots). Now **101 puzzles** (2026-09-23 → 2027-01-01): the 9
   real constellations were removed and 73 were redrawn (see "Redraw status" above). ORDER =
   redrawn puzzles first, then the rest; each part spreads the categories evenly with fewer dots
   first, and Starfish is day 1. The old test puzzles
   moved to `puzzles/samples.json` (not loaded by the game).
3. ✅ Controls + board for real-size puzzles: countdown numbers, eraser, undo, start over (see
   Controls); portrait board + nearest-dot hit testing (see open questions); review fix-ups
   (jsonschema compatibility, validator margin + dot-on-foreign-line checks).
4. ✅ Hint button (`useHint` in game.js; hint count in game state), timer (active time, see open
   questions), results dialog ~1s after the win glow (number, title, time, hints, countdown to
   00:00 UTC). Placeholder player-facing copy lives in `js/strings.js`. Tests: `node --test`.
5. ✅ `localStorage`-based history/streak; mobile responsiveness pass.
   - ✅ Mobile: the board fills the height left over (`.board-wrap` + container query units,
     capped at 600px) with no scrolling during play at 360×640 / 390×844 / desktop. Touch targets
     ≥ 44px, dialogs fit small screens (Esc, ×, tap outside). On solve the controls give way to
     the title + "See results". `prefers-reduced-motion`: no shake/pulse/fade (a red ring
     replaces the dot shake).
   - ✅ Storage (`js/storage.js`): mid-puzzle restore (lines, hinted lines, hints, timer; undo
     history starts empty), solved puzzles reopen in the win state, history + stats. Streak =
     consecutive puzzle days solved (hints don't break it; a missed day resets it to 0 on the next
     load). `?p=N` and pre-launch play use a `constelly:dev:` prefix and never write history/stats.
   - ✅ Stats dialog: solved, current/best streak, average/best time, **average hints** (one
     decimal max, `formatAverage`). `totalHints` was added to stats on 2026-09-25; older saved
     stats get it backfilled from history (on-day solves only) on the next load.
6. ✅ Share button (`js/share.js`): spoiler-free text (number, time, hints; never title or
   category). Native share sheet on touch devices, clipboard elsewhere (with an `execCommand`
   fallback for webviews); a cancelled share sheet is silent. Format (2026-09-25):
   `Constelly #3 ⭐⭐☆` / `⏱ 1:23 · 💡 1 hint` / `https://playconstelly.com/?n=3` — stars =
   `starRating(hints)` (0 → 3, 1–2 → 2, 3+ → 1), also shown in the results dialog; the link opens
   that exact puzzle (today's number → plain today, and the address is tidied to `/`). Also: how-to-play dialog (opens on
   the first visit) and stats dialog (solved, streaks, average/best time, "view today's result")
   behind header buttons. All their copy is placeholder text in `js/strings.js`.
7. Ads + cookie consent banner + analytics. **In progress (2026-09-25): AdSense review requested;
   consent message = Google's 3-choice (Consent / Do not consent / Manage options).**
   - ✅ **Cloudflare Web Analytics** (cookie-free, no consent needed; token 86d6de4d…): beacon
     snippet before `</body>` in index.html, privacy.html, 404.html. The site is NOT proxied
     through Cloudflare (DNS points at GitHub Pages), so the snippet is installed manually —
     "automatic injection" would never fire. Privacy page has an Analytics section.
   - Publisher **ca-pub-2867727940898674**. The AdSense script is in `<head>` of index.html and
     privacy.html (not 404.html: no ads on error pages); `ads.txt` at the root. Auto ads are
     configured in the AdSense dashboard (anchor/overlay on). Advice given: keep in-page auto ads
     off or excluded from the game area (ads next to the dots → accidental taps), no ads in dialogs.
   - `js/ads.js` pads the page by whatever an anchor ad covers (`--ad-top` / `--ad-bottom` on
     body), so it never sits on the controls; the board shrinks to fit.
   - Consent: Google's certified European regulations message (AdSense → Privacy & messaging),
     which also adds its own "Privacy and cookie settings" link; privacy.html has the required
     AdSense disclosures + an optional revocation link that appears once `googlefc` has loaded.
   - ✅ `about.html` (2026-09-25): About & FAQ — how to play, a worked Y-shaped example (inline
     SVG), scoring/streaks/sharing, past puzzles, FAQ, who makes it. Real text for the AdSense
     review and search engines. Linked from the menu, the How to play dialog, privacy.html and
     sitemap.xml; has the AdSense + Cloudflare snippets. Keep it true to the game when rules change.
   - ✅ `privacy.html` (contact: hello@playconstelly.com), linked from the how-to-play dialog.
   - **Consent approach (flagged):** since Jan 2024 Google requires a **Google-certified CMP**
     (IAB TCF v2.2) to serve AdSense ads in the EEA/UK/CH — a hand-rolled banner won't do. Plan:
     use AdSense's free built-in *Privacy & messaging* GDPR message instead of building one, and
     update privacy.html when ads go live.
8. ✅ Deployed: GitHub Pages (`ecomogames/Constelly`, `main`, root) at **playconstelly.com**
   (`CNAME`; HTTPS enforced; `www` and github.io redirect to it). Polish done before launch:
   - Icons + link preview: `img/favicon.svg`, `favicon-32.png`, `apple-touch-icon.png`,
     `icon-192/512.png` (`site.webmanifest`), `og-image.png` (1200×630, an original paper plane —
     never a real puzzle). All generated by `tools/make_icons.py`. OG/Twitter tags in index.html.
   - `404.html` (absolute paths — Pages serves it for any missing URL), `robots.txt`,
     `sitemap.xml`, `<noscript>` note.
   - A tab left open past 00:00 UTC reloads itself when it becomes visible again — unless the
     player is mid-puzzle (lines drawn, not solved). A failed puzzles.json fetch shows a message
     instead of an empty board.
   - **Everything in the repo is public** (Pages serves the whole root, incl. CLAUDE.md, tools/,
     tests/). So never commit solution previews: `Claude outputs/` is gitignored. puzzles.json
     itself is readable by anyone — accepted, it's the price of no backend.

9. ✅ Past puzzles + replay (2026-09-25).
   - Header left = **menu** (sidebar `<dialog class="drawer">`: Today's puzzle, Past puzzles,
     How to play, Statistics, Privacy); right = stats. The old stats "History" list is replaced
     by the **Past puzzles** dialog (`archiveRows` in storage.js): every day from today back to
     #1, title only once solved, "In progress" / "Not played yet", time/hints, "played later".
   - `?n=N` plays puzzle #N (only earlier days — `pickPuzzle` in daily.js; today/future/junk →
     today). Shown with a "Past puzzle #N · date · Back to today" bar. A past puzzle solved from
     the list goes into history with `late: true` and **never touches stats or the streak**. No
     midnight auto-reload on past puzzles.
   - **Play again** (solved state + results dialog) on any solved puzzle, today's included: clears
     that puzzle's saved progress and reloads. The first solve stays the official result — the
     results dialog and Share show it, with a "Replay: 0:20 · 0 hints" note for the replay;
     stats/history never change. A replay in progress shows a "Replaying #N" bar.
   - Stats' result button reads "View #N result" on a past puzzle ("View today's result" otherwise).
10. ✅ Review fixes (2026-09-25): a tap chain's selection is dropped by Undo, Hint and Start over;
   How to play fits a 360×640 screen (compact layout ≤ 760px tall) and its 220 KB animation only
   loads when the dialog first opens (`data-src` → `openHelp()` in main.js).
   **Known, not done:** 28 weak/old puzzles from day 74 (5 Dec); line colours only on the first 10
   (day 11 = 3 Oct is all-yellow); content runs out 2027-01-01; a deploy can briefly serve new HTML with
   cached old JS (Pages caches 10 min) — fix would be `?v=` on script/style URLs.

## Non-goals for v1
- No user accounts or server-side leaderboards.
- No procedural puzzle generation.
- No native mobile app.
- No business entity setup (see tax note in chat) unless/until revenue makes it necessary.

## Open questions (flagged, not resolved — decide before/while building)
- ~~**Overdraw cap:**~~ Resolved: **hard-cap** — a line that would push either endpoint past its
  printed number is rejected (brief shake feedback on the dot).
- ~~**Solution uniqueness:**~~ Resolved: every puzzle has exactly one intended answer and relies on
  the picture being visually obvious (classic dot-to-dot), not on the degree numbers being
  mathematically unique. No automated uniqueness check.
- ~~**Interaction model:**~~ Resolved: support **both** tap-tap and drag-to-connect via pointer
  events. Tapping a line erases it only in eraser mode (see Controls).
- ~~**Hosting:**~~ Resolved: **GitHub Pages** (deploy from `main`, root folder).
- ~~**Launch date / epoch:**~~ Resolved: **2026-09-23** (moved from 2026-10-01 on 2026-09-25, so
  that day was #3). `LAUNCH_DATE_UTC` in `js/daily.js`, `LAUNCH_DATE` in
  `tools/validate_puzzles.py`, `LAUNCH` in `tools/editor.py`. Puzzles #1+ are now live: don't
  reorder or reshape them (the editor warns).
- ~~**Pre-launch / out of puzzles:**~~ Resolved: before launch the site shows puzzle 0 (#1); past
  the end of the list it shows a "back tomorrow" message (no looping — progress is keyed by puzzle
  id). The validator prints the last puzzle's date and warns when < 14 days remain.
- ~~**Dot spacing:**~~ Resolved (with the board change below): dots must be ≥ **0.11** apart
  (≈ 38px centre-to-centre on a 360px phone), ≥ **0.05** from every board edge, and ≥ **0.05**
  from any solution line they aren't part of. All enforced by `tools/validate_puzzles.py`.
- `?p=N` picks any puzzle, but only on localhost.
- ~~**Board shape + hit testing:**~~ Resolved: **portrait 3:4** board (viewBox 1000×1333, `y` in
  0–4/3) and **nearest-dot** hit testing (within ~31px); in eraser mode the nearest line wins
  unless the tap is on a dot's visible circle. The 15-dot leaf fits at ~0.124 min spacing.
- ~~**Hinted lines:**~~ Resolved: **locked**, slightly different colour (see Controls).
- ~~**Hint edge case:**~~ Resolved: the hint first picks a random missing solution line whose two
  endpoints both still have room. Only if no such line exists does it pick a missing line anyway,
  remove a wrong line from each endpoint that is full, and draw the hinted line.
- ~~**Timer start:**~~ Resolved: starts when the **first line is drawn**.
- ~~**Timer while away:**~~ Resolved: **pauses** — only active time counts (paused while the tab
  is hidden, nothing counted while the page is closed). A hint before any line also starts it.
- ~~**Hints vs. undo:**~~ Resolved: a hint isn't undoable and doesn't clear the undo history; it
  drops only the history entries for the lines it touched (the hinted line + any wrong lines it
  removed), so the rest of the player's undo steps stay usable.
- ~~**Domain/branding/name:** not yet decided.~~ Resolved: **Constelly**, domain **playconstelly.com** (live on GitHub Pages, HTTPS + www redirect).
