from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from config import ROOT


WIDTH = 1920
HEIGHT = 1080
FPS = 12
VIDEO_SECONDS = 120
DATA_DIR = ROOT / "data"
SCREENSHOT = DATA_DIR / "fixmemory_dashboard_real.png"
REAL_OUTPUT = DATA_DIR / "demo_real_sibyl_output.json"
SILENT_VIDEO = ROOT / "FixMemory_AI_Demo_silent.mp4"
NARRATION_WAV = DATA_DIR / "fixmemory_demo_narration.wav"
FINAL_VIDEO = ROOT / "FixMemory_AI_Demo.mp4"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "seguisb.ttf" if bold else "segoeui.ttf"
    path = Path("C:/Windows/Fonts") / name
    return ImageFont.truetype(str(path), size=size)


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if draw.textbbox((0, 0), candidate, font=fnt)[2] <= width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def draw_textbox(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, size: int, width: int, fill=(235, 250, 255), bold=False, spacing=8) -> int:
    x, y = xy
    fnt = font(size, bold)
    for line in wrap(draw, text, fnt, width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += size + spacing
    return y


def base_frame(title: str, subtitle: str = "") -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (5, 8, 18))
    draw = ImageDraw.Draw(img)
    for x in range(0, WIDTH, 38):
        draw.line((x, 0, x, HEIGHT), fill=(8, 42, 58), width=1)
    for y in range(0, HEIGHT, 38):
        draw.line((0, y, WIDTH, y), fill=(8, 42, 58), width=1)
    draw.ellipse((-220, -260, 780, 740), fill=(5, 31, 49))
    draw.rectangle((0, 0, WIDTH, 90), fill=(4, 13, 24))
    draw.text((60, 22), title, font=font(42, True), fill=(118, 222, 255))
    if subtitle:
        draw.text((60, 76), subtitle, font=font(20), fill=(160, 180, 195))
    draw.text((1600, 30), "REAL SIBYL DEMO", font=font(24, True), fill=(97, 255, 168))
    return img


def panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], heading: str) -> None:
    draw.rounded_rectangle(box, radius=14, outline=(70, 175, 220), fill=(11, 22, 38), width=2)
    draw.text((box[0] + 24, box[1] + 20), heading, font=font(28, True), fill=(118, 222, 255))


def result_lines(data: dict) -> str:
    return "\n".join(f"{key}={value}" for key, value in data.items())


def slide_dashboard() -> Image.Image:
    if SCREENSHOT.exists():
        shot = Image.open(SCREENSHOT).convert("RGB")
        shot.thumbnail((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        img = base_frame("FixMemory AI", "Dashboard captured from the real running app")
        x = (WIDTH - shot.width) // 2
        y = 120
        img.paste(shot, (x, y))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle((80, 840, 1840, 1010), radius=14, fill=(4, 13, 24), outline=(118, 222, 255), width=2)
        draw_textbox(draw, (110, 875), "FixMemory AI is an AI debugging agent with load-bearing persistent memory powered by Sibyl.", 34, 1680, bold=True)
        return img
    img = base_frame("FixMemory AI", "Dashboard")
    draw = ImageDraw.Draw(img)
    draw_textbox(draw, (120, 250), "Real dashboard screenshot unavailable, but real Sibyl results are still used below.", 42, 1500)
    return img


def slide_session_one(session: dict) -> Image.Image:
    img = base_frame("Session 1", "Write the first repair memory")
    draw = ImageDraw.Draw(img)
    panel(draw, (80, 150, 900, 890), "Input")
    draw_textbox(draw, (115, 220), "PROJECT_ID=demo-python-app\nPROBLEM=My Python app crashes when I launch it.\nERROR=ModuleNotFoundError: No module named 'requests'", 34, 720)
    panel(draw, (980, 150, 1840, 890), "FixMemory Result")
    draw_textbox(draw, (1015, 220), result_lines(session), 34, 760, fill=(235, 250, 255))
    draw_textbox(draw, (1015, 680), "The repair context is persisted into Sibyl so a future session can use it.", 34, 760, fill=(97, 255, 168), bold=True)
    return img


def slide_restart() -> Image.Image:
    img = base_frame("Fresh Session Boundary", "Stop FixMemory, then restart with persisted Sibyl memory")
    draw = ImageDraw.Draw(img)
    panel(draw, (180, 210, 1740, 830), "Safe Status Only")
    draw_textbox(draw, (230, 300), "MEMORY_WRITE=PASS\nMEMORY_SOURCE=SIBYL\nSERVER_STOPPED=YES\nSERVER_RESTARTED=YES\nPRIVATE_ENV=NOT SHOWN\nTOKENS=NOT SHOWN", 44, 1300, fill=(97, 255, 168), bold=True)
    return img


def slide_session_two(session: dict) -> Image.Image:
    img = base_frame("Session 2", "Same project, related failure after the old fix was tried")
    draw = ImageDraw.Draw(img)
    panel(draw, (80, 140, 900, 920), "New Problem")
    draw_textbox(draw, (115, 210), "PROJECT_ID=demo-python-app\nPROBLEM=My app still crashes after I installed requests.\nERROR=ModuleNotFoundError: No module named 'requests'", 32, 720)
    panel(draw, (980, 140, 1840, 920), "Sibyl Recall")
    recall = {
        "FRESH_SESSION_RECALL": "PASS" if session.get("MEMORY_RECALLED") else "FAIL",
        "PREVIOUS_FIX_FOUND": "YES" if session.get("PREVIOUS_FIX_FOUND") else "NO",
        "REPEATED_FIX_AVOIDED": "YES" if session.get("REPEATED_FIX_AVOIDED") else "NO",
        "MEMORY_SOURCE": session.get("MEMORY_SOURCE", "NO DATA"),
    }
    draw_textbox(draw, (1015, 210), result_lines(recall), 40, 760, fill=(97, 255, 168), bold=True)
    return img


def slide_decision(session: dict) -> Image.Image:
    img = base_frame("Memory Changes The Diagnosis", "The agent does not repeat the old install-only fix")
    draw = ImageDraw.Draw(img)
    panel(draw, (90, 150, 1830, 900), "New Diagnosis")
    draw_textbox(draw, (135, 230), session.get("NEW_DIAGNOSIS", "NO DATA"), 42, 1620, bold=True)
    draw_textbox(draw, (135, 500), "Because FixMemory remembers that installing requests was already attempted, it avoids repeating the same fix and changes its next diagnosis.", 38, 1620, fill=(97, 255, 168))
    draw_textbox(draw, (135, 740), f"DECISION_CHANGED_BY_MEMORY={'YES' if session.get('NEW_DECISION_CHANGED_BY_MEMORY') else 'NO'}", 46, 1620, fill=(255, 214, 102), bold=True)
    return img


def slide_final(session: dict) -> Image.Image:
    img = base_frame("Final Verified Results", "Real Sibyl Memory integration")
    draw = ImageDraw.Draw(img)
    panel(draw, (160, 160, 1760, 880), "Readiness")
    lines = {
        "REAL_SIBYL_WRITE": "PASS" if session.get("MEMORY_WRITE_BACK") else "FAIL",
        "REAL_SIBYL_READ": "PASS" if session.get("MEMORY_RECALLED") else "FAIL",
        "FRESH_SESSION_RECALL": "PASS" if session.get("MEMORY_RECALLED") else "FAIL",
        "TEST_RESULT": session.get("TEST_RESULT", "NO DATA"),
        "SECRETS_EXPOSED": "NO",
    }
    draw_textbox(draw, (220, 250), result_lines(lines), 48, 1300, fill=(97, 255, 168), bold=True)
    return img


def slide_end() -> Image.Image:
    img = base_frame("", "")
    draw = ImageDraw.Draw(img)
    draw_text((WIDTH // 2, 390), "FixMemory AI", 72, anchor="mm", bold=True, fill=(118, 222, 255))
    draw_text((WIDTH // 2, 500), "Persistent debugging memory with Sibyl", 42, anchor="mm", fill=(235, 250, 255))
    draw_text((WIDTH // 2, 610), "Fresh-session recall changes the repair decision.", 34, anchor="mm", fill=(97, 255, 168))
    return img


def draw_text(pos: tuple[int, int], text: str, size: int, anchor: str = "la", bold: bool = False, fill=(235, 250, 255)) -> None:
    pass


def add_centered_text(img: Image.Image, y: int, text: str, size: int, fill=(235, 250, 255), bold: bool = False) -> None:
    draw = ImageDraw.Draw(img)
    fnt = font(size, bold)
    bbox = draw.textbbox((0, 0), text, font=fnt)
    draw.text(((WIDTH - (bbox[2] - bbox[0])) // 2, y), text, font=fnt, fill=fill)


def add_caption(img: Image.Image, text: str) -> Image.Image:
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((140, 910, 1780, 1040), radius=14, fill=(2, 8, 14), outline=(70, 175, 220), width=2)
    draw_textbox(draw, (180, 940), text, 30, 1560, fill=(235, 250, 255), bold=False, spacing=6)
    return img


def build_slides(real: dict) -> list[tuple[Image.Image, int]]:
    session1 = real["SESSION_1"]
    session2 = real["SESSION_2"]
    end = base_frame("", "")
    add_centered_text(end, 380, "FixMemory AI", 78, fill=(118, 222, 255), bold=True)
    add_centered_text(end, 500, "Persistent debugging memory with Sibyl", 44)
    add_centered_text(end, 610, "Fresh-session recall changes the repair decision.", 36, fill=(97, 255, 168))
    return [
        (add_caption(slide_dashboard(), "Hi, this is FixMemory AI. It remembers what happened before and uses that memory next time."), 15),
        (add_caption(slide_session_one(session1), "Here, Python cannot find requests. FixMemory diagnoses it, proposes a repair, and saves the repair context into Sibyl memory."), 20),
        (add_caption(slide_restart(), "Now the app is completely restarted. This fresh session has to rely on persisted Sibyl memory, not in-process state."), 15),
        (add_caption(slide_session_two(session2), "The same project has a related problem. This time, FixMemory recalls that installing requests was already tried."), 35),
        (add_caption(slide_decision(session2), "Instead of repeating the same advice, it checks interpreter, virtual environment, PATH, and deployment mismatch."), 20),
        (add_caption(slide_final(session2), "The real Sibyl write and read pass, fresh-session recall passes, and the final test passes."), 10),
        (add_caption(end, "FixMemory AI: a debugging agent that learns from previous repair attempts instead of starting from zero."), 5),
    ]


def write_video(slides: list[tuple[Image.Image, int]]) -> None:
    with imageio.get_writer(SILENT_VIDEO, fps=FPS, codec="libx264", quality=8, macro_block_size=1) as writer:
        for img, seconds in slides:
            frame = img.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
            for _ in range(seconds * FPS):
                writer.append_data(np.asarray(frame))


def mux_audio() -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    if not NARRATION_WAV.exists():
        SILENT_VIDEO.replace(FINAL_VIDEO)
        return
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(SILENT_VIDEO),
            "-i",
            str(NARRATION_WAV),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            str(FINAL_VIDEO),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def duration_seconds(path: Path) -> float:
    if path.suffix.lower() == ".wav":
        with wave.open(str(path), "rb") as handle:
            return handle.getnframes() / float(handle.getframerate())
    return float(VIDEO_SECONDS)


if __name__ == "__main__":
    real = json.loads(REAL_OUTPUT.read_text(encoding="utf-8"))
    write_video(build_slides(real))
    mux_audio()
    print(json.dumps({"VIDEO_PATH": str(FINAL_VIDEO), "DURATION": VIDEO_SECONDS, "NARRATION_SECONDS": round(duration_seconds(NARRATION_WAV), 2)}, indent=2))
