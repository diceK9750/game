/* Until the DOM game announces readiness, retain Pyxel's 640x360 viewport and
   scale its entire iframe. The responsive UI then receives the actual space. */
function fitGame(width, height) {
  const scale = Math.max(0, Math.min(width / 640, height / 360));
  return { width: 640 * scale, height: 360 * scale };
}

function isTrustedGameMessage(event, source, origin, type) {
  return Boolean(source && origin && origin !== "null" && event &&
    event.source === source && event.origin === origin &&
    event.data && event.data.type === type);
}

function isModernReadyMessage(event, source, origin) {
  return isTrustedGameMessage(event, source, origin, "number-rush-modern-ready");
}

if (typeof module !== "undefined") module.exports = { fitGame, isModernReadyMessage };

if (typeof window !== "undefined") {
  const stage = document.getElementById("stage");
  const frame = document.getElementById("game-frame");
  const box = document.getElementById("game-box");
  const root = document.documentElement;
  const status = document.getElementById("loading-status");
  const help = document.getElementById("connection-help");
  const reload = document.getElementById("reload-button");
  const fullscreen = document.getElementById("fullscreen-button");
  let scheduled = false;
  let modernReady = false;
  let loadingTimer;

  function update() {
    scheduled = false;
    const view = window.visualViewport;
    root.style.setProperty("--view-width", `${view ? view.width : window.innerWidth}px`);
    root.style.setProperty("--view-height", `${view ? view.height : window.innerHeight}px`);
    root.style.setProperty("--view-left", `${view ? view.offsetLeft : 0}px`);
    root.style.setProperty("--view-top", `${view ? view.offsetTop : 0}px`);
    const size = modernReady
      ? { width: Math.max(0, stage.clientWidth), height: Math.max(0, stage.clientHeight) }
      : fitGame(stage.clientWidth, stage.clientHeight);
    box.style.width = `${size.width}px`;
    box.style.height = `${size.height}px`;
    if (modernReady) {
      frame.style.width = `${size.width}px`;
      frame.style.height = `${size.height}px`;
      frame.style.transform = "none";
    } else {
      frame.style.transform = `scale(${size.width / 640})`;
    }
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
  window.addEventListener("message", event => {
    if (isTrustedGameMessage(event, frame.contentWindow, window.location?.origin,
      "number-rush-modern-fallback")) {
      modernReady = false;
      root.setAttribute("data-app-ready", "false");
      frame.style.width = "640px";
      frame.style.height = "360px";
      if (loadingTimer !== undefined) window.clearTimeout?.(loadingTimer);
      if (help) help.hidden = true;
      if (status) status.textContent = "軽量表示に切り替えました";
      schedule();
      return;
    }
    if (modernReady || !isModernReadyMessage(event, frame.contentWindow, window.location?.origin)) return;
    modernReady = true;
    root.setAttribute("data-app-ready", "true");
    if (loadingTimer !== undefined) window.clearTimeout?.(loadingTimer);
    if (help) help.hidden = true;
    if (status) status.textContent = "準備ができました。";
    schedule();
  });
  window.visualViewport?.addEventListener("resize", schedule);
  window.visualViewport?.addEventListener("scroll", schedule);
  if (typeof ResizeObserver !== "undefined") new ResizeObserver(schedule).observe(stage);

  // This status lives above the iframe, so Pyxel's click-to-start remains usable.
  if (typeof window.setTimeout === "function") {
    loadingTimer = window.setTimeout(() => {
      if (modernReady) return;
      if (status) status.textContent = "起動を待っています。";
      if (help) help.hidden = false;
      schedule();
    }, 20000);
  }
  reload?.addEventListener("click", () => window.location.reload());
  if (fullscreen && document.fullscreenEnabled && typeof root.requestFullscreen === "function") {
    fullscreen.hidden = false;
    fullscreen.addEventListener("click", async () => {
      // Request only from a user gesture; unsupported browsers keep this hidden.
      try {
        await root.requestFullscreen();
      } catch {
        if (status) status.textContent = "全画面にできませんでした。このまま遊べます。";
      }
    });
  }
  update();
}
