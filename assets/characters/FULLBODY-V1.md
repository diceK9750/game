# RIN / LUNA full-body v1

Adopted after user smartphone acceptance of isolated duo v4, 2026-10-25.
RIN: 9 frames (6-frame joy sequence + hurt/frustrated/defeat), 2304x256.
LUNA: 6 expressions (idle/celebrate/victory/hurt/frustrated/defeat), 1536x256.
Both: transparent 256x256 cells; common feet anchor (128,248); bounded 600ms correct-answer animation.
Latest adopted portraits define identity/outfits; existing atlases and fairy are retained for fallback.
Generated together per character/expression batch with built-in imagegen and Sprite Pipeline normalization.
Full sources/prompts and manual-acceptance preview remain in isolated number-rush-duo-fullbody-v4.
The fairy stays an independent existing node/image. No engine rules or saved data changes.
Negative poses, pause and reduced motion cancel animation; failed/deferred loading never blocks play.
Modules load and fail independently. Original assets remain intact.
The shared task HUD uses its own inline-size container, a 15–22px font clamp and half-em gutters to avoid long CJK text overflowing without changing board sizing.
