// Share — Wordle-style spoiler-free summary (wording in js/strings.js).
//
// buildShareText is pure and only ever sees the puzzle number, time and hint count — never the
// title or category, so it can't spoil the picture. It ends with a link to that exact puzzle
// (?n=N), so a friend who taps it later still gets the same one; on the day itself it's just
// today's puzzle for them. The star rating (starRating) is the at-a-glance part, like Wordle's
// coloured squares.
//
// share(): the native share sheet on touch devices (phones/tablets), otherwise copy to the
// clipboard. Desktop browsers that support navigator.share (e.g. Chrome on Windows) get the
// clipboard too — a system share dialog on desktop is more surprising than useful.

import { formatTime } from "./format.js";
import { STRINGS } from "./strings.js";

export const SITE_URL = "https://playconstelly.com/";

// Three stars for a solve without hints, two for one or two hints, one for three or more.
export function starRating(hints) {
  const n = Number.isInteger(hints) && hints > 0 ? hints : 0;
  return n === 0 ? 3 : n <= 2 ? 2 : 1;
}

export function buildShareText({ number, timeMs, hints }) {
  return STRINGS.share.text({
    number, time: formatTime(timeMs), hints, stars: starRating(hints), url: `${SITE_URL}?n=${number}`,
  });
}

// → "shared" | "cancelled" | "copied" | "failed"
export async function share(result) {
  const text = buildShareText(result);
  const touch = globalThis.matchMedia?.("(pointer: coarse)").matches;
  if (touch && navigator.share) {
    try {
      await navigator.share({ text });
      return "shared";
    } catch (e) {
      if (e?.name === "AbortError") return "cancelled"; // user closed the sheet: not an error
      // Anything else (e.g. NotAllowedError): fall back to the clipboard.
    }
  }
  try {
    await navigator.clipboard.writeText(text);
    return "copied";
  } catch {
    // In-app browsers / webviews often deny the Clipboard API; the old selection trick still works.
    return legacyCopy(text) ? "copied" : "failed";
  }
}

function legacyCopy(text) {
  const area = document.createElement("textarea");
  area.value = text;
  area.setAttribute("readonly", "");
  area.style.cssText = "position:fixed;top:0;left:0;opacity:0;";
  // Inside a modal dialog only its subtree is interactive, so attach it there.
  (document.querySelector("dialog[open]") ?? document.body).appendChild(area);
  area.select();
  let ok = false;
  try {
    ok = document.execCommand("copy");
  } catch {
    ok = false;
  }
  area.remove();
  return ok;
}
