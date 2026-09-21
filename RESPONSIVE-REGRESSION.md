# Smartphone / keyboard regression verification

## Current shared composition (2026-09-21, uncommitted)

The earlier verification below records the previous smartphone fix. The current
working tree supersedes its live-board geometry with one shared composition:

- Both renderers opt into `data-game-layout`, `data-arena`, `data-board-space`
  and `.game-hud`. `character-layout.css` owns this contract at every viewport,
  not only on phones. `mobile-layout.css` owns menus, dialogs and shell chrome;
  obsolete live-stage rules were removed from it.
- Portrait: rival above the board, player below it. Landscape: player to the
  left, rival to the right. Solo keeps the player in the same slot and leaves
  the absent rival's lane empty (no fictional CPU). Visible setup/result casts
  follow the same directional convention. Countdown/pause retain their existing
  character-free state UI; previously suppressed short-result cast remains so.
- The board receives the remaining rectangle independently of HUD content.
  HUD space is a bounded viewport-derived budget. Short landscape docks this
  same HUD beside the arena to preserve useful card sizes instead of shrinking
  the five number rows into the remaining strip below it.
- Each square side is `min((availableWidth - gaps) / columns,
  (availableHeight - gaps) / rows)`. Cards additionally use `aspect-ratio: 1 / 1`.
  Number search retains 8 columns x 5 rows, including its empty cells.
- Picture-grid columns follow the **board container's aspect ratio**, not a
  phone model: 24 visible cards use 4x6, 6x4 or 8x3; 12 use 3x4, 4x3 or 6x2.
  Stock replacement and game rules are unchanged. Arrow navigation and the CPU
  cursor read the same rendered column count, including immediately on rotation.
- Exceptional long HUD information remains accessible through HUD-local scrolling;
  it cannot expand the page or resize the board. It is not hidden or discarded.
  Chain effects remain inside their dedicated HUD meter lanes.
- No Python game-rule, audio, viewport host, or Pages workflow changes.

Base HEAD remains `75460a546e982d69790c496b4f8ae7f1c7592ff0`, detached.
Remote main was read again and matched it. The 14 previously uncommitted files
were backed up before this redesign (patch plus complete file copies) under:
`C:\Users\dicek\AppData\Local\Temp\number-rush-layout-base-20260921-181432`.
No commit, push, branch, merge, PR or publication was performed.

### Extended regression coverage

The browser runner now measures every card's aspect ratio, character/board
separation, and HUD/board intersections in addition to its original checks.
It runs the original 264 state cases plus 288 range/order/count variants (552).
An additional 48 comparisons verify that normal play, updated scores/CPU state,
and deliberately expanded HUD text have identical board rectangles.
The negative control squeezes the redesigned HUD to 13px and must detect overflow.
The original auto/flex reproduction no longer applies to the new DOM hierarchy.

Use the same local server/run button described below. Test fixtures do not run
the Python engine and do not replace actual game interaction or phone testing.

### Shared-layout validation results

- JavaScript: **190 passed** (two additional tests, including rendered-column
  navigation/CPU cursor and a rotation before the next engine snapshot).
- Python: **200 passed**; no Python changes. Syntax and diff whitespace checks passed.
- Browser: **552/552 passed**, **48/48 stable board comparisons**, squeezed-HUD
  negative control detected. All visible cards square within 0.6 CSS px rounding.
  No page overflow, tested HUD text collisions, offscreen buttons or buttons
  clipped by a scrolling ancestor. Main navigation/hint minimum **44px**.
- At 667x375: number HUD **320 client / 320 scroll**; number cards about **38.8px**.
  At 667x250, side docking preserves number cards **33px** and picture cards
  **40.25px** instead of a tiny board under the HUD. These cards are deliberately
  smaller than 44px; main controls retain their 44px minimum.
- Live Pyxel game in the in-app Chromium browser: numbers CPU scoring/chain,
  legal tap and player score update, pause/reverse-Tab/Tab/resume/countdown, and
  rotation 667x375 to 375x667. Player moved below the board, rival above it.
- Live picture solo 48: legal fox reading, stock 24 to 23, same-slot refill,
  dictionary registration and results. At 375x667, Down from card 1 went to
  card 7; after rotation to 852x393 it went to card 9, matching the new grid.
  Both setup directions and picture pause modal cycling were checked.
- The pre-existing browser diagnostic `MutationObserver.observe` non-Node
  exception appeared again without an identified source. Fixture error records
  were empty. Do not attribute that diagnostic to these changes without evidence.
- Actual iPhone Safari / LINE / Android Chrome, nonzero hardware safe insets,
  real toolbar transitions, touch precision and subjective audio remain untested.
  Finite animation transforms are settled for geometry measurements; every
  animation frame is not exhaustively tested.

## Revision and scope (2026-09-21)

- Repository: https://github.com/diceK9750/game
- Initial local branch/HEAD: `main`, `a36f70321fb88e6faf54e443d7ab877e1fc0a35c`, clean.
- Remote checked with `git ls-remote`, fetched, then checked out **detached**:
  `75460a546e982d69790c496b4f8ae7f1c7592ff0`.
- Audit revision `b8a30ea` has one subsequent commit, `75460a5` (#112), concerning compact portrait practice layout. It did not fix the landscape HUD or setup keyboard trap.
- No merge, commit, push, PR, Pages configuration or Python game-rule changes.

## Fixes

- `mobile-layout.css`: bounded landscape HUD/supplement tracks; separate rows for stats, CPU timer and wrapping feedback, bounded chain/hint column. Main toolbar and hint remain 44px at short heights. Results use horizontal action space and explicitly place shiritori secondary stats instead of an implicit extra row. Target padding accounts for font ink.
- `character-layout.css`: short-landscape shiritori HUD row grows with its contents rather than fixing it to 28px.
- `modern-ui.js`, `shiritori-ui.js`: normal setup pages no longer intercept Tab. Actual modal traps and entry/resume focus are retained.
- `index.html`, `player.html`: changed asset version keys to avoid stale cached CSS/JS. No deployment settings changed.
- Existing unit tests now assert the intended native setup navigation, not the previous inaccessible trap.

## Repeatable browser regression

From the repository root:

```powershell
.\.venv\Scripts\python.exe -B -m http.server 8029 --bind 127.0.0.1
```

Open `http://127.0.0.1:8029/tests/browser-layout.html` and click **Run all sizes / states**.

This uses the production renderers/styles in an iframe and deterministic bridge snapshots. It is a real DOM/layout test, not a game-engine simulation. No Pyxel CDN is required. The runner is not included in the Pages workflow.

12 sizes: 393×852, 375×667, 360×800, 852×393, 667×375, 1280×720, 667×360, 667×320, 667×300, 667×250, 666×375, 668×375.

At each size: numbers battle/practice (setup, countdown, play, updated, pause, result) and shiritori battle/solo (setup, play, updated, pause, result). Shiritori has no countdown. Total **264 cases**.

Checks include page dimensions, internal overflow in HUD/stats/prompt/setup/result, important text box intersections, button bounds, and actual main-toolbar/hint hit areas. Updated snapshots contain CPU claims, two-digit scores, long text, chain tiers and long elapsed time. Finite decorative scale animations are advanced to their final frame before settled-box checks; this is not an exhaustive animation-frame test.

The negative control deliberately reinstates the old auto/flex layout in the test iframe and must report `detects old HUD: true`. This ensures the known regression is actually detectable rather than merely checking for a CSS string.

Recorded result: **264/264 passed**, negative control **true**, fixture window error records **empty**.
At 667×375 the settled HUD is **292px client / 292px scroll** for battle and practice (before correction: approximately **13px / 143px** on current HEAD).
Main toolbar/hint minimum measured hit dimension is **44px**. Cards are exempt from this navigation-size assertion: at extreme 667×250 they remain smaller, a board-density tradeoff.

## Live game and keyboard checks

- Actual Pyxel game: numbers random 10 practice completed; ordered 40 battle CPU reached 11 points while HUD stayed 292/292; pause/Tab/Shift+Tab/Esc resume worked.
- Numbers practice actual host/iframe was resized through all 12 sizes. Document dimensions matched the inner viewport and HUD horizontal dimensions matched. This additionally tests host viewport resizing, separate from deterministic fixtures.
- Shiritori solo 48: two legal taps produced a 2-chain, stock 24→22, dictionary registrations, pause, resume and results.
- Shiritori battle 24: legal player answer, CPU turn/answer, 2/24 progress and timeout result were exercised.
- Numbers BGM/SFX toggles changed ON/OFF and were restored; retry confirmation, Esc cancellation and accepted retry/countdown worked.
- Native Tab/Shift+Tab in both setup pages reached game selection, BGM, help, mode/count/range/difficulty/start, effects, motion; shiritori also reached dictionary.
- Both pause dialogs kept forward/reverse focus inside their controls. Numbers help kept focus on Back and Esc returned to setup. Shiritori resume returned focus to a playable card.
- Browser diagnostic logs included a `MutationObserver.observe` non-Node message before these edits and during page reloads. Its source was not identified; do not describe the whole browser log as error-free. The fixture's own error listener reported no application errors, and no new game fallback was observed.

## Automated commands

```powershell
node --test tests/*.cjs
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p 'test_*.py'
Get-ChildItem -File *.js | ForEach-Object { node --check $_.FullName }
node --check tests/browser-layout.js
git diff --check
```

- JavaScript: **188 passed / 0 failed**.
- Python: **200 passed / 0 failed**.
- JavaScript syntax checks: passed.
- Working diff whitespace check: passed (Git may print normal LF/CRLF conversion notices).

## Limits / remaining device verification

Browser layout and live checks used the available Chromium-based in-app browser, not physical phones. Actual iPhone Safari, Android Chrome, LINE browser, nonzero safe-area insets, toolbar animation and pinch zoom remain unverified. All sound/difficulty/range combinations were not manually played; existing regression tests cover their logic. Sound toggles/routing are preserved; subjective listening quality is not evaluated by these layout tests.

On real devices, prioritize the 667×375-equivalent landscape, toolbars visible, rotation during play, 44px pause access, and safe-area clearance before publishing.
