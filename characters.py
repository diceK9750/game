"""Original code-drawn two-head-tall rivals. No external sprite assets.

Milo is a river otter in a blue expedition jacket; Ruby is a fox in a plum
waistcoat. The renderer is injected so pose geometry can be tested headlessly.
"""

import math

INK, DARK, PLUM, TEAL, BROWN, SLATE, GREY, WHITE = range(8)
RED, ORANGE, GOLD, MINT, BLUE, MUTED, PINK, CREAM = range(8, 16)
ACTIONS = ("idle", "celebrate", "victory", "hurt", "frustrated", "defeat")


def draw_rival(g, x, y, species, action, *, motion=True):
    """Draw within a 72 x 70 envelope, including expressive accessories."""
    fox = species == "fox"
    happy = action in {"celebrate", "victory"}
    sad = action in {"hurt", "frustrated", "defeat"}
    tick = g.frame_count if motion else 0
    sway = round(2 * math.sin(tick / (7 if happy else 20)))
    breathe = int(tick // 24 % 2)
    head_y = y + (2 if action == "defeat" else -1 if happy else breathe)
    fur, light = (ORANGE, GOLD) if fox else (BROWN, CREAM)
    coat, accent = (PLUM, PINK) if fox else (BLUE, MINT)

    # Tails sit behind the silhouette and move independently of the head.
    if fox:
        g.tri(x + 42, y + 49, x + 63, y + 21 + sway, x + 65, y + 48, INK)
        g.tri(x + 43, y + 46, x + 61, y + 25 + sway, x + 62, y + 47, fur)
        g.tri(x + 50, y + 39, x + 61, y + 25 + sway, x + 62, y + 38, CREAM)
        g.line(x + 46, y + 47, x + 58, y + 43, BROWN)
    else:
        g.elli(x + 1, y + 33 + sway, 29, 17, INK)
        g.elli(x + 4, y + 35 + sway, 24, 12, BROWN)
        g.line(x + 7, y + 39 + sway, x + 17, y + 41, CREAM)

    # Boots, jacket, shirt, zipper and distinct small badges.
    g.rect(x + 17, y + 46, 13, 10, INK)
    g.rect(x + 34, y + 46, 13, 10, INK)
    g.rect(x + 19, y + 48, 10, 5, coat)
    g.rect(x + 35, y + 48, 9, 5, coat)
    g.rect(x + 17, y + 54, 13, 2, GREY)
    g.rect(x + 34, y + 54, 13, 2, GREY)
    g.elli(x + 16, y + 26, 32, 27, INK)
    g.elli(x + 19, y + 28, 26, 23, coat)
    g.tri(x + 27, y + 29, x + 37, y + 29, x + 32, y + 46, CREAM)
    g.line(x + 32, y + 38, x + 32, y + 49, DARK)
    g.rect(x + 22, y + 40, 5, 3, accent)
    g.pset(x + 39, y + 36, GOLD)
    g.rect(x + 30, y + 44, 4, 3, GOLD)
    # League medallions and stitched shoulder bands distinguish the rivals.
    g.line(x + 21, y + 30, x + 26, y + 34, accent)
    g.line(x + 43, y + 30, x + 38, y + 34, accent)
    g.circ(x + 40, y + 38, 3, INK)
    g.circ(x + 40, y + 38, 2, GOLD)
    g.pset(x + 40, y + 37, WHITE)

    # Raised arms, folded arms or a ready-to-pounce stance.
    if happy:
        for ax, bx in ((20, 10), (44, 54)):
            g.line(x + ax, y + 34, x + bx, y + 23 + sway, INK)
            g.circ(x + bx, y + 23 + sway, 5, INK)
            g.circ(x + bx, y + 23 + sway, 3, fur)
            g.pset(x + bx - 1, y + 22 + sway, CREAM)
    elif action == "frustrated":
        g.rect(x + 18, y + 35, 28, 7, INK)
        g.rect(x + 21, y + 36, 22, 4, coat)
        g.circ(x + 25, y + 38, 3, fur)
        g.circ(x + 40, y + 38, 3, fur)
    else:
        arm_y = y + (44 if sad else 35 + breathe)
        for ax in (16, 48):
            g.circ(x + ax, arm_y, 5, INK)
            g.circ(x + ax, arm_y, 3, fur)
            g.rect(x + ax - 3, arm_y + 2, 6, 2, coat)

    # Ear geometry differentiates the species even in silhouette.
    if fox:
        for a, b, c in ((12, 15, 27), (38, 50, 51)):
            g.tri(x + a, head_y + 10, x + b, head_y - 7, x + c, head_y + 8, INK)
            g.tri(x + a + 3, head_y + 8, x + b, head_y - 3, x + c - 3, head_y + 8, fur)
            g.tri(x + a + 5, head_y + 7, x + b + 1, head_y + 1, x + c - 5, head_y + 7, PLUM)
    else:
        for ex in (16, 48):
            g.circ(x + ex, head_y + 5, 7, INK)
            g.circ(x + ex, head_y + 5, 5, fur)
            g.circ(x + ex, head_y + 5, 2, PINK)
    g.elli(x + 11, head_y + 1, 42, 33, INK)
    g.elli(x + 14, head_y + 3, 36, 28, fur)
    g.elli(x + 18, head_y + 5, 27, 8, light)
    if fox:
        g.tri(x + 14, head_y + 17, x + 31, head_y + 32, x + 28, head_y + 18, CREAM)
        g.tri(x + 50, head_y + 17, x + 33, head_y + 32, x + 36, head_y + 18, CREAM)
        # Flight goggles worn on the forehead, not covering expressive eyes.
        g.rect(x + 13, head_y + 6, 38, 3, PLUM)
        for ex in (19, 34):
            g.rect(x + ex, head_y + 2, 11, 7, INK)
            g.rect(x + ex + 1, head_y + 3, 9, 5, GOLD)
            g.rect(x + ex + 3, head_y + 3, 5, 3, BLUE)
            g.pset(x + ex + 3, head_y + 3, WHITE)
    else:
        g.elli(x + 17, head_y + 17, 29, 14, CREAM)
        g.rect(x + 25, head_y + 2, 15, 3, BROWN)

    # Large eye whites and inward-looking pupils keep both rivals engaged.
    blink = (tick + (71 if fox else 0)) % 211 < 6
    for ex in (21, 38):
        if happy or blink:
            g.line(x + ex, head_y + 17, x + ex + 2, head_y + 15, INK)
            g.line(x + ex + 2, head_y + 15, x + ex + 5, head_y + 17, INK)
        elif sad:
            g.line(x + ex, head_y + 15, x + ex + 5, head_y + 17, INK)
            g.pset(x + ex + 3, head_y + 18, INK)
        else:
            g.rect(x + ex, head_y + 12, 6, 8, INK)
            g.rect(x + ex + 1, head_y + 13, 4, 6, WHITE)
            g.rect(x + ex + (1 if fox else 3), head_y + 15, 2, 4, INK)
    g.rect(x + 29, head_y + 21, 6, 3, INK)
    g.pset(x + 30, head_y + 21, WHITE)
    g.line(x + 32, head_y + 24, x + 32, head_y + 26, INK)
    if happy:
        g.elli(x + 27, head_y + 25, 11, 6, INK)
        g.rect(x + 30, head_y + 28, 5, 2, PINK)
    elif sad:
        g.line(x + 28, head_y + 28, x + 32, head_y + 26, INK)
        g.line(x + 32, head_y + 26, x + 36, head_y + 28, INK)
    else:
        g.line(x + 27, head_y + 26, x + 29, head_y + 28, INK)
        g.line(x + 29, head_y + 28, x + 32, head_y + 26, INK)
        g.line(x + 32, head_y + 26, x + 36, head_y + 27, INK)
    for ex in (18, 43):
        g.rect(x + ex, head_y + 22, 3, 2, PINK)
    if not fox:
        for dy in (22, 25):
            g.line(x + 11, head_y + dy, x + 18, head_y + dy + 1, CREAM)
            g.line(x + 46, head_y + dy + 1, x + 53, head_y + dy, CREAM)

    # A short flowing neckerchief echoes each side's UI colour.
    g.rect(x + 22, head_y + 31, 21, 3, accent)
    g.tri(x + 41, head_y + 32, x + 52, head_y + 35 + sway, x + 45, head_y + 40, accent)
    if sad:
        g.tri(x + 53, head_y + 11, x + 56, head_y + 18, x + 50, head_y + 18, BLUE)
        g.pset(x + 52, head_y + 16, WHITE)
    if happy:
        for sx, sy in ((4, 11), (59, 6)):
            sy += sway
            g.line(x + sx - 2, head_y + sy, x + sx + 2, head_y + sy, GOLD)
            g.line(x + sx, head_y + sy - 2, x + sx, head_y + sy + 2, GOLD)
    if action == "victory":
        g.tri(x + 22, head_y - 3, x + 20, head_y - 10, x + 31, head_y - 5, GOLD)
        g.tri(x + 28, head_y - 4, x + 32, head_y - 12, x + 37, head_y - 4, GOLD)
        g.tri(x + 34, head_y - 5, x + 44, head_y - 10, x + 42, head_y - 3, GOLD)
        g.rect(x + 23, head_y - 4, 18, 3, GOLD)
