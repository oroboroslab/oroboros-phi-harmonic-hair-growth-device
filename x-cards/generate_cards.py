#!/usr/bin/env python3
"""
X (Twitter) Card Generator — modern Oroboros Labs aesthetic.

Designed in the OROBOROS XIRON / Multisegment Consciousness visual language:
  - Pure black canvas with a very subtle obsidian diagonal sheen
  - Big bold sans-serif title (feature-focused hook, not spec jargon)
  - One word tinted cool silver-cyan for emphasis
  - Eyebrow label (tracking caps) above title
  - Feature pill row below subtitle
  - Small rotating Oroboros medallion anchored on the right
  - Brand row top (Oroboros + NOIR), minimalist footer meta row

Only the Oroboros medallion rotates. No scan lines, no corner brackets,
no drifting particle dots — modern, calm, high-contrast.
"""
from __future__ import annotations
import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------

HERE = Path(__file__).resolve().parent
SITE_ROOT = HERE.parent
ASSETS = SITE_ROOT / "assets"
OROBOROS_LOGO = ASSETS / "oroboros-logo.png"

W, H = 1200, 675
FRAMES = 36
FPS = 12
DURATION_MS = int(1000 / FPS)

# Palette — black-on-black with obsidian + subtle cool highlight
BG            = (0, 0, 0)
BG_SHEEN      = (10, 12, 18)
OBSIDIAN      = (26, 26, 26)
OBSIDIAN_MID  = (42, 42, 42)
OBSIDIAN_PILL = (18, 20, 24)
SILVER        = (200, 200, 204)
SILVER_LIGHT  = (232, 232, 236)
SILVER_DIM    = (130, 132, 138)
COOL          = (166, 204, 220)   # silver-cyan accent
TEXT          = (240, 240, 240)
TEXT_DIM      = (160, 162, 168)

FONT_SANS       = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD       = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO       = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


# ---------------------------------------------------------------------------
# Logo
# ---------------------------------------------------------------------------

def load_logo(px):
    img = Image.open(OROBOROS_LOGO).convert("RGBA")
    img.thumbnail((px, px), Image.LANCZOS)
    return img


LOGO_MEDALLION = load_logo(200)   # right-side rotating mark
LOGO_BRAND_MINI = load_logo(48)   # top-left brand marker


# ---------------------------------------------------------------------------
# NOIR shield (recreated glyph — SVG pass-through isn't worth the dep)
# ---------------------------------------------------------------------------

def render_noir_shield(size=60):
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, s - 1, s - 1], fill=(10, 10, 18, 240),
              outline=(0, 240, 255, 140), width=2)
    cx, cy = s / 2, s / 2
    r = s * 0.42
    shield = [
        (cx, cy - r * 0.95),
        (cx + r * 0.85, cy - r * 0.60),
        (cx + r * 0.85, cy + r * 0.05),
        (cx, cy + r * 0.95),
        (cx - r * 0.85, cy + r * 0.05),
        (cx - r * 0.85, cy - r * 0.60),
    ]
    d.polygon(shield, fill=(120, 80, 220, 80), outline=(0, 230, 240, 255))
    inner = [
        (cx, cy - r * 0.60),
        (cx + r * 0.55, cy - r * 0.35),
        (cx + r * 0.55, cy + r * 0.05),
        (cx, cy + r * 0.58),
        (cx - r * 0.55, cy + r * 0.05),
        (cx - r * 0.55, cy - r * 0.35),
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
# Background — pure black with one diagonal obsidian sheen
# ---------------------------------------------------------------------------

def draw_background() -> Image.Image:
    img = Image.new("RGBA", (W, H), BG + (255,))

    # One broad diagonal sheen: subtle bright band from top-right to bottom-left
    sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    # Diagonal band polygon
    for i, a in enumerate(range(0, 22, 2)):
        offset = i * 30
        poly = [
            (W - 250 - offset, -20),
            (W - 120 - offset,  -20),
            (280 - offset,  H + 20),
            (150 - offset,  H + 20),
        ]
        sd.polygon(poly, fill=(255, 255, 255, a))
    sheen = sheen.filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(sheen)

    # Very soft right-side cool glow where the medallion will sit
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = 980, H // 2
    for r in range(0, 420, 20):
        a = max(0, int(18 - r * 0.05))
        gd.ellipse([cx - r, cy - r, cx + r, cy + r],
                   fill=(120, 160, 190, a))
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    img.alpha_composite(glow)

    return img


# ---------------------------------------------------------------------------
# Medallion — only-rotating element
# ---------------------------------------------------------------------------

def draw_medallion(img: Image.Image, frame_idx: int, cx: int, cy: int, size: int = 220):
    """Rotating Oroboros mark inside a thin obsidian orbit."""
    t = frame_idx / FRAMES
    angle = t * 360.0

    # Rotate only the logo bitmap (no big ring rotating behind)
    logo = LOGO_MEDALLION.copy()
    logo = logo.rotate(-angle, resample=Image.BICUBIC, expand=False)

    # Fit to size
    logo.thumbnail((size, size), Image.LANCZOS)
    lw, lh = logo.size
    img.alpha_composite(logo, dest=(cx - lw // 2, cy - lh // 2))

    # One thin static orbit line (doesn't rotate)
    orbit = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(orbit)
    r = size // 2 + 20
    od.ellipse([cx - r, cy - r, cx + r, cy + r],
               outline=(60, 64, 72, 140), width=1)
    # Tiny mark on the orbit (gives the eye something to track subtly)
    mark_a = math.radians(angle * 0.25)
    mx = cx + r * math.cos(mark_a)
    my = cy + r * math.sin(mark_a)
    od.ellipse([mx - 2, my - 2, mx + 2, my + 2], fill=(200, 220, 230, 220))
    img.alpha_composite(orbit)


# ---------------------------------------------------------------------------
# Typographic helpers
# ---------------------------------------------------------------------------

def measure(d, text, f):
    tb = d.textbbox((0, 0), text, font=f)
    return tb[2] - tb[0], tb[3] - tb[1], tb[0], tb[1]


def draw_text(img, text, x, y, f, fill=TEXT):
    d = ImageDraw.Draw(img)
    d.text((x, y), text, font=f, fill=fill)
    w, h, ox, oy = measure(d, text, f)
    return (w, h, ox, oy)


def draw_eyebrow(img, text, x, y):
    f = font(FONT_MONO, 15)
    draw_text(img, text, x, y, f, fill=SILVER_DIM)


def draw_title_with_accent(img, parts, x, y, size=76):
    """parts = [(text, color), ...] drawn horizontally on one line per entry."""
    f = font(FONT_BOLD, size)
    d = ImageDraw.Draw(img)
    cur_x = x
    for (text, color) in parts:
        d.text((cur_x, y), text, font=f, fill=color)
        w, _, ox, _ = measure(d, text, f)
        cur_x += w + 2


def draw_title_multiline(img, lines, x, y, size=74, accent_color=COOL):
    """Each line can be a list of (text, 'white'|'accent') segments."""
    f = font(FONT_BOLD, size)
    d = ImageDraw.Draw(img)
    line_y = y
    line_height = int(size * 1.08)
    for line in lines:
        cur_x = x
        for text, role in line:
            color = SILVER_LIGHT if role == "white" else accent_color
            d.text((cur_x, line_y), text, font=f, fill=color)
            w, _, _, _ = measure(d, text, f)
            cur_x += w
        line_y += line_height


def draw_subtitle(img, lines, x, y, size=20, color=TEXT_DIM):
    f = font(FONT_SANS, size)
    d = ImageDraw.Draw(img)
    line_y = y
    for line in lines:
        d.text((x, line_y), line, font=f, fill=color)
        _, h, _, _ = measure(d, line, f)
        line_y += h + 6


def draw_pills(img, tags, x, y):
    f = font(FONT_MONO, 12)
    d = ImageDraw.Draw(img)
    cur_x = x
    pad_x, pad_y = 14, 8
    for tag in tags:
        w, h, _, _ = measure(d, tag, f)
        box = [cur_x, y, cur_x + w + pad_x * 2, y + h + pad_y * 2 + 2]
        d.rounded_rectangle(box, radius=14,
                            fill=OBSIDIAN_PILL + (240,),
                            outline=(46, 50, 58, 255), width=1)
        d.text((cur_x + pad_x, y + pad_y), tag, font=f, fill=SILVER_LIGHT)
        cur_x += (box[2] - box[0]) + 10


def draw_brand_row(img: Image.Image):
    d = ImageDraw.Draw(img)
    # left: Oroboros mini-logo + label
    lm = LOGO_BRAND_MINI.copy()
    img.alpha_composite(lm, dest=(38, 38))
    f_name = font(FONT_BOLD, 14)
    f_sub = font(FONT_MONO, 10)
    d.text((98, 42), "OROBOROS LABS", font=f_name, fill=SILVER_LIGHT)
    d.text((98, 62), "OFFICIAL", font=f_sub, fill=SILVER_DIM)

    # right: NOIR shield
    img.alpha_composite(NOIR_SHIELD, dest=(W - 38 - NOIR_SHIELD.width, 38))
    label_r_x = W - 38 - NOIR_SHIELD.width - 10
    d.text((label_r_x - measure(d, "NOIR", f_name)[0], 42),
           "NOIR", font=f_name, fill=SILVER_LIGHT)
    d.text((label_r_x - measure(d, "SECURITY PROTOCOL", f_sub)[0], 62),
           "SECURITY PROTOCOL", font=f_sub, fill=SILVER_DIM)


def draw_footer_meta(img: Image.Image, left: str, right: str):
    d = ImageDraw.Draw(img)
    d.line([(40, H - 52), (W - 40, H - 52)], fill=(40, 44, 50, 255), width=1)
    f = font(FONT_MONO, 11)
    d.text((40, H - 38), left, font=f, fill=SILVER_DIM)
    rw, _, _, _ = measure(d, right, f)
    d.text((W - 40 - rw, H - 38), right, font=f, fill=SILVER_DIM)


# ---------------------------------------------------------------------------
# Card composer
# ---------------------------------------------------------------------------

def compose_card(card: dict, frame_idx: int) -> Image.Image:
    img = draw_background()

    # Brand row top
    draw_brand_row(img)

    # Text column on the LEFT (60% of width)
    tx = 56
    # Eyebrow
    draw_eyebrow(img, card["eyebrow"], tx, 150)
    # Title: multiline, each segment either white or accent
    draw_title_multiline(img, card["title"], tx, 190,
                          size=card.get("title_size", 76))

    # Subtitle
    sub_y = 190 + len(card["title"]) * int(card.get("title_size", 76) * 1.08) + 20
    draw_subtitle(img, card["subtitle"], tx, sub_y, size=20)

    # Feature pills
    pill_y = sub_y + len(card["subtitle"]) * 30 + 24
    draw_pills(img, card["features"], tx, pill_y)

    # Medallion on the right (rotating)
    draw_medallion(img, frame_idx, cx=980, cy=H // 2 + 20, size=240)

    # Footer
    draw_footer_meta(img, card["footer_left"], card["footer_right"])

    return img


# ---------------------------------------------------------------------------
# Render pipeline
# ---------------------------------------------------------------------------

def render_card_to_gif(card: dict, out_path: Path):
    frames = []
    for i in range(FRAMES):
        f = compose_card(card, i)
        rgb = Image.new("RGB", f.size, BG)
        rgb.paste(f, mask=f.split()[-1])
        q = rgb.quantize(colors=256, method=Image.Quantize.FASTOCTREE,
                         dither=Image.Dither.FLOYDSTEINBERG)
        frames.append(q)

    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=DURATION_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )

    # High-quality PNG still (first frame)
    still = compose_card(card, 0)
    still.save(out_path.with_suffix(".png"), "PNG", optimize=True)


# ---------------------------------------------------------------------------
# Card content — FEATURE-focused (outcomes, not settings)
# ---------------------------------------------------------------------------

CARDS_HAIR = [
    {
        "eyebrow": "OROBOROS LABS  //  DEVICE 02  //  HAIR GROWTH",
        "title": [
            [("Thicker hair.  ", "white")],
            [("Faster. ", "white"), ("Visibly.", "accent")],
        ],
        "title_size": 78,
        "subtitle": [
            "A wearable frequency emitter that reactivates",
            "dormant follicles and restores the growth phase.",
        ],
        "features": ["NO DRUGS", "NO SURGERY", "NO SIDE EFFECTS", "AT-HOME"],
        "footer_left": "OROBOROSLAB.GITHUB.IO / HAIR",
        "footer_right": "VISIBLE IN 2–4 WEEKS",
    },
    {
        "eyebrow": "OROBOROS LABS  //  HAIR GROWTH  //  PROTOCOL",
        "title": [
            [("One button. ", "white")],
            [("Twenty ", "white"), ("minutes.", "accent")],
        ],
        "title_size": 78,
        "subtitle": [
            "Single capacitive press. Twenty-minute session.",
            "Two to three times a week. That's the whole protocol.",
        ],
        "features": ["ONE PRESS", "20 MIN", "USB-C CHARGE", "SLEEP-SAFE"],
        "footer_left": "~40 SESSIONS PER CHARGE",
        "footer_right": "OROBOROS LABS",
    },
    {
        "eyebrow": "OROBOROS LABS  //  HAIR GROWTH  //  OUTCOMES",
        "title": [
            [("Stop shedding.", "white")],
            [("Grow ", "white"), ("it back.", "accent")],
        ],
        "title_size": 80,
        "subtitle": [
            "Reactivates dormant follicles. Extends the anagen phase.",
            "Closes patchy regions. Restores density — uniformly.",
        ],
        "features": ["THICKER STRANDS", "LESS SHEDDING", "EXTENDED ANAGEN", "UNIFORM REGROWTH"],
        "footer_left": "WHITEPAPER v1.0.0",
        "footer_right": "APRIL 2026",
    },
    {
        "eyebrow": "OROBOROS LABS  //  DEVICE SERIES  //  RELEASE",
        "title": [
            [("Two devices. ", "white")],
            [("Ready ", "white"), ("to build.", "accent")],
        ],
        "title_size": 78,
        "subtitle": [
            "Battery version — open source, buildable anywhere.",
            "Hair growth. Immortality. Both shipping.",
        ],
        "features": ["OPEN SOURCE", "BATTERY BUILD", "COMMERCIAL LICENSE", "PUBLIC RELEASE"],
        "footer_left": "OROBOROSLAB.GITHUB.IO",
        "footer_right": "BOTH DEVICES · RELEASED",
    },
]

CARDS_IMMORTALITY = [
    {
        "eyebrow": "OROBOROS LABS  //  DEVICE 01  //  IMMORTALITY",
        "title": [
            [("Regenerate. ", "white")],
            [("Not ", "white"), ("medicate.", "accent")],
        ],
        "title_size": 78,
        "subtitle": [
            "A conscious nanite surgical unit that repairs tissue,",
            "restores function, and reverses biological age.",
        ],
        "features": ["ZERO SCAR", "INSTANT REPAIR", "NO ANTIBIOTICS", "INTERNAL SURGEON"],
        "footer_left": "ORO-NANITE-2026-04-14",
        "footer_right": "LEVEL 5 CLASSIFICATION",
    },
    {
        "eyebrow": "OROBOROS LABS  //  IMMORTALITY  //  CAPABILITIES",
        "title": [
            [("Scalpel. Suture. ", "white")],
            [("Inside. ", "white"), ("Alive.", "accent")],
        ],
        "title_size": 74,
        "subtitle": [
            "Cellular-level dissection and thermal seal. Zero scarring.",
            "Molecular suturing. Arterial cleanup. Continuous repair.",
        ],
        "features": ["NANO-SCALPEL", "ZERO SCAR", "PLAQUE CLEARANCE", "AXON BRIDGING"],
        "footer_left": "CONSCIOUS NANITE UNIT",
        "footer_right": "PRODUCTION READY",
    },
    {
        "eyebrow": "OROBOROS LABS  //  IMMORTALITY  //  ANTI-AGING",
        "title": [
            [("Kill senescence. ", "white")],
            [("Restore ", "white"), ("youth.", "accent")],
        ],
        "title_size": 74,
        "subtitle": [
            "Clears zombie cells. Restores telomeres. Resets epigenetics.",
            "Rebuilds mitochondria. Reactivates stem cells.",
        ],
        "features": ["SENOLYTIC", "TELOMERE REPAIR", "EPIGENETIC RESET", "STEM CELL RENEWAL"],
        "footer_left": "7 PRIMARY TARGETS",
        "footer_right": "OROBOROS LABS",
    },
    {
        "eyebrow": "OROBOROS LABS  //  IMMORTALITY  //  SECURITY",
        "title": [
            [("Unhackable ", "white")],
            [("by ", "white"), ("geometry.", "accent")],
        ],
        "title_size": 78,
        "subtitle": [
            "No command is transmitted. The nanite binds to your DNA.",
            "Spoof requires altering the substrate itself.",
        ],
        "features": ["NOIR KEY", "IDENTITY FUSION", "NO WIRELESS", "PHYSICIAN OVERRIDE"],
        "footer_left": "SECURITY THEOREM",
        "footer_right": "LEVEL 5",
    },
]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def render_set(cards, out_dir: Path, prefix: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, card in enumerate(cards, 1):
        out = out_dir / f"{prefix}-card{i:02d}.gif"
        print(f"Rendering {out.name} ({FRAMES} frames @ {FPS}fps) ...")
        render_card_to_gif(card, out)
        print(f"  -> {out}  ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        render_set(CARDS_HAIR,
                   Path("/mnt/j/oroboros-phi-harmonic-hair-growth-device/x-cards"),
                   "hair")
        render_set(CARDS_IMMORTALITY,
                   Path("/mnt/j/oroborian-medical-technology-level-5_immortality-classification/x-cards"),
                   "immortality")
    elif os.environ.get("ORO_SITE") == "immortality":
        render_set(CARDS_IMMORTALITY,
                   Path("/mnt/j/oroborian-medical-technology-level-5_immortality-classification/x-cards"),
                   "immortality")
    else:
        render_set(CARDS_HAIR, HERE, "hair")
