"""
Generates ptcglleaderboard.ico - the launcher and installer icon.

Deliberately original artwork. The game's own icon is not used and must not be: it is TPCi's
mark, and an installer wearing it would also imply this is an official product.

The mark is three fanned cards with the front one highlighted - "which of these is it". It is
drawn at 4x and downsampled per size so it stays readable at 16px, where a literal 2x3 prize
grid turns to mush.

    python src/branding/make_icon.py
"""
from PIL import Image, ImageDraw

SIZES = [16, 24, 32, 48, 64, 128, 256]
SS = 4  # supersample factor

NAVY_TOP = (38, 52, 92)
NAVY_BOT = (20, 27, 51)
SLATE = (176, 190, 220)
SLATE_DIM = (138, 152, 186)
GOLD = (244, 197, 66)
GOLD_EDGE = (198, 152, 34)


def card(w, h, fill, edge, radius):
    """
    One card on its own layer, positioned so the LAYER CENTRE sits at the card's bottom edge.

    That pivot is the whole trick: rotating about the card's own centre splays the cards outward
    like wings, which is what a real hand of cards does not look like. Fanning about the bottom
    keeps the bases together and spreads only the tops.
    """
    layer = Image.new("RGBA", (w * 3, h * 2), (0, 0, 0, 0))
    x0, y0 = w, 0  # card occupies the top half, horizontally centred
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle(
        (x0, y0, x0 + w, y0 + h), radius=radius, fill=fill, outline=edge,
        width=max(1, w // 14),
    )
    return layer


def render(size):
    r = size * SS
    img = Image.new("RGBA", (r, r), (0, 0, 0, 0))

    # rounded background with a soft vertical gradient
    grad = Image.new("RGBA", (r, r))
    gd = ImageDraw.Draw(grad)
    for y in range(r):
        t = y / max(1, r - 1)
        gd.line(
            [(0, y), (r, y)],
            fill=tuple(int(a + (b - a) * t) for a, b in zip(NAVY_TOP, NAVY_BOT)) + (255,),
        )
    mask = Image.new("L", (r, r), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, r - 1, r - 1), radius=int(r * 0.22), fill=255)
    img.paste(grad, (0, 0), mask)

    cw, ch = int(r * 0.30), int(r * 0.42)
    rad = max(2, int(cw * 0.16))
    # the pivot every card fans around: bottom-centre of the upright card
    px, py = r // 2, int(r * 0.74)

    # back-to-front: the two fanned cards, then the upright gold one in front
    for angle, fill, edge in (
        (-22, SLATE_DIM, None),
        (22, SLATE, None),
        (0, GOLD, GOLD_EDGE),
    ):
        layer = card(cw, ch, fill, edge, rad).rotate(angle, resample=Image.BICUBIC, expand=False)
        img.alpha_composite(layer, (px - layer.width // 2, py - layer.height // 2))

    return img.resize((size, size), Image.LANCZOS)


frames = [render(s) for s in SIZES]
frames[-1].save(
    "src/branding/ptcglleaderboard.ico",
    format="ICO",
    sizes=[(s, s) for s in SIZES],
    append_images=frames[:-1],
)
print("wrote src/branding/ptcglleaderboard.ico with sizes:", SIZES)
