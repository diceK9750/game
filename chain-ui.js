/* Presentation only: all chain timing and awards come from Python. */
(function () {
  function motionReduced() {
    try {
      if (document.getElementById('modern-app')?.getAttribute('data-reduced') === 'true') return true;
      return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    } catch (_) { return false; }
  }
  window.createTimedChainView = function ({E, add, portraits}) {
    const root = E('div', 'timed-chains');
    const feverNotice = E('span', 'nr-sr-only');
    feverNotice.setAttribute('role', 'status');
    feverNotice.setAttribute('aria-live', 'polite');
    feverNotice.setAttribute('aria-atomic', 'true');
    let lastFever = '';
    const fx = E('div', 'chain-fx');
    fx.setAttribute('aria-hidden', 'true');
    const edge = E('div', 'chain-fx-edge'), wave = E('div', 'chain-fx-wave');
    const banner = E('div', 'chain-fx-banner');
    const hit = E('div', 'chain-fx-hit');
    const particles = E('div', 'chain-fx-particles');
    for (let j = 0; j < 16; j++) {
      const spark = E('i');
      spark.style.cssText = `--angle:${j * 22.5}deg`;
      particles.append(spark);
    }
    fx.append(edge, wave, particles, banner, hit);
    let entryUntil = 0, highUntil = 0, hitUntil = 0, effectFlip = 0;
    const rows = ['you', 'cpu'].map((owner, i) => {
      const row = E('div', 'timed-chain'), label = E('span'), bar = E('div', 'chain-meter'), fill = E('i');
      row.dataset.owner = owner; bar.setAttribute('role', 'progressbar');
      bar.setAttribute('aria-label', `${i ? 'CPU' : 'あなた'}の連鎖猶予`);
      bar.setAttribute('aria-valuemin', '0'); bar.setAttribute('aria-valuemax', '100');
      add(bar, fill); add(row, label, bar); root.append(row);
      const burst = E('div', 'chain-burst');
      // The dedicated live region below announces only the FEVER entry edge.
      burst.setAttribute('aria-hidden', 'true');
      burst.hidden = true; row.append(burst);
      return {row,label,bar,fill,burst,until:0,event:-1,flip:0};
    });
    root.append(feverNotice, fx);
    return {root, update(chains, battle, live=true, finished=false) {
      root.hidden = !live;
      const currentFever = live && !finished
        ? (chains?.you?.tier === 3 && chains.you.remaining > 0 ? 'you'
          : battle && chains?.cpu?.tier === 3 && chains.cpu.remaining > 0 ? 'cpu' : '')
        : '';
      root.dataset.feverOwner = currentFever;
      if (currentFever && currentFever !== lastFever) {
        feverNotice.textContent = `${currentFever === 'you' ? 'あなた' : 'ルナ'}、RUSH FEVER突入！`;
        entryUntil = Date.now() + 850;
        effectFlip = 1 - effectFlip;
        fx.dataset.pulse = String(effectFlip);
        window.chainVoice?.stinger?.();
      }
      else if (!currentFever && feverNotice.textContent) feverNotice.textContent = '';
      // A pause hides the view, but does not end the chain or re-announce on resume.
      if (live || finished) lastFever = currentFever;
      rows.forEach((r, i) => {
        const c = chains?.[i ? 'cpu' : 'you'] || {};
        const tier = c.tier || 0, count = c.count || 0;
        r.row.hidden = !!i && !battle;
        r.row.dataset.tier = String(tier);
        r.label.textContent = `${i ? 'CPU' : 'YOU'} ${count >= 2 ? `${count}連鎖${tier===3?' ★ RUSH FEVER':tier===2?' ✦ HIGH COMBO':''}` : count ? '次で2連鎖' : '正解で連鎖開始'}${count ? ` · ${c.waiting?'手番待ち':`${(c.remaining||0).toFixed(1)}秒`}` : ''}`;
        const percent = Math.max(0, Math.min(100, (c.remaining || 0) / (c.window || 4.5) * 100));
        r.fill.style.width = `${percent}%`; r.bar.setAttribute('aria-valuenow', String(Math.round(percent)));
        if (r.event !== c.event) {
          const fresh = r.event >= 0 && c.event > r.event;
          r.event=c.event; r.flip=1-r.flip;
          if (fresh && (live || finished) && count >= 1 && (!i || battle)) window.chainVoice?.play(i ? 'cpu' : 'you', count);
          if (fresh && live && tier >= 2 && count >= 4) {
            effectFlip = 1 - effectFlip;
            fx.dataset.pulse = String(effectFlip);
            hitUntil = Date.now() + (tier === 3 ? 160 : 130);
            hit.textContent = `${count} COMBO`;
            r.label.dataset.punch = String(r.flip);
            if (tier === 2) highUntil = Date.now() + 650;
          }
          if (fresh && live && count >= 2) {
            r.burst.textContent = `${i ? 'CPU' : 'YOU'}  ${count}連鎖！${tier===3?' ★ RUSH FEVER!':tier===2?' ✦ HIGH COMBO!':''}`;
            r.burst.dataset.pulse = String(r.flip);
            r.until = Date.now() + (motionReduced() ? 2800 : 1000);
          }
        }
        if (!live || count < 2) r.until = 0;
        r.burst.hidden = !live || Date.now() >= r.until;
        const portrait = portraits[i]?.image;
        if (portrait) {
          portrait.dataset.chainTier = String(live ? tier : 0);
          portrait.dataset.chainPulse = String(r.flip);
          if (live && tier >= 1 && count >= 2) {
            const pose = tier === 3 ? 'victory' : 'celebrate';
            portrait.style.backgroundPosition = tier === 3 ? '100% 0%' : '50% 0%';
            portrait.dataset.pose = pose;
          } else if (live && (chains?.[i ? 'you' : 'cpu']?.tier || 0) >= 2) {
            portrait.style.backgroundPosition = '50% 100%';
            portrait.dataset.pose = 'frustrated';
          }
        }
      });
      const now = Date.now();
      fx.dataset.owner = currentFever || '';
      fx.dataset.phase = !live ? 'none' : currentFever
        ? now < entryUntil ? 'entry' : 'active'
        : now < highUntil ? 'high' : 'none';
      fx.dataset.hit = String(live && now < hitUntil);
      banner.textContent = fx.dataset.phase === 'high' ? 'HIGH COMBO!' : 'RUSH FEVER!';
    }};
  };
})();
