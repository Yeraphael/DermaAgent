from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(r"F:\GraduationDesign\project\DermaAgent\apps\mobile-user\static\tabs")
OUTPUT_SIZE = 96
LOGICAL_SIZE = 64
SCALE = 8

INACTIVE = "#7E9CBA"
ACTIVE = "#5BE5C3"


def p(value: float) -> float:
    return value * SCALE


def stroke() -> int:
    return int(4 * SCALE)


def new_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    size = LOGICAL_SIZE * SCALE
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    return image, ImageDraw.Draw(image)


def save_image(image: Image.Image, name: str) -> None:
    image = image.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.LANCZOS)
    image.save(ROOT / name, "PNG")


def draw_home(draw: ImageDraw.ImageDraw, color: str) -> None:
    points = [(12, 30.5), (32, 14), (52, 30.5), (52, 50), (12, 50), (12, 30.5)]
    draw.line([(p(x), p(y)) for x, y in points], fill=color, width=stroke(), joint="curve")


def draw_case(draw: ImageDraw.ImageDraw, color: str) -> None:
    draw.rounded_rectangle(
        (p(14), p(14), p(50), p(50)),
        radius=p(10),
        outline=color,
        width=stroke(),
    )
    for x1, y1, x2, y2 in ((24, 23, 40, 23), (24, 31, 40, 31), (24, 39, 34, 39)):
        draw.line((p(x1), p(y1), p(x2), p(y2)), fill=color, width=stroke(), joint="curve")


def draw_qa(draw: ImageDraw.ImageDraw, color: str) -> None:
    draw.rounded_rectangle(
        (p(10), p(18), p(54), p(46)),
        radius=p(8),
        outline=color,
        width=stroke(),
    )
    tail = [(31, 46), (22, 54), (22, 46)]
    draw.line([(p(x), p(y)) for x, y in tail], fill=color, width=stroke(), joint="curve")


def draw_history(draw: ImageDraw.ImageDraw, color: str) -> None:
    draw.rounded_rectangle(
        (p(14), p(20), p(50), p(48)),
        radius=p(6),
        outline=color,
        width=stroke(),
    )
    for x1, y1, x2, y2 in ((24, 30, 40, 30), (24, 38, 36, 38)):
        draw.line((p(x1), p(y1), p(x2), p(y2)), fill=color, width=stroke(), joint="curve")


def draw_profile(draw: ImageDraw.ImageDraw, color: str) -> None:
    draw.ellipse((p(22), p(14), p(42), p(34)), outline=color, width=stroke())
    draw.arc((p(14), p(28), p(50), p(64)), start=200, end=340, fill=color, width=stroke())


def render(name: str, color: str, icon) -> None:
    image, draw = new_canvas()
    icon(draw, color)
    save_image(image, name)


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    render("home.png", INACTIVE, draw_home)
    render("home-active.png", ACTIVE, draw_home)
    render("case.png", INACTIVE, draw_case)
    render("case-active.png", ACTIVE, draw_case)
    render("qa.png", INACTIVE, draw_qa)
    render("qa-active.png", ACTIVE, draw_qa)
    render("history.png", INACTIVE, draw_history)
    render("history-active.png", ACTIVE, draw_history)
    render("profile.png", INACTIVE, draw_profile)
    render("profile-active.png", ACTIVE, draw_profile)


if __name__ == "__main__":
    main()
