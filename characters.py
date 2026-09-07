"""Rin the rabbit and Koh the red panda: lightweight native/fallback artwork.

The browser uses the matching HD expression atlases when available. This
renderer stays dependency-free, animated and fully playable offline.
"""
import math

INK, DARK, PLUM, TEAL, BROWN, SLATE, GREY, WHITE = range(8)
RED, ORANGE, GOLD, MINT, BLUE, MUTED, PINK, CREAM = range(8, 16)
ACTIONS = ("idle", "celebrate", "victory", "hurt", "frustrated", "defeat")


def draw_rival(g, x, y, species, action, *, motion=True):
    panda = species in {"red_panda", "fox"}
    if species not in {"rabbit", "red_panda", "otter", "fox"}:
        raise ValueError("unknown character")
    if action not in ACTIONS:
        raise ValueError("unknown pose")
    tick = g.frame_count if motion else 42
    happy = action in {"celebrate", "victory"}
    sad = action in {"hurt", "frustrated", "defeat"}
    sway = round(2 * math.sin(tick / 18)) if motion else 0
    bob = int(tick // 28 % 2) if motion else 0
    hy = y + (3 if action == "defeat" else -1 if happy else bob)
    fur, shade, face = (ORANGE, BROWN, CREAM) if panda else (WHITE, MUTED, CREAM)
    coat, scarf = (PLUM, PINK) if panda else (BLUE, MINT)

    # Tail silhouettes: a curled banded plume versus a cotton puff.
    if panda:
        g.elli(x + 39, y + 18 + sway, 29, 34, INK)
        g.elli(x + 42, y + 20 + sway, 24, 29, BROWN)
        g.elli(x + 44, y + 20 + sway, 19, 12, ORANGE)
        g.elli(x + 48, y + 34 + sway, 15, 8, ORANGE)
        g.elli(x + 39, y + 43 + sway, 21, 9, ORANGE)
        g.line(x + 54, y + 23 + sway, x + 58, y + 26 + sway, GOLD)
    else:
        g.circ(x + 13, y + 43, 8, shade)
        g.circ(x + 12, y + 41, 6, WHITE)

    # Rounded boots and layered miniature explorer outfits.
    for bx in (19, 35):
        g.elli(x + bx - 2, y + 46, 15, 11, INK)
        g.elli(x + bx, y + 47, 11, 7, DARK)
        g.line(x + bx, y + 55, x + bx + 10, y + 55, GOLD)
        g.rect(x + bx + 3, y + 49, 4, 2, BROWN)
    g.elli(x + 16, y + 27, 33, 25, INK)
    g.elli(x + 19, y + 29, 27, 21, coat)
    g.tri(x + 28, y + 29, x + 36, y + 29, x + 32, y + 46, CREAM)
    g.line(x + 32, y + 35, x + 32, y + 48, DARK)
    g.line(x + 22, y + 33, x + 25, y + 40, WHITE if not panda else PINK)
    g.rect(x + 22, y + 45, 21, 3, BROWN)
    g.rect(x + 30, y + 44, 5, 4, GOLD)
    g.circ(x + 40, y + 38, 4, BROWN)
    g.circ(x + 40, y + 38, 3, GOLD)
    g.pset(x + 39, y + 36, WHITE)

    if happy:
        for ax in (11, 53):
            g.line(x + (21 if ax == 11 else 43), y + 34, x + ax, y + 22 + sway, INK)
            g.circ(x + ax, y + 22 + sway, 5, shade)
            g.circ(x + ax, y + 21 + sway, 4, fur)
    elif action == "frustrated":
        g.rect(x + 17, y + 36, 30, 7, coat)
        g.circ(x + 24, y + 40, 4, fur)
        g.circ(x + 41, y + 38, 4, fur)
        g.line(x + 28, y + 40, x + 39, y + 38, shade)
    else:
        ay = y + (31 if action == "hurt" else 45 if action == "defeat" else 36 + bob)
        for ax in (16, 49):
            g.circ(x + ax, ay, 5, shade)
            g.circ(x + ax - 1, ay - 1, 4, fur)

    # Koh is a dark enchantress: layered skirt, cape and long plum hair.
    if panda:
        g.tri(x + 18, y + 27, x + 7, y + 50, x + 31, y + 47, PLUM)
        g.tri(x + 42, y + 27, x + 57, y + 50, x + 30, y + 47, DARK)
        g.tri(x + 24, y + 33, x + 13, y + 48, x + 48, y + 48, DARK)
        g.line(x + 15, y + 48, x + 46, y + 48, PINK)
        g.elli(x + 7, hy + 3, 17, 44, PLUM)
        g.elli(x + 44, hy + 5, 16, 41, PLUM)
        g.line(x + 10, hy + 23, x + 13, hy + 42, PINK)
    # Long soft rabbit ears; Koh has rounded ears.
    if panda:
        for ex in (17, 46):
            g.circ(x + ex, hy + 3, 8, INK)
            g.circ(x + ex, hy + 3, 6, CREAM)
            g.circ(x + ex, hy + 3, 4, PLUM)
    elif action == "defeat":
        g.elli(x + 4, hy + 1, 22, 9, shade)
        g.elli(x + 7, hy + 1, 18, 6, WHITE)
        g.elli(x + 43, hy + 2, 19, 12, shade)
        g.elli(x + 45, hy + 3, 15, 8, WHITE)
    else:
        g.elli(x + 17, hy - 11, 11, 27, shade)
        g.elli(x + 18, hy - 10, 9, 24, WHITE)
        g.elli(x + 21, hy - 7, 4, 19, PINK)
        g.elli(x + 39, hy - 8, 14, 23, shade)
        g.elli(x + 40, hy - 7, 11, 21, WHITE)
        g.elli(x + 43, hy - 4, 5, 15, PINK)
        g.elli(x + 46, hy - 5, 12, 8, WHITE)

    g.elli(x + 10, hy + 2, 45, 34, shade)
    g.elli(x + 12, hy + 3, 41, 31, fur)
    g.elli(x + 17, hy + 5, 29, 9, face)
    g.elli(x + 18, hy + 19, 28, 14, face)
    if panda:
        for ex in (16, 35):
            g.elli(x + ex, hy + 12, 15, 14, CREAM)
        g.tri(x + 13, hy + 16, x + 7, hy + 22, x + 21, hy + 24, CREAM)
        g.tri(x + 51, hy + 16, x + 58, hy + 22, x + 43, hy + 24, CREAM)
    else:
        g.tri(x + 24, hy + 6, x + 29, hy - 1, x + 37, hy + 6, WHITE)

    blink = motion and (tick + (83 if panda else 0)) % 223 < 5
    for ex in (21, 38):
        if happy and action != "victory" or blink:
            g.line(x + ex, hy + 18, x + ex + 3, hy + 16, INK)
            g.line(x + ex + 3, hy + 16, x + ex + 6, hy + 18, INK)
        else:
            g.elli(x + ex - 1, hy + 12, 9, 12, INK)
            g.elli(x + ex, hy + 13, 7, 10, WHITE)
            g.elli(x + ex + (0 if panda else 2), hy + 15, 5, 8, PINK if panda else BROWN)
            g.elli(x + ex + (1 if panda else 3), hy + 16, 3, 6, INK)
            g.pset(x + ex + 2, hy + 15, WHITE)
            if panda:
                g.line(x + ex - 2, hy + 11, x + ex + 1, hy + 14, INK)
    if panda:
        g.tri(x + 13, hy + 9, x + 30, hy - 2, x + 36, hy + 3, PLUM)
        for cx, cy in ((24, -5), (32, -10), (40, -5)):
            g.tri(x + cx - 4, hy + 2, x + cx, hy + cy, x + cx + 4, hy + 2, DARK)
            g.line(x + cx, hy + cy, x + cx + 3, hy + 1, PINK)
            g.pset(x + ex + 4, hy + 20, MINT if panda else GOLD)
        if action == "frustrated":
            g.line(x + ex, hy + 11, x + ex + 6, hy + 14, INK)
        elif action == "defeat":
            g.line(x + ex, hy + 14, x + ex + 6, hy + 12, shade)
    g.elli(x + 29, hy + 23, 6, 4, INK if panda else PINK)
    g.pset(x + 30, hy + 23, WHITE)
    if happy:
        g.elli(x + 27, hy + 27, 11, 6, INK)
        g.elli(x + 29, hy + 30, 7, 3, PINK)
    elif action == "hurt":
        g.elli(x + 29, hy + 28, 6, 6, INK)
    elif sad:
        g.line(x + 28, hy + 31, x + 32, hy + 29, INK)
        g.line(x + 32, hy + 29, x + 36, hy + 31, INK)
    else:
        g.line(x + 27, hy + 28, x + 31, hy + 30, INK)
        g.line(x + 31, hy + 30, x + 37, hy + 28, INK)
    g.rect(x + 22, hy + 34, 22, 3, scarf)
    g.tri(x + 42, hy + 34, x + 59, hy + 37 + sway, x + 47, hy + 43, scarf)
    g.line(x + 24, hy + 34, x + 41, hy + 34, WHITE)
    if happy:
        for sx, sy in ((4, 11), (62, 9)):
            g.line(x + sx - 2, hy + sy, x + sx + 2, hy + sy, GOLD)
            g.line(x + sx, hy + sy - 2, x + sx, hy + sy + 2, GOLD)
    if action == "victory":
        g.tri(x + 29, hy - 8, x + 32, hy - 13, x + 35, hy - 8, GOLD)
        g.tri(x + 27, hy - 10, x + 37, hy - 10, x + 32, hy - 5, GOLD)
