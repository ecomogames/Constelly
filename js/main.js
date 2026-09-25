// Entry point: wires the modules together on page load.
//
// Flow:
//   1. load puzzles (puzzles/puzzles.json)
//   2. pick today's puzzle (daily.js); ?p=N overrides it on localhost only
//   3. create game state (game.js), restore saved progress for that puzzle id (storage.js),
//      render it (render.js)
//   4. hook up input + controls (eraser, undo, start over, hint) and the timer
//   5. on win: glow + title, record the result, then the results dialog (with Share).
//      A puzzle that was already solved opens straight into the win state.
//   Header: how-to-play (auto-opens on the first visit) and stats dialogs.

import {
  createGame, addEdge, removeEdge, undo, canUndo, startOver, isSolved, edgeKey, splitKey,
  useHint, elapsedMs, pauseTimer, resumeTimer, snapshot, restoreProgress,
} from "./game.js";
import { getDayIndex, getTodaysPuzzle, msUntilNextPuzzle } from "./daily.js";
import { createStore, summarize, historyRows } from "./storage.js";
import { share } from "./share.js";
import { renderBoard } from "./render.js";
import { attachInput } from "./input.js";
import { formatTime, formatCountdown } from "./format.js";
import { STRINGS } from "./strings.js";

const LOCAL_HOSTS = ["localhost", "127.0.0.1", "[::1]"];
const RESULTS_DELAY_MS = 1000; // let the win glow play before the dialog covers it

const $ = (id) => document.getElementById(id);

// Dev-only: on localhost, ?p=N picks puzzles[N] so any puzzle can be tested. → N | null
function devOverride(count) {
  if (!LOCAL_HOSTS.includes(location.hostname)) return null;
  const raw = new URLSearchParams(location.search).get("p");
  if (raw === null) return null;
  const n = Number.parseInt(raw, 10);
  return Number.isInteger(n) && n >= 0 && n < count ? n : null;
}

// Static labels: data-text="results.time" → textContent, data-label → aria-label + title.
function applyStaticStrings() {
  const lookup = (path) => path.split(".").reduce((o, k) => o?.[k], STRINGS);
  for (const node of document.querySelectorAll("[data-text]")) {
    node.textContent = lookup(node.dataset.text);
  }
  for (const node of document.querySelectorAll("[data-label]")) {
    node.setAttribute("aria-label", lookup(node.dataset.label));
    node.title = lookup(node.dataset.label);
  }
}

// Dialogs close on a tap outside their box (Esc and the × already close them natively).
function lightDismiss(dialog) {
  dialog.addEventListener("click", (e) => {
    if (e.target !== dialog) return;
    const r = dialog.getBoundingClientRect();
    const inside = e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom;
    if (!inside) dialog.close();
  });
}

async function init() {
  applyStaticStrings();
  document.querySelectorAll("dialog.dialog").forEach(lightDismiss);

  let puzzles;
  try {
    const res = await fetch("puzzles/puzzles.json");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    puzzles = await res.json();
  } catch {
    // Offline, or a flaky connection mid-load: say so instead of showing an empty board.
    $("board").style.display = "none";
    $("controls").hidden = true;
    $("hint-btn").hidden = true;
    $("timer").hidden = true;
    $("reveal").textContent = STRINGS.loadFailed;
    $("reveal").hidden = false;
    return;
  }
  const override = devOverride(puzzles.length);
  const pick = override !== null
    ? { index: override, number: override + 1, puzzle: puzzles[override], preLaunch: false }
    : getTodaysPuzzle(puzzles);

  $("puzzle-num").textContent = `#${pick.number}`;
  document.title = `Constelly #${pick.number} — daily constellation puzzle`;

  const svg = $("board");
  const reveal = $("reveal");
  const controls = $("controls");
  const hintBtn = $("hint-btn");
  const eraserBtn = $("eraser-btn");
  const undoBtn = $("undo-btn");
  const resetBtn = $("reset-btn");
  const resultsBtn = $("results-btn");
  const timerEl = $("timer");
  const confirmReset = $("confirm-reset");
  const resultsDialog = $("results");
  const helpDialog = $("help");
  const statsDialog = $("stats");

  // Dev override and pre-launch play keep their progress apart and never touch history/stats.
  const store = createStore({ dev: override !== null || pick.preLaunch });
  const today = getDayIndex();
  store.loadStats(today); // resets a broken streak as soon as the game loads

  // ---- how to play: opens by itself on the very first visit ----
  for (const text of STRINGS.help.body) {
    const p = document.createElement("p");
    p.textContent = text;
    $("help-body").appendChild(p);
  }
  $("help-demo-img").alt = STRINGS.help.demoAlt;
  $("help-btn").addEventListener("click", () => helpDialog.showModal());
  if (!store.hasSeenHelp()) {
    helpDialog.showModal();
    store.markHelpSeen();
  }

  // ---- stats ----
  function renderHistory() {
    const rows = historyRows(store.loadHistory(), puzzles, today);
    const list = $("history-list");
    list.replaceChildren();
    for (const r of rows) {
      const li = document.createElement("li");
      li.className = `history-row history-row--${r.status}`;
      const num = document.createElement("span");
      num.className = "history-num";
      num.textContent = `#${r.number}`;
      const name = document.createElement("span");
      name.className = "history-title";
      name.textContent = r.status === "solved" ? r.title
        : r.status === "today" ? STRINGS.stats.historyToday : STRINGS.stats.historyMissed;
      const meta = document.createElement("span");
      meta.className = "history-meta";
      if (r.status === "solved") {
        meta.textContent = [r.timeMs === null ? null : formatTime(r.timeMs),
          r.hints === null ? null : STRINGS.stats.historyHints(r.hints)].filter(Boolean).join(" · ");
      }
      li.append(num, name, meta);
      list.appendChild(li);
    }
    $("history").hidden = rows.length === 0;
  }
  let isSolvedNow = () => false; // replaced once a puzzle is loaded
  const statTime = (ms) => (ms === null ? STRINGS.stats.none : formatTime(ms));
  $("stats-btn").addEventListener("click", () => {
    const s = summarize(store.loadStats(today));
    $("stat-solved").textContent = String(s.solved);
    $("stat-streak").textContent = String(s.streak);
    $("stat-max-streak").textContent = String(s.maxStreak);
    $("stat-avg").textContent = statTime(s.avgTimeMs);
    $("stat-best").textContent = statTime(s.bestTimeMs);
    $("stats-today").hidden = !isSolvedNow();
    renderHistory();
    for (const d of [helpDialog, resultsDialog]) if (d.open) d.close();
    statsDialog.showModal();
  });

  if (!pick.puzzle) {
    svg.style.display = "none";
    controls.hidden = true;
    hintBtn.hidden = true;
    timerEl.hidden = true;
    reveal.textContent = STRINGS.outOfPuzzles;
    reveal.hidden = false;
    return;
  }

  const puzzle = pick.puzzle;
  if (puzzle.clue) {
    $("clue").textContent = STRINGS.hud.clue(puzzle.clue);
    $("clue").hidden = false;
  }
  const game = restoreProgress(createGame(puzzle), store.loadProgress(puzzle.id));
  const view = renderBoard(svg, game);
  let solved = false;

  const save = () => store.saveProgress(puzzle.id, snapshot(game));
  function recordResult() {
    store.recordResult({ id: puzzle.id, day: pick.index, timeMs: elapsedMs(game), hints: game.hintsUsed });
  }

  // ---- results ----
  let countdownTimer = null;

  function currentResult() {
    return { number: pick.number, title: puzzle.title, timeMs: elapsedMs(game), hints: game.hintsUsed };
  }

  function updateCountdown() {
    // Past 00:00 UTC since the page loaded: today's puzzle has changed under us.
    $("results-next").textContent = getDayIndex() !== today
      ? STRINGS.results.nextPuzzleReady
      : `${STRINGS.results.nextPuzzle} ${formatCountdown(msUntilNextPuzzle())}`;
  }

  function openResults() {
    const r = currentResult();
    $("results-heading").textContent = STRINGS.results.heading(r.number);
    $("results-title").textContent = STRINGS.results.solvedTitle(r.title);
    $("results-time").textContent = formatTime(r.timeMs);
    $("results-hints").textContent = String(r.hints);
    $("share-status").textContent = "";
    updateCountdown();
    clearInterval(countdownTimer);
    countdownTimer = setInterval(updateCountdown, 1000);
    for (const d of [helpDialog, statsDialog]) if (d.open) d.close();
    if (!resultsDialog.open) resultsDialog.showModal();
  }
  resultsDialog.addEventListener("close", () => clearInterval(countdownTimer));
  resultsBtn.addEventListener("click", openResults);
  $("stats-today").addEventListener("click", openResults);
  isSolvedNow = () => solved;

  let statusTimer = null;
  $("share-btn").addEventListener("click", async () => {
    const outcome = await share(currentResult());
    const message = { copied: STRINGS.share.copied, failed: STRINGS.share.failed }[outcome] ?? "";
    $("share-status").textContent = message;
    clearTimeout(statusTimer);
    if (message) statusTimer = setTimeout(() => ($("share-status").textContent = ""), 2500);
  });

  // ---- timer display: derived from game.timer on each tick, never counted up ----
  function showTime() {
    timerEl.textContent = formatTime(elapsedMs(game));
  }
  const tick = setInterval(showTime, 250);

  function showSolved() {
    input.detach();
    clearInterval(tick);
    showTime();
    reveal.textContent = puzzle.title;
    reveal.hidden = false;
    resultsBtn.hidden = false;
    document.querySelector(".stage").classList.add("stage--solved");
  }

  function refresh() {
    view.update(game);
    solved = isSolved(game);
    undoBtn.disabled = solved || !canUndo(game);
    resetBtn.disabled = solved || game.drawn.size === game.hinted.size;
    eraserBtn.disabled = solved;
    hintBtn.disabled = solved;
    hintBtn.textContent = STRINGS.hud.hint(game.hintsUsed);
    showTime();
  }

  // After a player action or hint: refresh, and if that solved it, celebrate once.
  function afterChange() {
    const wasSolved = solved;
    refresh();
    save();
    if (solved && !wasSolved) {
      recordResult();
      showSolved();
      setTimeout(openResults, RESULTS_DELAY_MS);
    }
  }

  const input = attachInput(svg, view, {
    onSelect: (id) => view.setSelected(id),
    onRubberBand: (fromId, point) => view.setRubberBand(fromId, point),
    onEraserChange: (on) => eraserBtn.setAttribute("aria-pressed", String(on)),
    onConnect(a, b) {
      const result = addEdge(game, a, b);
      if (!result.ok && result.reason === "cap") result.capped.forEach((id) => view.shake(id));
      afterChange();
    },
    onEraseLine(a, b) {
      const result = removeEdge(game, a, b);
      if (!result.ok && result.reason === "locked") view.shakeLine(edgeKey(a, b));
      afterChange();
    },
  });

  eraserBtn.addEventListener("click", () => input.setEraser(!input.isErasing()));

  undoBtn.addEventListener("click", () => {
    const result = undo(game);
    // Only fails once hints exist (a hint may have filled a dot since the erase being undone).
    if (result && !result.ok) (result.capped ?? splitKey(result.key)).forEach((id) => view.shake(id));
    afterChange();
  });

  hintBtn.addEventListener("click", () => {
    const result = useHint(game);
    if (!result) return;
    afterChange();
    view.flashLine(result.key);
    // Dots that had a wrong line taken away to make room.
    new Set(result.removed.flatMap(splitKey)).forEach((id) => {
      if (splitKey(result.key).includes(id)) view.shake(id);
    });
  });

  resetBtn.addEventListener("click", () => confirmReset.showModal());
  // Act on the submit itself (synchronous, and Esc never submits) rather than on "close" +
  // returnValue, which keeps its old value when the dialog is dismissed with Esc.
  confirmReset.querySelector("form").addEventListener("submit", (e) => {
    if (e.submitter?.value !== "reset") return;
    input.setEraser(false);
    startOver(game);
    afterChange();
  });

  // Active time only: pause while the tab is hidden, and save then — on mobile, "hidden" is often
  // the last event a page gets before it's killed.
  function onVisibility() {
    if (document.hidden) {
      pauseTimer(game);
      save();
    } else {
      // A tab left open past 00:00 UTC: load the new puzzle — unless the player is part-way
      // through the old one (its progress is saved; solving it still counts for its own day).
      if (override === null && getDayIndex() !== today && (solved || game.drawn.size === 0)) {
        location.reload();
        return;
      }
      resumeTimer(game);
    }
    showTime();
  }
  document.addEventListener("visibilitychange", onVisibility);
  window.addEventListener("pagehide", save);
  onVisibility();

  refresh();
  if (solved) {
    // Revisiting a solved puzzle: straight to the win state; results reopen via the button.
    recordResult(); // no-op if already recorded (covers a solve whose result never got saved)
    showSolved();
  }
}

init();
