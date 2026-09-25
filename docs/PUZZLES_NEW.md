# Session guide: create new puzzles

Start a new session with: *"Read docs/PUZZLES_NEW.md in my Constelly folder and follow it. Make N
new puzzles."*

## Goal
Add new, original puzzles to the **end** of the daily list. The list currently runs out on
**2027-01-28** (#128). The validator prints the last date and warns when fewer than 14 days
remain. One puzzle = one day.

## Setup and tool
Same as `docs/PUZZLES_REDRAW_AND_COLOR.md`, which you should read for:
- the "Setup" (cloud clone, what to copy back, never commit or push, keep previews and drafts in
  the gitignored `Claude outputs/`)
- "The tool" (`tools/puzzle_kit.py`)
- the "Redraw brief" (the quality bar and hard rules are identical for new puzzles)
- the "Colouring guide": new puzzles get their colours right away, via `colors=` in `P()`

## Picking subjects
- Run `python tools/puzzle_kit.py order` (ids, titles) and `check` (prints every clue) to see what
  exists. **No repeats or near-repeats** (e.g. Key is id `key2`; bird, seagull and birdhouse all exist).
  Clues must not repeat existing ones either.
- Choose subjects everyone knows and that read well as straight-line icons: animals, plants and
  everyday objects. Categories must be `animal`, `plant` or `object`. Plants are the scarcest,
  so add some.
- Avoid anything branded, a known character, a logo or a specific artwork. Avoid anything that
  needs text to be recognised, and anything too thin or tiny (the spacing rules kill fine detail).
  Avoid real star constellations; the user removed them.
- Seasonal ideas fit the dates. Puzzle #N plays on 2026-09-23 + (N−1) days, and `order` shows the
  date. Examples: snowman or mittens in January, heart on 14 Feb.
- Propose the subject list to the user first (id, title, category, planned date) and let him cut
  or swap subjects before you draw.

## Ids and order
- The id is lowercase letters, digits and dashes, unique, and never changed once published
  (progress is keyed by id). The title is shown only after solving.
- `apply FILE` appends new ids to the end of `ORDER` in the order they appear in the file.
  Interleave categories (animal, object, plant, …) and don't put two similar subjects on
  neighbouring days. Put simpler drawings first within a batch.
- `apply FILE --at N` inserts at puzzle number N instead, for seasonal slots. N must be a future
  day, and everything after N shifts by one day. Only do that before those puzzles are live, and
  only if the user agrees.
- Always pass `--redrawn` for new puzzles: they meet the new standard, and `REDRAWN` means "good".

## Workflow
1. Draft about 8–10 per file in `Claude outputs/drafts/new-01.py` (subagents optional, max 3 in
   parallel).
2. Run `python tools/puzzle_kit.py draft FILE --big`, `Read` each PNG, and redraw until each one
   passes and is instantly recognisable. Then run `draft FILE` without `--big` to see colours at
   player size.
3. Run `python tools/puzzle_kit.py apply FILE --redrawn`. It prints the validator's new last date.
4. Check with `puzzle_kit.py order`, `puzzle_kit.py check`, `validate_puzzles.py` and
   `node --test`.
5. Update `CLAUDE.md`: the puzzle count and the end date in Build plan step 2 and in the "Known,
   not done" line.
6. Copy the three files back to the user's folder. Tell him how many puzzles were added and the
   new end date, then he can commit and push.
