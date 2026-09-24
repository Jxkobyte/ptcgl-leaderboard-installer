"""
Generates ptcglleaderboard.ico - the icon on the launcher, the installer, and the
"Pokemon TCG Live (Leaderboard & Match History)" shortcut - and ptcglleaderboard.icns, the
same mark for the macOS "PTCGL Leaderboard" app.

Deliberately original artwork. The game's own icon is not used and must not be: it is TPCi's
mark, and an installer wearing it would also imply this is an official product.

The mark is a gold trophy with a star on a navy tile - it is a leaderboard. It replaced three
fanned cards, which said "card game tool" but not what this one does. Drawn at 4x on a 100-unit
grid and downsampled per size; at 24px and below the handles thicken and the star and shading are
dropped, because fine detail at 16px turns to a smudge.

    python src/branding/make_icon.py

The launcher embeds its own copy: after regenerating, copy the .ico to
PtcglLeaderboard\Launcher\ptcglleaderboard.ico as well.
"""
import sys
from PIL import Image, ImageDraw

SIZES = [16, 24, 32, 48, 64, 128, 256]
SS = 4

NAVY_TOP = (38, 52, 92)
NAVY_BOT = (20, 27, 51)
GOLD = (244, 197, 66)
GOLD_LIGHT = (255, 226, 130)
GOLD_EDGE = (198, 152, 34)
GOLD_DEEP = (170, 124, 22)
SLATE = (176, 190, 220)


def render(size):
    r = size * SS
    img = Image.new("RGBA", (r, r), (0, 0, 0, 0))

    grad = Image.new("RGBA", (r, r))
    gd = ImageDraw.Draw(grad)
    for y in range(r):
        t = y / max(1, r - 1)
        gd.line([(0, y), (r, y)],
                fill=tuple(int(a + (b - a) * t) for a, b in zip(NAVY_TOP, NAVY_BOT)) + (255,))
    mask = Image.new("L", (r, r), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, r - 1, r - 1), radius=int(r * 0.22), fill=255)
    img.paste(grad, (0, 0), mask)

    d = ImageDraw.Draw(img)
    u = r / 100.0                      # design on a 100-unit grid
    P = lambda x, y: (x * u, y * u)
    # Small sizes get thicker handles and no fine detail - at 16px a thin ring is a smudge.
    small = size <= 24
    hw = (6.5 if small else 5.0) * u   # handle stroke

    # handles: rings either side of the bowl, drawn first so the bowl covers their inner half
    for cx in (27, 73):
        rad = 11
        d.ellipse((P(cx - rad, 22) + P(cx + rad, 22 + 2 * rad)), outline=GOLD_EDGE, width=int(hw))

    # bowl: flat rim, straight flanks tapering into a rounded bottom
    bowl = [P(26, 18), P(74, 18), P(72, 36), P(66, 50), P(58, 57), P(50, 59),
            P(42, 57), P(34, 50), P(28, 36)]
    d.polygon(bowl, fill=GOLD)
    # rim
    d.rounded_rectangle(P(23, 15) + P(77, 21), radius=int(2 * u), fill=GOLD_LIGHT)

    # stem and knot
    d.polygon([P(46, 58), P(54, 58), P(52.5, 70), P(47.5, 70)], fill=GOLD_EDGE)
    d.ellipse(P(43, 66) + P(57, 72), fill=GOLD)

    # base: a stepped plinth
    d.rounded_rectangle(P(35, 71) + P(65, 77), radius=int(1.5 * u), fill=GOLD)
    d.rounded_rectangle(P(29, 77) + P(71, 86), radius=int(2 * u), fill=GOLD_DEEP)

    if not small:
        # shading: the right half of the bowl a touch darker, a highlight streak on the left
        shade = Image.new("RGBA", (r, r), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shade)
        sd.polygon([P(50, 21), P(74, 21), P(72, 36), P(66, 50), P(58, 57), P(50, 59)],
                   fill=GOLD_EDGE + (95,))
        img.alpha_composite(shade)
        d = ImageDraw.Draw(img)
        d.line([P(34, 25), P(36, 44)], fill=GOLD_LIGHT, width=int(3 * u))
        # a star on the bowl - the "first place" read
        cx, cy, ro, ri = 50, 36, 8.5, 3.6
        import math
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            rr = ro if k % 2 == 0 else ri
            pts.append(P(cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=NAVY_BOT)

    return img.resize((size, size), Image.LANCZOS)


frames = {s: render(s) for s in SIZES}
frames[256].save(
    "src/branding/ptcglleaderboard.ico",
    format="ICO",
    sizes=[(s, s) for s in SIZES],
    append_images=[frames[s] for s in SIZES[:-1]],
)
print("wrote src/branding/ptcglleaderboard.ico with sizes:", SIZES)

# macOS: the same mark for the "PTCGL Leaderboard" launcher app. Mac icons sit inset in their
# canvas (824 of 1024 for the tile) rather than filling it, so it is drawn smaller and centred;
# Pillow derives the other ICNS sizes from the 1024 one.
mac = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
mac.paste(render(824), (100, 100))
mac.save("src/branding/ptcglleaderboard.icns", format="ICNS")
print("wrote src/branding/ptcglleaderboard.icns")
