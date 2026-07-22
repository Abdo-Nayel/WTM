from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    import subprocess
    import sys

    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "-q"])
    from PIL import Image, ImageDraw

out = Path(r"E:\WorkTaskMe\mobile\assets\images")
out.mkdir(parents=True, exist_ok=True)


def make_icon(path: Path, size: int = 1024) -> None:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    margin = int(size * 0.06)
    d.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=int(size * 0.22),
        fill=(79, 70, 229, 255),
    )
    gx0, gy0 = int(size * 0.18), int(size * 0.22)
    gw, gh = int(size * 0.42), int(size * 0.48)
    d.rounded_rectangle(
        [gx0, gy0, gx0 + gw, gy0 + gh],
        radius=int(size * 0.05),
        outline=(255, 255, 255, 235),
        width=max(4, size // 40),
    )
    d.rounded_rectangle(
        [gx0, gy0, gx0 + gw, gy0 + int(gh * 0.22)],
        radius=int(size * 0.05),
        fill=(255, 255, 255, 235),
    )
    cx, cy, r = int(size * 0.70), int(size * 0.64), int(size * 0.16)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(16, 185, 129, 255))
    w = max(6, size // 28)
    d.line(
        [(cx - r * 0.45, cy), (cx - r * 0.05, cy + r * 0.35), (cx + r * 0.48, cy - r * 0.35)],
        fill=(255, 255, 255, 255),
        width=w,
        joint="curve",
    )
    img.save(path)


make_icon(out / "app_icon.png", 1024)
make_icon(out / "splash_logo.png", 512)
print("wrote", out / "app_icon.png", out / "splash_logo.png")
