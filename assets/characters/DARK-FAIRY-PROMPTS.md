# 背景修正と闇の妖精

imagegenスキル / 組み込み image_gen を使用。外部CLI/APIは使用していません。
生成PNGをそのままコピーし、RGBAの背景透明ピクセルを確認。旧画像は保持。
採用: koh-dark-cutout-atlas.png（1536×1024、3×2表情）、dark-fairy.png。
最初の背景抽出は市松模様を描いたRGB画像だったため不採用。

## ライバル：採用した最終編集プロンプト

Remove the background from the attached sprite atlas, preserving all six characters and the exact 1536x1024 3x2 layout. Deliver TRUE alpha transparency PNG, with fully transparent pixels outside the characters. Do NOT draw a checkerboard or white background. Background extraction only, preserve all expressions, character scales, clothes and poses. Clean fur edges, no halo. Transparent background is essential.

入力: koh-dark-atlas.png。

## 闇の妖精：最終生成プロンプト

Original game companion sprite, a tiny mischievous dark fairy who whispers temptation to a fallen red panda heroine. ONE full-body two-head-tall fairy hovering, facing left, sly friendly villain smile, pale lavender face, large violet eyes, pointed ears, short midnight purple hair, fully clothed high-neck black plum petal tunic with sleeves, tights and pointed boots, two large translucent purple moth wings, tiny violet gemstone. Polished hand-painted 2.5D cute family-friendly fantasy mascot, soft detailed materials, warm amber rim light from forest lanterns. Centered complete silhouette with broad empty margins, wings fully visible. Square 1024x1024, character including wings within central 70 percent. Background perfectly uniform midnight navy #070b20, no checkerboard, no scenery, no border, no text, no watermark, no other figures. Readable as a small companion icon, not an existing franchise character.

実際の出力は1254×1254のRGBA PNG。返された透明背景を維持して採用。
