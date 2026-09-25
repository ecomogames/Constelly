// Room for AdSense's anchor ad.
//
// Auto ads can show an "anchor" ad: a bar fixed to the bottom (or top) of the screen. The game
// fills exactly one screen, so without room the bar would sit on top of the Eraser / Undo /
// Start over buttons (or the header) and invite accidental taps, which AdSense counts against
// the site. This watches for the anchor and pads the page by the part of the screen it covers
// (--ad-top / --ad-bottom, used by body in style.css); the board shrinks to fit. When the ad is
// collapsed or closed, the padding follows.

const ANCHOR = "ins.adsbygoogle[data-anchor-status], ins.adsbygoogle[data-anchor-shown]";

// → { top, bottom } px of the viewport covered by visible anchor ads
export function anchorCover(nodes, viewportHeight) {
  let top = 0, bottom = 0;
  for (const el of nodes) {
    const style = getComputedStyle(el);
    if (style.display === "none" || style.visibility === "hidden") continue;
    const r = el.getBoundingClientRect();
    if (r.height <= 0 || r.bottom <= 0 || r.top >= viewportHeight) continue;
    if (r.bottom >= viewportHeight - 2) bottom = Math.max(bottom, viewportHeight - Math.max(r.top, 0));
    else if (r.top <= 2) top = Math.max(top, Math.min(r.bottom, viewportHeight));
  }
  return { top: Math.round(top), bottom: Math.round(bottom) };
}

export function watchAnchorAds(root = document.documentElement) {
  let queued = false;
  const update = () => {
    queued = false;
    const { top, bottom } = anchorCover(document.querySelectorAll(ANCHOR), innerHeight);
    root.style.setProperty("--ad-top", `${top}px`);
    root.style.setProperty("--ad-bottom", `${bottom}px`);
  };
  const schedule = () => {
    if (!queued) { queued = true; requestAnimationFrame(update); }
  };
  new MutationObserver(schedule).observe(document.body, {
    childList: true, subtree: true, attributes: true,
    attributeFilter: ["data-anchor-status", "data-anchor-shown", "style", "class"],
  });
  addEventListener("resize", schedule);
  // the anchor slides in and out with a CSS transition: re-measure when it ends
  addEventListener("transitionend", schedule, true);
  schedule();
}
