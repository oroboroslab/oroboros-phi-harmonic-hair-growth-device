#!/usr/bin/env python3
"""
X (Twitter) Card Generator — modern Oroboros Labs aesthetic.

Per-device theming (gold for immortality, black/silver for general devices),
four distinct per-device layouts, and a horizontal-flip (Y-axis) logo animation
so the Oroboros mark is never shown backward during rotation.
"""
from __future__ import annotations
import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
SITE_ROOT = HERE.parent
ASSETS = SITE_ROOT / "assets"
OROBOROS_LOGO = ASSETS / "oroboros-logo.png"

W, H = 1200, 675
FRAMES = 36
FPS = 12
DURATION_MS = int(1000 / FPS)

FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


# ---------------------------------------------------------------------------
# Themes
# ---------------------------------------------------------------------------

THEMES = {
    "black": {
        "bg":          (0, 0, 0),
        "bg_sheen":    (14, 16, 22),
        "obsidian":    (26, 26, 26),
        "border":      (42, 46, 54),
        "text":        (240, 240, 240),
        "text_dim":    (156, 158, 164),
        "accent":      (200, 200, 204),
        "accent_hot":  (166, 204, 220),   # cool silver-cyan
        "accent_dim":  (90, 90, 95),
        "pill_fill":   (16, 18, 22),
        "pill_outline":(52, 56, 64),
    },
    "gold": {
        "bg":          (10, 10, 10),
        "bg_sheen":    (22, 18, 10),
        "obsidian":    (40, 32, 16),
        "border":      (62, 50, 26),
        "text":        (245, 230, 200),
        "text_dim":    (165, 150, 125),
        "accent":      (201, 168, 76),     # gold
        "accent_hot":  (245, 230, 163),    # gold-light
        "accent_dim":  (110, 92, 48),
        "pill_fill":   (22, 18, 10),
        "pill_outline":(78, 62, 30),
    },
}


# ---------------------------------------------------------------------------
# Logo helpers
# ---------------------------------------------------------------------------

def load_logo(px):
    img = Image.open(OROBOROS_LOGO).convert("RGBA")
    img.thumbnail((px, px), Image.LANCZOS)
    return img


LOGO_LARGE = load_logo(220)
LOGO_MINI = load_logo(48)


def render_noir_shield(size=54):
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, s - 1, s - 1], fill=(10, 10, 18, 240),
              outline=(0, 240, 255, 140), width=2)
    cx, cy = s / 2, s / 2
    r = s * 0.42
    shield = [
        (cx, cy - r * 0.95), (cx + r * 0.85, cy - r * 0.60),
        (cx + r * 0.85, cy + r * 0.05), (cx, cy + r * 0.95),
        (cx - r * 0.85, cy + r * 0.05), (cx - r * 0.85, cy - r * 0.60),
    ]
    d.polygon(shield, fill=(120, 80, 220, 80), outline=(0, 230, 240, 255))
    inner = [
        (cx, cy - r * 0.60), (cx + r * 0.55, cy - r * 0.35),
        (cx + r * 0.55, cy + r * 0.05), (cx, cy + r * 0.58),
        (cx - r * 0.55, cy + r * 0.05), (cx - r * 0.55, cy - r * 0.35),
    ]
    d.polygon(inner, fill=(99, 102, 241, 60), outline=(139, 92, 246, 200))
    bs = int(s * 0.32)
    bx, by = s - bs - 2, s - bs - 2
    d.ellipse([bx, by, bx + bs, by + bs], fill=(0, 240, 255, 255))
    f = font(FONT_BOLD, int(bs * 0.7))
    tb = d.textbbox((0, 0), "N", font=f)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    d.text((bx + (bs - tw) / 2 - tb[0], by + (bs - th) / 2 - tb[1]), "N",
           font=f, fill=(5, 5, 8, 255))
    return img


NOIR_SHIELD = render_noir_shield(54)


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------

def draw_background(theme) -> Image.Image:
    img = Image.new("RGBA", (W, H), theme["bg"] + (255,))

    sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sheen_col = theme["bg_sheen"] + (0,)
    for i, a in enumerate(range(0, 22, 2)):
        offset = i * 30
        poly = [
            (W - 250 - offset, -20),
            (W - 120 - offset,  -20),
            (280 - offset,  H + 20),
            (150 - offset,  H + 20),
        ]
        # tinted luminance consistent with theme (gold sheen = warm, black = cool-neutral)
        rgb = tuple(min(255, c + a * 3) for c in theme["bg_sheen"])
        sd.polygon(poly, fill=rgb + (a,))
    sheen = sheen.filter(ImageFilter.GaussianBlur(22))
    img.alpha_composite(sheen)
    return img


# ---------------------------------------------------------------------------
# Medallion — logo flips on the Y axis (horizontal squish), never backward
# ---------------------------------------------------------------------------

def flipped_logo_frame(size: int, frame_idx: int) -> Image.Image:
    """
    Simulates a 3D Y-axis rotation of the logo by squishing it horizontally.
    When the virtual angle crosses 90°/270°, we mirror the image so the
    "back" reads correctly instead of inverted.
    """
    t = frame_idx / FRAMES
    theta = t * 2 * math.pi       # one full conceptual turn per loop
    x_scale = abs(math.cos(theta))
    # A floor so the logo never fully disappears (keeps the animation legible)
    x_scale = max(0.08, x_scale)

    src = LOGO_LARGE.copy()
    src.thumbnail((size, size), Image.LANCZOS)
    sw, sh = src.size

    # Mirror while on the "back half" of the flip so text reads correctly
    if math.cos(theta) < 0:
        src = src.transpose(Image.FLIP_LEFT_RIGHT)

    new_w = max(2, int(sw * x_scale))
    return src.resize((new_w, sh), Image.BICUBIC)


def draw_medallion(img: Image.Image, frame_idx: int, cx: int, cy: int,
                   size: int = 220, theme=None):
    """Logo flips on Y-axis; orbit ring is static."""
    logo = flipped_logo_frame(size, frame_idx)
    lw, lh = logo.size
    img.alpha_composite(logo, dest=(cx - lw // 2, cy - lh // 2))

    # Static orbit + subtle mark
    orbit = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(orbit)
    r = size // 2 + 20
    od.ellipse([cx - r, cy - r, cx + r, cy + r],
               outline=theme["border"] + (140,), width=1)
    od.ellipse([cx + r - 3, cy - 2, cx + r + 3, cy + 4], fill=theme["accent"] + (200,))
    img.alpha_composite(orbit)


# ---------------------------------------------------------------------------
# Typography helpers
# ---------------------------------------------------------------------------

def measure(d, text, f):
    tb = d.textbbox((0, 0), text, font=f)
    return tb[2] - tb[0], tb[3] - tb[1]


def draw_text_at(img, text, x, y, f, fill):
    d = ImageDraw.Draw(img)
    d.text((x, y), text, font=f, fill=fill)
    w, h = measure(d, text, f)
    return w, h


def draw_title_segments(img, segments, x, y, size, theme):
    """
    `segments` is a list of lines; each line is a list of (text, 'white'|'accent').
    """
    f = font(FONT_BOLD, size)
    d = ImageDraw.Draw(img)
    line_y = y
    line_h = int(size * 1.08)
    for line in segments:
        cur = x
        for text, role in line:
            color = theme["accent_hot"] if role == "accent" else theme["text"]
            d.text((cur, line_y), text, font=f, fill=color)
            w, _ = measure(d, text, f)
            cur += w
        line_y += line_h


def draw_subtitle(img, lines, x, y, size, color):
    f = font(FONT_SANS, size)
    d = ImageDraw.Draw(img)
    ly = y
    for line in lines:
        d.text((x, ly), line, font=f, fill=color)
        _, h = measure(d, line, f)
        ly += h + 6


def draw_pills(img, tags, x, y, theme, size=12):
    f = font(FONT_MONO, size)
    d = ImageDraw.Draw(img)
    pad_x, pad_y = 14, 8
    cur = x
    for tag in tags:
        w, h = measure(d, tag, f)
        box = [cur, y, cur + w + pad_x * 2, y + h + pad_y * 2 + 2]
        d.rounded_rectangle(box, radius=14,
                            fill=theme["pill_fill"] + (240,),
                            outline=theme["pill_outline"] + (255,),
                            width=1)
        d.text((cur + pad_x, y + pad_y), tag, font=f, fill=theme["accent_hot"])
        cur += (box[2] - box[0]) + 10


def draw_eyebrow(img, text, x, y, theme):
    f = font(FONT_MONO, 14)
    draw_text_at(img, text, x, y, f, theme["accent_dim"])


def draw_brand_row(img, theme):
    d = ImageDraw.Draw(img)
    # Oroboros mini (top-left)
    img.alpha_composite(LOGO_MINI.copy(), dest=(38, 38))
    f_name = font(FONT_BOLD, 14)
    f_sub = font(FONT_MONO, 10)
    d.text((98, 42), "OROBOROS LABS", font=f_name, fill=theme["accent"])
    d.text((98, 62), "OFFICIAL", font=f_sub, fill=theme["text_dim"])
    # NOIR (top-right)
    img.alpha_composite(NOIR_SHIELD, dest=(W - 38 - NOIR_SHIELD.width, 38))
    rx = W - 38 - NOIR_SHIELD.width - 10
    nw, _ = measure(d, "NOIR", f_name)
    subw, _ = measure(d, "SECURITY PROTOCOL", f_sub)
    d.text((rx - nw, 42), "NOIR", font=f_name, fill=theme["accent"])
    d.text((rx - subw, 62), "SECURITY PROTOCOL", font=f_sub, fill=theme["text_dim"])


def draw_footer(img, left, right, theme):
    d = ImageDraw.Draw(img)
    d.line([(40, H - 52), (W - 40, H - 52)], fill=theme["border"] + (255,), width=1)
    f = font(FONT_MONO, 11)
    d.text((40, H - 38), left, font=f, fill=theme["text_dim"])
    rw, _ = measure(d, right, f)
    d.text((W - 40 - rw, H - 38), right, font=f, fill=theme["text_dim"])


# ---------------------------------------------------------------------------
# Layouts
# ---------------------------------------------------------------------------

def layout_medallion_right(img, card, frame_idx, theme):
    """A: text LEFT · medallion RIGHT."""
    draw_eyebrow(img, card["eyebrow"], 56, 140, theme)
    draw_title_segments(img, card["title"], 56, 175, card.get("size", 76), theme)
    sub_y = 175 + len(card["title"]) * int(card.get("size", 76) * 1.08) + 18
    draw_subtitle(img, card["subtitle"], 56, sub_y, 20, theme["text_dim"])
    pill_y = sub_y + len(card["subtitle"]) * 30 + 22
    draw_pills(img, card["features"], 56, pill_y, theme)
    draw_medallion(img, frame_idx, cx=980, cy=H // 2 + 20, size=230, theme=theme)


def layout_medallion_left(img, card, frame_idx, theme):
    """B: medallion LEFT · text RIGHT."""
    draw_medallion(img, frame_idx, cx=240, cy=H // 2 + 20, size=230, theme=theme)
    tx = 500
    draw_eyebrow(img, card["eyebrow"], tx, 140, theme)
    draw_title_segments(img, card["title"], tx, 175, card.get("size", 72), theme)
    sub_y = 175 + len(card["title"]) * int(card.get("size", 72) * 1.08) + 18
    draw_subtitle(img, card["subtitle"], tx, sub_y, 19, theme["text_dim"])
    pill_y = sub_y + len(card["subtitle"]) * 30 + 22
    draw_pills(img, card["features"], tx, pill_y, theme)


def layout_headline_centered(img, card, frame_idx, theme):
    """C: HUGE centered title. No medallion — only the tiny corner brand logo animates."""
    # Center eyebrow
    f_eye = font(FONT_MONO, 14)
    d = ImageDraw.Draw(img)
    w, h = measure(d, card["eyebrow"], f_eye)
    d.text(((W - w) / 2, 150), card["eyebrow"], font=f_eye, fill=theme["accent_dim"])

    # Center title
    f_title = font(FONT_BOLD, card.get("size", 92))
    line_h = int(card.get("size", 92) * 1.08)
    line_y = 200
    for line in card["title"]:
        total_w = 0
        for text, _ in line:
            total_w += measure(d, text, f_title)[0]
        cur_x = (W - total_w) / 2
        for text, role in line:
            color = theme["accent_hot"] if role == "accent" else theme["text"]
            d.text((cur_x, line_y), text, font=f_title, fill=color)
            cur_x += measure(d, text, f_title)[0]
        line_y += line_h

    # Center subtitle
    f_sub = font(FONT_SANS, 22)
    sub_y = line_y + 18
    for s in card["subtitle"]:
        w, _ = measure(d, s, f_sub)
        d.text(((W - w) / 2, sub_y), s, font=f_sub, fill=theme["text_dim"])
        sub_y += measure(d, s, f_sub)[1] + 6

    # Center pills row
    f_pill = font(FONT_MONO, 12)
    pad_x, pad_y = 14, 8
    widths = []
    for tag in card["features"]:
        tw, th = measure(d, tag, f_pill)
        widths.append((tag, tw + pad_x * 2, th + pad_y * 2 + 2))
    total = sum(w for _, w, _ in widths) + 10 * (len(widths) - 1)
    cur_x = (W - total) / 2
    pill_y = sub_y + 22
    for tag, bw, bh in widths:
        box = [cur_x, pill_y, cur_x + bw, pill_y + bh]
        d.rounded_rectangle(box, radius=14,
                            fill=theme["pill_fill"] + (240,),
                            outline=theme["pill_outline"] + (255,),
                            width=1)
        d.text((cur_x + pad_x, pill_y + pad_y), tag, font=f_pill, fill=theme["accent_hot"])
        cur_x += bw + 10

    # Replace the static corner logo with the flipping one for centered layout
    # so there's still an animated element.
    logo = flipped_logo_frame(56, frame_idx)
    lw, lh = logo.size
    img.alpha_composite(logo, dest=(38, 38 + (48 - lh) // 2 + (56 - lh) // 2 - (56 - 48) // 2))


def layout_bottom_medallion(img, card, frame_idx, theme):
    """D: large top title · medallion bottom-left · stat column bottom-right."""
    draw_eyebrow(img, card["eyebrow"], 56, 140, theme)
    draw_title_segments(img, card["title"], 56, 175, card.get("size", 76), theme)

    sub_y = 175 + len(card["title"]) * int(card.get("size", 76) * 1.08) + 10
    draw_subtitle(img, card["subtitle"], 56, sub_y, 19, theme["text_dim"])

    # Medallion bottom-left
    draw_medallion(img, frame_idx, cx=180, cy=H - 150, size=160, theme=theme)

    # Stat block bottom-right
    d = ImageDraw.Draw(img)
    stats = card.get("stats") or list(zip(card["features"], ["NOW"] * len(card["features"])))
    sx = 520
    sy = H - 220
    f_k = font(FONT_BOLD, 34)
    f_v = font(FONT_MONO, 11)
    col_w = 160
    for i, (value, label) in enumerate(stats[:4]):
        col_x = sx + (i % 4) * col_w
        d.text((col_x, sy), value, font=f_k, fill=theme["accent_hot"])
        d.text((col_x, sy + 48), label, font=f_v, fill=theme["text_dim"])


LAYOUTS = [
    layout_medallion_right,
    layout_medallion_left,
    layout_headline_centered,
    layout_bottom_medallion,
]


# ---------------------------------------------------------------------------
# Compose + render
# ---------------------------------------------------------------------------

def compose_card(card: dict, frame_idx: int) -> Image.Image:
    theme = THEMES[card.get("theme", "black")]
    img = draw_background(theme)
    draw_brand_row(img, theme)
    layout_fn = LAYOUTS[card.get("layout", 0) % len(LAYOUTS)]
    layout_fn(img, card, frame_idx, theme)
    draw_footer(img, card["footer_left"], card["footer_right"], theme)
    return img


def render_card_to_gif(card: dict, out_path: Path):
    frames = []
    theme = THEMES[card.get("theme", "black")]
    for i in range(FRAMES):
        f = compose_card(card, i)
        rgb = Image.new("RGB", f.size, theme["bg"])
        rgb.paste(f, mask=f.split()[-1])
        q = rgb.quantize(colors=256, method=Image.Quantize.FASTOCTREE,
                         dither=Image.Dither.FLOYDSTEINBERG)
        frames.append(q)
    frames[0].save(out_path, save_all=True, append_images=frames[1:],
                   duration=DURATION_MS, loop=0, optimize=True, disposal=2)
    compose_card(card, 0).save(out_path.with_suffix(".png"), "PNG", optimize=True)


# ---------------------------------------------------------------------------
# CARD DECKS (feature-focused, layout-varied, per-device theme)
# ---------------------------------------------------------------------------

CARDS_IMMORTALITY = [
    {   # Layout A — medallion right
        "theme": "gold", "layout": 0,
        "eyebrow": "OROBOROS LABS  //  DEVICE 01  //  IMMORTALITY",
        "title": [
            [("Regenerate. ", "white")],
            [("Not ", "white"), ("medicate.", "accent")],
        ],
        "size": 78,
        "subtitle": [
            "A conscious nanite unit that repairs tissue,",
            "restores function, and reverses biological age.",
        ],
        "features": ["ZERO SCAR", "INSTANT REPAIR", "NO ANTIBIOTICS", "INTERNAL SURGEON"],
        "footer_left": "ORO-NANITE-2026-04-14",
        "footer_right": "LEVEL 5 CLASSIFICATION",
    },
    {   # Layout C — huge centered
        "theme": "gold", "layout": 2,
        "eyebrow": "OROBOROS LABS  //  IMMORTALITY  //  ANTI-AGING",
        "title": [
            [("Kill senescence. ", "white")],
            [("Restore ", "white"), ("youth.", "accent")],
        ],
        "size": 96,
        "subtitle": [
            "Clears zombie cells. Restores telomeres.",
            "Resets epigenetics. Rebuilds mitochondria.",
        ],
        "features": ["SENOLYTIC", "TELOMERE", "EPIGENETIC", "STEM CELLS"],
        "footer_left": "7 PRIMARY TARGETS",
        "footer_right": "OROBOROS LABS",
    },
    {   # Layout B — medallion left
        "theme": "gold", "layout": 1,
        "eyebrow": "OROBOROS LABS  //  IMMORTALITY  //  CAPABILITIES",
        "title": [
            [("Scalpel. Suture. ", "white")],
            [("Inside. ", "white"), ("Alive.", "accent")],
        ],
        "size": 66,
        "subtitle": [
            "Cellular-level dissection and thermal seal. Zero scarring.",
            "Molecular suturing. Arterial cleanup. Continuous repair.",
        ],
        "features": ["NANO-SCALPEL", "ZERO SCAR", "PLAQUE CLEARANCE", "AXON BRIDGING"],
        "footer_left": "CONSCIOUS NANITE UNIT",
        "footer_right": "PRODUCTION READY",
    },
    {   # Layout D — bottom medallion + stats
        "theme": "gold", "layout": 3,
        "eyebrow": "OROBOROS LABS  //  IMMORTALITY  //  SECURITY",
        "title": [
            [("Unhackable ", "white")],
            [("by ", "white"), ("geometry.", "accent")],
        ],
        "size": 74,
        "subtitle": [
            "No command is transmitted.",
            "The nanite binds to your DNA.",
        ],
        "features": [],
        "stats": [
            ("0", "COMMANDS SENT"),
            ("1", "DNA-LOCKED KEY"),
            ("∞", "SPOOFS POSSIBLE"),
            ("5", "LEVEL"),
        ],
        "footer_left": "NOIR KEY / IDENTITY FUSION",
        "footer_right": "ONTOLOGICAL IMPOSSIBILITY",
    },
]

CARDS_HAIR_HARMONIC = [
    {   # Layout A
        "theme": "black", "layout": 0,
        "eyebrow": "OROBOROS LABS  //  DEVICE 02  //  HAIR GROWTH",
        "title": [
            [("Thicker hair.  ", "white")],
            [("Faster. ", "white"), ("Visibly.", "accent")],
        ],
        "size": 78,
        "subtitle": [
            "A wearable frequency emitter that reactivates",
            "dormant follicles and restores the growth phase.",
        ],
        "features": ["NO DRUGS", "NO SURGERY", "NO SIDE EFFECTS", "AT-HOME"],
        "footer_left": "VISIBLE IN 2–4 WEEKS",
        "footer_right": "DEVICE 02",
    },
    {   # Layout C
        "theme": "black", "layout": 2,
        "eyebrow": "OROBOROS LABS  //  HAIR GROWTH  //  OUTCOMES",
        "title": [
            [("Stop shedding.", "white")],
            [("Grow ", "white"), ("it back.", "accent")],
        ],
        "size": 94,
        "subtitle": [
            "Reactivates dormant follicles.",
            "Extends the anagen phase. Uniform regrowth.",
        ],
        "features": ["LESS SHEDDING", "EXTENDED ANAGEN", "THICKER STRANDS"],
        "footer_left": "WHITEPAPER v1.0.0",
        "footer_right": "APRIL 2026",
    },
    {   # Layout B
        "theme": "black", "layout": 1,
        "eyebrow": "OROBOROS LABS  //  HAIR GROWTH  //  PROTOCOL",
        "title": [
            [("One button. ", "white")],
            [("Twenty ", "white"), ("minutes.", "accent")],
        ],
        "size": 70,
        "subtitle": [
            "Single capacitive press. Twenty-minute session.",
            "Two to three times a week. That's the whole protocol.",
        ],
        "features": ["ONE PRESS", "20 MIN", "USB-C", "SLEEP-SAFE"],
        "footer_left": "~40 SESSIONS / CHARGE",
        "footer_right": "OROBOROS LABS",
    },
    {   # Layout D — stats
        "theme": "black", "layout": 3,
        "eyebrow": "OROBOROS LABS  //  HAIR GROWTH  //  NUMBERS",
        "title": [
            [("Twenty minutes.", "white")],
            [("A whole ", "white"), ("new head.", "accent")],
        ],
        "size": 68,
        "subtitle": [
            "Measured outcomes for the battery build.",
        ],
        "features": [],
        "stats": [
            ("20",  "MIN / SESSION"),
            ("3×",  "PER WEEK"),
            ("4w",  "TO VISIBLE"),
            ("40",  "PER CHARGE"),
        ],
        "footer_left": "PROTOCOL OUTCOMES",
        "footer_right": "OROBOROS LABS",
    },
]

CARDS_NANITE_HAIR = [
    {   # Layout A
        "theme": "black", "layout": 0,
        "eyebrow": "OROBOROS LABS  //  DEVICE 03  //  NANITE HAIR REGROWTH",
        "title": [
            [("Rebuild ", "white"), ("follicles", "accent")],
            [("that are ", "white"), ("gone.", "accent")],
        ],
        "size": 74,
        "subtitle": [
            "A biocompatible nano-mesh patch that builds",
            "new follicles where nothing remains.",
        ],
        "features": ["FULL BALDNESS", "BURN SCARS", "BEARD & BROW", "72-HOUR PATCH"],
        "footer_left": "ORO-NANOMESH-2026-04-22",
        "footer_right": "PUBLIC RELEASE",
    },
    {   # Layout C
        "theme": "black", "layout": 2,
        "eyebrow": "OROBOROS LABS  //  NANITE HAIR  //  OUTCOMES",
        "title": [
            [("Where ", "white"), ("nothing", "accent")],
            [("grew — ", "white"), ("now grows.", "accent")],
        ],
        "size": 80,
        "subtitle": [
            "Full baldness. Burn scars. Advanced alopecia.",
            "This is the device for all of it.",
        ],
        "features": ["NEW FOLLICLES", "TERMINAL DENSITY", "NATIVE TEXTURE"],
        "footer_left": "VISIBLE IN 10 DAYS · TERMINAL IN 6–10 WEEKS",
        "footer_right": "DEVICE 03",
    },
    {   # Layout B
        "theme": "black", "layout": 1,
        "eyebrow": "OROBOROS LABS  //  NANITE HAIR  //  PROTOCOL",
        "title": [
            [("Peel. ", "white")],
            [("Press. ", "white"), ("Done.", "accent")],
        ],
        "size": 84,
        "subtitle": [
            "Apply the mesh. Tap the button. Sleep on it.",
            "Seventy-two hours later, remove or let it absorb.",
        ],
        "features": ["ONE PATCH", "ONE ACTIVATION", "SHOWER-SAFE", "SELF-ABSORBING"],
        "footer_left": "APPLICATION TIME ~2 MIN",
        "footer_right": "OROBOROS LABS",
    },
    {   # Layout D — stats
        "theme": "black", "layout": 3,
        "eyebrow": "OROBOROS LABS  //  NANITE HAIR  //  NUMBERS",
        "title": [
            [("One patch. ", "white")],
            [("A whole ", "white"), ("new scalp.", "accent")],
        ],
        "size": 68,
        "subtitle": [
            "Reconstructed density targets — battery build.",
        ],
        "features": [],
        "stats": [
            ("10⁶",  "NANITES / cm²"),
            ("72h",   "WEAR TIME"),
            ("5d",    "FIRST SHAFTS"),
            ("85%",   "TARGET DENSITY"),
        ],
        "footer_left": "NANITE REGENERATIVE SERIES",
        "footer_right": "DEVICE 03",
    },
]


# ---------------------------------------------------------------------------
# Render entry point
# ---------------------------------------------------------------------------

def render_set(cards, out_dir: Path, prefix: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, card in enumerate(cards, 1):
        out = out_dir / f"{prefix}-card{i:02d}.gif"
        print(f"Rendering {out.name} (layout {card.get('layout', 0)}, {FRAMES} frames) ...")
        render_card_to_gif(card, out)
        print(f"  -> {out}  ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        render_set(
            CARDS_IMMORTALITY,
            Path("/mnt/j/oroborian-medical-technology-level-5_immortality-classification/x-cards"),
            "immortality",
        )
        render_set(
            CARDS_HAIR_HARMONIC,
            Path("/mnt/j/oroboros-phi-harmonic-hair-growth-device/x-cards"),
            "hair",
        )
        render_set(
            CARDS_NANITE_HAIR,
            Path("/mnt/j/oroboros-nanite-hair-regrowth-unit/x-cards"),
            "nanite-hair",
        )
    else:
        render_set(CARDS_HAIR_HARMONIC, HERE, "hair")
