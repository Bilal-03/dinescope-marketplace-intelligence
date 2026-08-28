"""Build deterministic DineScope lockup and social-card assets from the master icon."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
BRAND_ASSETS = ROOT / "assets" / "brand"
ICON_PATH = BRAND_ASSETS / "favicon.png"
LOCKUP_PATH = BRAND_ASSETS / "dinescope-lockup.png"
LIGHT_ICON_PATH = BRAND_ASSETS / "dinescope-icon-light.png"
LIGHT_LOCKUP_PATH = BRAND_ASSETS / "dinescope-lockup-light.png"
OG_PATH = BRAND_ASSETS / "og.png"

EVERGREEN = "#123C36"
CORAL = "#EF6A50"
INK = "#172033"
MUTED = "#65736F"
CANVAS = "#F5F4EE"
WHITE = "#FFFFFF"
LIGHT_INK = "#FFF8EF"
LIGHT_MUTED = "#B9D0C7"
LIGHT_MARK = "#E7F3EE"

FONT_REGULAR = Path("/System/Library/Fonts/Supplemental/Trebuchet MS.ttf")
FONT_BOLD = Path("/System/Library/Fonts/Supplemental/Trebuchet MS Bold.ttf")


def font(path: Path, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default()


def contain(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    copy = image.copy()
    copy.thumbnail(size, Image.Resampling.LANCZOS)
    return copy


def build_lockup(icon: Image.Image) -> None:
    canvas = Image.new("RGBA", (700, 180), (0, 0, 0, 0))
    mark = contain(icon, (132, 132))
    canvas.alpha_composite(mark, (14, (canvas.height - mark.height) // 2))
    draw = ImageDraw.Draw(canvas)
    draw.text((164, 36), "DineScope", fill=EVERGREEN, font=font(FONT_BOLD, 55))
    draw.text(
        (166, 102),
        "FOOD MARKETPLACE INTELLIGENCE",
        fill=MUTED,
        font=font(FONT_BOLD, 20),
        spacing=4,
    )
    canvas.save(LOCKUP_PATH, optimize=True)


def build_light_icon(icon: Image.Image) -> Image.Image:
    """Create a high-contrast mark for the evergreen Streamlit sidebar."""

    light = Image.new("RGBA", icon.size, (0, 0, 0, 0))
    source = icon.load()
    target = light.load()
    for y in range(icon.height):
        for x in range(icon.width):
            red, green, blue, alpha = source[x, y]
            if alpha == 0:
                continue
            # Preserve the coral growth arrow; lift the evergreen compass and
            # chart marks to a pale mint that remains legible on #123C36.
            if red > 150 and red > green * 1.15:
                target[x, y] = (red, green, blue, alpha)
            else:
                target[x, y] = (*ImageColor.getrgb(LIGHT_MARK), alpha)
    light.save(LIGHT_ICON_PATH, optimize=True)
    return light


def build_light_lockup(icon: Image.Image) -> None:
    canvas = Image.new("RGBA", (700, 180), (0, 0, 0, 0))
    mark = contain(icon, (132, 132))
    canvas.alpha_composite(mark, (14, (canvas.height - mark.height) // 2))
    draw = ImageDraw.Draw(canvas)
    draw.text((164, 36), "DineScope", fill=LIGHT_INK, font=font(FONT_BOLD, 55))
    draw.text(
        (166, 102),
        "FOOD MARKETPLACE INTELLIGENCE",
        fill=LIGHT_MUTED,
        font=font(FONT_BOLD, 20),
        spacing=4,
    )
    canvas.save(LIGHT_LOCKUP_PATH, optimize=True)


def build_social_card(icon: Image.Image) -> None:
    canvas = Image.new("RGB", (1200, 630), CANVAS)
    draw = ImageDraw.Draw(canvas)

    draw.ellipse((872, -150, 1328, 306), fill="#E6EEE9")
    draw.ellipse((945, 365, 1265, 685), fill="#F8DDD6")
    draw.rounded_rectangle((64, 52, 1136, 578), radius=38, fill=WHITE, outline="#DDE5E1", width=2)
    draw.rounded_rectangle((64, 52, 80, 578), radius=8, fill=CORAL)

    mark = contain(icon, (270, 270))
    canvas.paste(mark, (790, 162), mark)

    draw.text((126, 104), "DineScope", fill=EVERGREEN, font=font(FONT_BOLD, 73))
    draw.text(
        (130, 197),
        "FOOD MARKETPLACE INTELLIGENCE",
        fill=CORAL,
        font=font(FONT_BOLD, 24),
    )
    draw.text((130, 270), "See demand.", fill=INK, font=font(FONT_BOLD, 37))
    draw.text((130, 318), "Understand customers.", fill=INK, font=font(FONT_BOLD, 37))
    draw.text((130, 366), "Prioritize growth.", fill=INK, font=font(FONT_BOLD, 37))
    draw.text(
        (130, 453),
        "Decision intelligence for Product & Growth teams",
        fill=MUTED,
        font=font(FONT_REGULAR, 23),
    )
    draw.rounded_rectangle((130, 509, 415, 546), radius=18, fill="#E9F3F0")
    draw.text((153, 517), "AUDITED · AGGREGATE-ONLY", fill=EVERGREEN, font=font(FONT_BOLD, 16))
    canvas.save(OG_PATH, quality=94, optimize=True)


def main() -> None:
    icon = Image.open(ICON_PATH).convert("RGBA")
    build_lockup(icon)
    light_icon = build_light_icon(icon)
    build_light_lockup(light_icon)
    build_social_card(icon)


if __name__ == "__main__":
    main()
