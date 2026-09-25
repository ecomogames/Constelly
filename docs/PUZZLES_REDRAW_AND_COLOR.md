# Session guide: redraw weak puzzles + colour lines

Start a new session with: *"Read docs/PUZZLES_REDRAW_AND_COLOR.md in my Constelly folder and follow it."*
Read `CLAUDE.md` too, but only the "Content & puzzle authoring" part matters here.

## Goal
1. **Redraw the 28 weak puzzles** at the end of `ORDER` (#74 onwards, from 5 Dec 2026). Get the
   current list with `python tools/puzzle_kit.py order 70-110`: they're the rows marked `OLD`.
2. **Colour the lines** of every puzzle from **#11 (Fox)** onwards. #1–10 are done. Do them in
   play order, since the nearest dates matter most.

## Setup
- The user's folder is `C:\Projects\Constelly\Constelly` (`$HOME/mnt/Constelly` in device bash).
  Repo `ecomogames/Constelly` is public. **The user commits and pushes himself. Never commit
  or push.**
- Recommended: work in a cloud clone (`git clone https://github.com/ecomogames/Constelly`, then
  `pip install cairosvg --break-system-packages`). There you can `Read` the preview PNGs directly.
  Check first that the user's folder has no uncommitted changes (`git status` on the device) and
  is at the same commit, then work in the clone.
- At the end, copy back only `tools/author_puzzles.py`, `puzzles/puzzles.json` and `CLAUDE.md`.
  Use a fresh staging folder, then `device_commit_files`. On the device, run
  `python3 tools/validate_puzzles.py && node --test` to verify.
- **Never commit previews.** They show the answers. The kit writes them to `Claude outputs/`,
  which is gitignored. Keep draft files there too (`Claude outputs/drafts/`).

## The tool: `tools/puzzle_kit.py`
Run `python tools/puzzle_kit.py --help` for the full usage.

| command | what it does |
|---|---|
| `order [N-M]` | table: #, date, id, dots, redrawn (yes/OLD), number of coloured lines, clue, today |
| `check [ids / N-M]` | all validator + quality rules, dot count 18–26, clue rules |
| `preview ids / N-M [--big]` | PNG contact sheet. `--big` = large, with dot **names** + degrees and the player view next to it |
| `draft FILE [ids] [--big]` | check + preview a draft file (not yet in the game) |
| `apply FILE [--redrawn]` | write the draft into `author_puzzles.py`, regenerate `puzzles.json`, run the validator |

Draft file = plain Python with two helpers:
```python
P("bat", "Bat", "animal",
  "a 0 0; b 20 5; c 40 0; d 20 30",          # "name x y" on a free grid, y points DOWN
  ["a b c", "b d"],                          # paths: "a b c" = lines a-b and b-c
  clue="Hangs around all day",
  colors={"purple": ["a b c"], "white": ["b d"]})   # optional; unlisted lines stay yellow

COLOR("fox", orange=["etl eol ckl jl nl"], white=["nl nb nr"])   # colour-only, shape untouched
```
`COLOR` replaces all of a puzzle's colours (lines you don't list turn yellow). It's safe on
already-played puzzles, because colours don't change the solution. `apply` refuses to change the
**shape** of a played puzzle (number ≤ today's). Never reorder `ORDER`.

## Redraw brief (quality bar)
1. **A stranger names it in 3 seconds** from the solved line drawing. Draw it like a clean line-art
   icon with straight lines only. Pick the 2–4 defining features and exaggerate them. Use the most
   readable view (side view for most animals and vehicles, front view for faces and buildings).
2. Use **18–26 dots** for real detail, not for smoothing one outline. Fill the board: it's
   portrait 3:4, so tall-ish drawings use it best. Make symmetric subjects exactly symmetric. A
   small circle is 5–6 dots; a big one is 8–10.
3. **Interesting to solve.** The numbers only help where lines branch, so give it internal
   structure: panels, stripes, legs, veins, spokes, facial features. Detached groups (eyes,
   buttons, spots) are good.
4. Hard rules, all enforced by the kit:
   - dots ≥ 0.11 apart on the fitted board (about 13–14 units for a drawing 100 wide)
   - a dot ≥ 0.05 (about 6.5 units) from any line it isn't part of; a dot sitting on a straight
     run must be *in* that run
   - no run of more than 5 degree-2 dots
   - ≥ 25% of dots with 3+ lines
   Tiny details are usually what breaks the spacing rules, so make features big and bold.
5. **Clue:** a witty line that hints without naming. The kit checks that it contains no word of
   the title or id; also avoid obvious synonyms. Aim for ≤ 40 characters (max 80). Keep it
   family-friendly, with no song lyrics and no quotes longer than a few words. Vary the style.
   Examples: balloon "I can see my house from here...", starfish "No, this is Patrick!".
6. Keep the id and category. You may polish the title.
7. Iterate: `draft FILE --big`, then `Read` the PNG, then fix it. Two or three rounds per subject
   is normal. Be a harsh critic: if it reads as a generic blob, start over from a different idea.
   Compare against the good ones: `preview 1-10`.
8. `apply FILE --redrawn` adds the ids to `REDRAWN`. Leave their position in `ORDER` alone.

## Colouring guide
- Colours only appear in the **win state**, as a glow per line, so they're pure reward and never
  a hint. Dots never change colour.
- Palette: yellow (default), orange, red, pink, purple, blue, cyan, green, white, brown.
- Use the object's natural colours: green leaves and needles, brown wood and trunks, red or pink
  petals, blue water and glass, white for eyes, highlights, windows and seams, orange for fur and
  fruit. Use 2–4 colours per puzzle, and colour most lines. Plain yellow works well as a
  secondary colour (sun, gold, straw).
- Workflow: `preview 11-20 --big` shows the dot names. Write `COLOR(...)` lines, then
  `draft FILE`, look at the PNG, then `apply FILE`. About 10 puzzles per round.

## Working in parallel (optional)
For many redraws, give subagents about 8–10 subjects each, with this brief and the kit. Run at
most 3 at a time because of rate limits. Each agent writes only its own draft file. You review
every PNG yourself before `apply`. Redraws that are still weak stay `OLD` (don't pass
`--redrawn`); list them for the user.

## Finish
- `python tools/puzzle_kit.py check` and `python tools/validate_puzzles.py` must both pass, and
  `node --test` must pass.
- Update `CLAUDE.md`: the "Redraw status" paragraph (counts, remaining ids) and the "Coloured so
  far" line.
- Tell the user what changed, then commit and push. Send one final contact sheet in the chat only;
  it must never go into the repo.
