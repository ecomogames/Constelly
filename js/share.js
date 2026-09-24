// Share — Wordle-style spoiler-free summary (wording in js/strings.js).
//
// buildShareText is pure and only ever sees the puzzle number, time and hint count — never the
// title or category, so it can't spoil the picture.
//
// share(): the native share sheet on touch devices (phones/tablets), otherwise copy to the
// clipboard. Desktop browsers that support navigator.share (e.g. Chrome on Windows) get the
// clipboard too — a system share dialog on desktop is more surprising than useful.

import { formatTime } from "./format.js";
import { STRINGS } from "./strings.js";

export function buildShareText({ number, timeMs, hints }) {
  return STRINGS.share.text({ number, time: formatTime(timeMs), hints });
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
