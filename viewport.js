/* Pyxel clamps its internal scale to >= 1. Keep its viewport at 640x360,
   scaling the entire iframe. The browser maps input into iframe coordinates. */
function fitGame(width, height) {
  const scale = Math.max(0, Math.min(width / 640, height / 360));
  return { width: 640 * scale, height: 360 * scale };
}

if (typeof module !== "undefined") module.exports = { fitGame };

if (typeof window !== "undefined") {
  const stage = document.getElementById("stage");
  const frame = document.getElementById("game-frame");
  const box = document.getElementById("game-box");
  const root = document.documentElement;
  let scheduled = false;

  function update() {
    scheduled = false;
    const view = window.visualViewport;
    root.style.setProperty("--view-width", `${view ? view.width : window.innerWidth}px`);
    root.style.setProperty("--view-height", `${view ? view.height : window.innerHeight}px`);
    root.style.setProperty("--view-left", `${view ? view.offsetLeft : 0}px`);
    root.style.setProperty("--view-top", `${view ? view.offsetTop : 0}px`);
    const size = fitGame(stage.clientWidth, stage.clientHeight);
    box.style.width = `${size.width}px`;
    box.style.height = `${size.height}px`;
    frame.style.transform = `scale(${size.width / 640})`;
  }

  function schedule() {
    if (!scheduled) {
      scheduled = true;
      window.requestAnimationFrame(update);
    }
  }

  window.addEventListener("resize", schedule);
  window.addEventListener("orientationchange", schedule);
  window.addEventListener("pageshow", schedule);
  window.visualViewport?.addEventListener("resize", schedule);
  window.visualViewport?.addEventListener("scroll", schedule);
  new ResizeObserver(schedule).observe(stage);
  update();
}
