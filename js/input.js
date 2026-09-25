// Input — pointer events so mouse, touch and pen share one code path.
//
// Decision (confirmed): support BOTH interaction styles.
//   - Tap-tap: tap a dot to select it, tap another dot to connect. Taps CHAIN: the dot just
//     connected stays selected, so a third tap draws 2nd→3rd, and so on — until that dot has no
//     room for another line (onConnect returns false) or the player taps the selected dot again
//     / empty space to stop.
//   - Drag: press on a dot, drag, release over another dot to connect (show a rubber-band
//     line while dragging).
// Distinguish tap from drag by movement distance after pointerdown. A drag that ends back on
// its start dot counts as a tap (fingers wobble past the threshold on phones).
//
// Modes (CLAUDE.md "Controls"):
//   - Draw (default): tapping a line does nothing.
//   - Eraser: tapping a line erases it. Lines win over the dots' extended tap area (short lines
//     are mostly covered by it); only a tap on a dot's visible circle counts as a dot tap. Pressing
//     a dot turns the eraser off and carries on as a normal draw press.
//
// Hit testing is geometric via the view: dotAtPoint(p, {strict}) and lineAtPoint(p).
// No game knowledge here — it only reports gestures through the handlers:
//   onConnect(a, b) → false to end a tap chain at b, onEraseLine(a, b), onSelect(id | null),
//   onRubberBand(fromId, point | null), onEraserChange(on)

import { splitKey } from "./game.js";

const DRAG_THRESHOLD_PX = 8;

export function attachInput(svg, { dotAtPoint, lineAtPoint }, handlers) {
  let selected = null; // dot id chosen by a first tap
  let press = null;    // { pointerId, startX, startY, dot, edge, dragging }
  let eraser = false;
  let attached = true;

  function select(id) {
    selected = id;
    handlers.onSelect(id);
  }

  function setEraser(on) {
    if (eraser === on) return;
    eraser = on;
    if (on) select(null);
    svg.classList.toggle("board--erasing", on);
    handlers.onEraserChange(on);
  }

  function toSvgPoint(e) {
    const ctm = svg.getScreenCTM();
    if (!ctm) return null;
    const p = new DOMPoint(e.clientX, e.clientY).matrixTransform(ctm.inverse());
    return { x: p.x, y: p.y };
  }

  function hitAt(e) {
    const p = toSvgPoint(e);
    if (!p) return { dot: null, edge: null };
    if (eraser) {
      const onDot = dotAtPoint(p, { strict: true });
      if (onDot) return { dot: onDot, edge: null };
      const edge = lineAtPoint(p);
      if (edge) return { dot: null, edge };
    }
    return { dot: dotAtPoint(p), edge: null };
  }

  function tapDot(id) {
    if (selected === null) select(id);
    else if (selected === id) select(null);
    else {
      const from = selected;
      select(null);
      const keepGoing = handlers.onConnect(from, id) !== false;
      if (keepGoing && attached) select(id); // chain on from the dot just reached
    }
  }

  function onDown(e) {
    if (!e.isPrimary || press) return;
    const { dot, edge } = hitAt(e);
    if (dot && eraser) setEraser(false);
    press = {
      pointerId: e.pointerId,
      startX: e.clientX,
      startY: e.clientY,
      selectedAtDown: selected, // a drag overwrites the selection; restore it if the drag was a wobbly tap
      dot,
      edge,
      dragging: false,
    };
    svg.setPointerCapture(e.pointerId);
    e.preventDefault();
  }

  function onMove(e) {
    if (!press || e.pointerId !== press.pointerId || !press.dot) return;
    if (!press.dragging) {
      const moved = Math.hypot(e.clientX - press.startX, e.clientY - press.startY);
      if (moved < DRAG_THRESHOLD_PX) return;
      press.dragging = true;
      select(press.dot);
    }
    handlers.onRubberBand(press.dot, toSvgPoint(e));
  }

  function onUp(e) {
    if (!press || e.pointerId !== press.pointerId) return;
    const p = press;
    press = null;

    if (p.dragging) {
      handlers.onRubberBand(null, null);
      const target = hitAt(e).dot; // eraser is off during a drag (pressing a dot turned it off)
      if (target === p.dot) {
        // Ended on its start dot: a finger that wobbled past the threshold — treat as a tap.
        selected = p.selectedAtDown;
        tapDot(p.dot);
        return;
      }
      select(null);
      if (target) handlers.onConnect(p.dot, target);
      return;
    }

    if (p.dot) {
      tapDot(p.dot);
    } else if (p.edge) {
      const moved = Math.hypot(e.clientX - p.startX, e.clientY - p.startY);
      if (moved >= DRAG_THRESHOLD_PX) return; // slid off: not a tap
      const [a, b] = splitKey(p.edge);
      handlers.onEraseLine(a, b);
    } else {
      select(null);
    }
  }

  function onCancel(e) {
    if (!press || e.pointerId !== press.pointerId) return;
    press = null;
    handlers.onRubberBand(null, null);
    select(null);
  }

  svg.addEventListener("pointerdown", onDown);
  svg.addEventListener("pointermove", onMove);
  svg.addEventListener("pointerup", onUp);
  svg.addEventListener("pointercancel", onCancel);

  function detach() {
    attached = false;
    svg.removeEventListener("pointerdown", onDown);
    svg.removeEventListener("pointermove", onMove);
    svg.removeEventListener("pointerup", onUp);
    svg.removeEventListener("pointercancel", onCancel);
    press = null;
    handlers.onRubberBand(null, null);
    select(null);
    setEraser(false);
  }

  // The board changed under a tap chain (undo, hint, start over): drop the selection.
  const clearSelection = () => select(null);

  return { detach, setEraser, isErasing: () => eraser, clearSelection };
}
