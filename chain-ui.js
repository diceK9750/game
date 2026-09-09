/* Presentation only: all chain timing and awards come from Python. */
(function () {
  window.createTimedChainView = function ({E, add, portraits}) {
    const root = E('div', 'timed-chains');
    const rows = ['you', 'cpu'].map((owner, i) => {
      const row = E('div', 'timed-chain'), label = E('span'), bar = E('div', 'chain-meter'), fill = E('i');
      row.dataset.owner = owner; bar.setAttribute('role', 'progressbar');
      bar.setAttribute('aria-label', `${i ? 'CPU' : 'あなた'}の連鎖猶予`);
      bar.setAttribute('aria-valuemin', '0'); bar.setAttribute('aria-valuemax', '100');
      add(bar, fill); add(row, label, bar); root.append(row);
      const burst = E('div', 'chain-burst');
      burst.setAttribute('role', 'status'); burst.setAttribute('aria-live', 'polite');
      burst.hidden = true; row.append(burst);
      return {row,label,bar,fill,burst,until:0,event:-1,flip:0};
    });
    return {root, update(chains, battle, live=true) {
      root.hidden = !live;
      rows.forEach((r, i) => {
        const c = chains?.[i ? 'cpu' : 'you'] || {};
        const tier = c.tier || 0, count = c.count || 0;
        r.row.hidden = !!i && !battle;
        r.row.dataset.tier = String(tier);
        r.label.textContent = `${i ? 'CPU' : 'YOU'} ${count >= 2 ? `${count}連鎖${tier===3?' ★ FEVER':tier===2?' ✦ SUPER':''}` : count ? '次で2連鎖' : '正解で連鎖開始'}${count ? ` · ${c.waiting?'手番待ち':`${(c.remaining||0).toFixed(1)}秒`}` : ''}`;
        const percent = Math.max(0, Math.min(100, (c.remaining || 0) / (c.window || 4.5) * 100));
        r.fill.style.width = `${percent}%`; r.bar.setAttribute('aria-valuenow', String(Math.round(percent)));
        if (r.event !== c.event) {
          const fresh = r.event >= 0 && c.event > r.event;
          r.event=c.event; r.flip=1-r.flip;
          if (fresh && live && count >= 2) {
            r.burst.textContent = `${i ? 'CPU' : 'YOU'}  ${count}連鎖！${tier===3?' ★ FEVER!!':tier===2?' ✦ SUPER!':''}`;
            r.burst.dataset.pulse = String(r.flip);
            r.until = Date.now() + 1000;
          }
        }
        if (!live || count < 2) r.until = 0;
        r.burst.hidden = !live || Date.now() >= r.until;
        const portrait = portraits[i]?.image;
        if (portrait) {
          portrait.dataset.chainTier = String(live ? tier : 0);
          portrait.dataset.chainPulse = String(r.flip);
          if (live && tier >= 2) portrait.style.backgroundPosition = tier === 3 ? '100% 0%' : '50% 0%';
        }
      });
    }};
  };
})();
