"""
Generate WorkTaskMe promo showreel + poster for the product tour modal.
Output:
  web/assets/videos/worktaskme_promo.mp4
  web/assets/images/video_poster.jpg
"""
from __future__ import annotations

from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"E:\WorkTaskMe")
WEB = ROOT / "web" / "assets"
OUT_VIDEO = WEB / "videos" / "worktaskme_promo.mp4"
OUT_POSTER = WEB / "images" / "video_poster.jpg"
W, H = 1280, 720
FPS = 24
SECONDS_PER_SLIDE = 5

SLIDES = [
    {
        "eyebrow": "WorkTaskMe",
        "title": "Where Agile Meets\nTeam Scheduling",
        "sub": "Boards · Backlog · Calendar · Realtime",
        "accent": (79, 70, 229),
    },
    {
        "eyebrow": "Agile Boards",
        "title": "Jira-style Kanban\n& Sprint Tracking",
        "sub": "Move issues, set priority, ship faster",
        "accent": (99, 102, 241),
    },
    {
        "eyebrow": "Team Calendar",
        "title": "TeamUp-style\nVisual Scheduling",
        "sub": "Color-coded deadlines & resource sync",
        "accent": (16, 185, 129),
    },
    {
        "eyebrow": "Workspaces",
        "title": "Secure Multi-tenant\nRoles & Invites",
        "sub": "Admin · PM · Member · Viewer",
        "accent": (14, 165, 233),
    },
    {
        "eyebrow": "Realtime",
        "title": "Live Updates &\nNotification Hub",
        "sub": "Everyone stays aligned as work moves",
        "accent": (245, 158, 11),
    },
    {
        "eyebrow": "Get Started",
        "title": "Plan. Assign.\nDeliver — together.",
        "sub": "© 2026 WorkTaskMe · Powered by lyomastech",
        "accent": (79, 70, 229),
    },
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibrib.ttf" if bold else r"C:\Windows\Fonts\calibri.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def lerp(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_slide(slide: dict, progress: float) -> Image.Image:
    """progress 0..1 within the slide for subtle motion."""
    img = Image.new("RGB", (W, H), (11, 18, 32))
    draw = ImageDraw.Draw(img, "RGBA")

    # Mesh background
    for i in range(0, W, 8):
        t = i / W
        c = lerp((15, 23, 42), slide["accent"], 0.15 + 0.25 * abs(0.5 - t))
        draw.line([(i, 0), (i, H)], fill=c + (255,))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    cx = int(980 + 40 * np.sin(progress * np.pi * 2))
    cy = int(180 + 20 * np.cos(progress * np.pi * 2))
    od.ellipse([cx - 260, cy - 260, cx + 260, cy + 260], fill=slide["accent"] + (55,))
    od.ellipse([120, 420, 420, 720], fill=(16, 185, 129, 40))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Card
    card = [120, 110, W - 120, H - 110]
    draw.rounded_rectangle(card, radius=28, fill=(15, 23, 42), outline=(100, 116, 139), width=2)
    # Inner accent bar
    draw.rounded_rectangle([140, 130, 170, H - 130], radius=10, fill=slide["accent"])

    # Logo mark
    draw.rounded_rectangle([200, 150, 260, 210], radius=14, fill=slide["accent"])
    draw.text((218, 162), "W", font=font(36, True), fill=(255, 255, 255))

    ey = font(22, True)
    title_f = font(56, True)
    sub_f = font(26, False)

    draw.text((280, 165), slide["eyebrow"].upper(), font=ey, fill=slide["accent"])

    y = 240
    for line in slide["title"].split("\n"):
        # Soft rise based on progress
        offset = int((1 - min(progress * 3, 1)) * 18)
        draw.text((200, y + offset), line, font=title_f, fill=(248, 250, 252))
        y += 70

    draw.text((200, y + 24), slide["sub"], font=sub_f, fill=(148, 163, 184))

    # Fake UI chips
    chips = ["Board", "Calendar", "Team", "Live"]
    x = 200
    for chip in chips:
        tw = draw.textlength(chip, font=font(18, True))
        draw.rounded_rectangle([x, H - 180, x + tw + 28, H - 146], radius=999, fill=(51, 65, 85))
        draw.text((x + 14, H - 174), chip, font=font(18, True), fill=(226, 232, 240))
        x += int(tw) + 40

    draw.text((200, H - 120), "worktaskme.com", font=font(20, False), fill=(100, 116, 139))
    return img


def main() -> None:
    OUT_VIDEO.parent.mkdir(parents=True, exist_ok=True)
    OUT_POSTER.parent.mkdir(parents=True, exist_ok=True)

    frames: list[np.ndarray] = []
    frames_per = SECONDS_PER_SLIDE * FPS
    for slide in SLIDES:
        for i in range(frames_per):
            progress = i / max(frames_per - 1, 1)
            frame = draw_slide(slide, progress)
            frames.append(np.asarray(frame))

    # Poster = first frame of slide 1 mid-way
    poster = Image.fromarray(frames[frames_per // 3])
    poster.save(OUT_POSTER, "JPEG", quality=90, optimize=True)

    # Encode with bundled ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    writer = imageio.get_writer(
        str(OUT_VIDEO),
        fps=FPS,
        codec="libx264",
        quality=7,
        pixelformat="yuv420p",
        macro_block_size=None,
        ffmpeg_log_level="error",
        output_params=["-movflags", "+faststart"],
    )
    # Ensure even dims for yuv420p
    for arr in frames:
        h, w = arr.shape[:2]
        if w % 2 or h % 2:
            arr = arr[: h - (h % 2), : w - (w % 2)]
        writer.append_data(arr)
    writer.close()

    print(f"ffmpeg={ffmpeg}")
    print(f"video={OUT_VIDEO} size={OUT_VIDEO.stat().st_size}")
    print(f"poster={OUT_POSTER} size={OUT_POSTER.stat().st_size}")
    print(f"duration_s={len(SLIDES) * SECONDS_PER_SLIDE}")


if __name__ == "__main__":
    main()
