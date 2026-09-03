"""
Partition setup wizard.

Lets you scrub to a representative frame in a video (e.g. drawer open,
partitions visible), draw ROI boxes over each partition, then asks for
each partition's id, display name, part_type, and alert thresholds, and
writes the result straight into config/config.yaml (backing up the
previous config as config/config.yaml.bak first).

Usage:
    python scripts/find_roi.py [video_path] [--config config/config.yaml] [--frame N]

If video_path is omitted, the newest video in the configured
watch_directory (data/videos by default) is used. If --frame is omitted,
an interactive frame picker opens first.

Controls in the frame-picker window:
    Drag the "Frame" slider  - jump to a frame
    a / d                    - step one frame back / forward
    s                        - select the current frame and continue
    q                        - give up and use frame 0

Controls in the drawing window:
    Click and drag  - draw a rectangle over a partition
    r               - clear all rectangles and start over
    q               - finish drawing and move to labeling
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

import cv2
import yaml

drawing = False
rois = []
current_rect = None
ix, iy = -1, -1
frame_display = None


def mouse_callback(event, x, y, flags, param):
    global drawing, ix, iy, current_rect, frame_display

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        current_rect = (x, y, x, y)

    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        current_rect = (ix, iy, x, y)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        x1, y1 = min(ix, x), min(iy, y)
        x2, y2 = max(ix, x), max(iy, y)
        current_rect = (x1, y1, x2, y2)
        rois.append(current_rect)
        print(f"  Partition {len(rois)}: roi: [{x1}, {y1}, {x2}, {y2}]")


def read_frame_at(video_path, index):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Cannot open video: {video_path}")
        sys.exit(1)
    cap.set(cv2.CAP_PROP_POS_FRAMES, index)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print(f"Could not read frame {index} from video")
        sys.exit(1)
    return frame


def select_frame(video_path):
    """Let the user scrub through the video and pick a frame to draw on."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Cannot open video: {video_path}")
        sys.exit(1)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    if frame_count <= 1:
        return read_frame_at(video_path, 0)

    window = "Pick a frame"
    cv2.namedWindow(window)
    state = {"idx": 0, "frame": read_frame_at(video_path, 0)}

    def show(idx):
        idx = max(0, min(idx, frame_count - 1))
        state["idx"] = idx
        state["frame"] = read_frame_at(video_path, idx)

    cv2.createTrackbar("Frame", window, 0, frame_count - 1, show)

    print("\nScrub to a frame where the partitions are clearly visible (e.g. drawer open).")
    print("Drag the slider, or press 'a'/'d' to step one frame back/forward.")
    print("Press 's' to select the current frame, 'q' to use frame 0.\n")

    while True:
        display = state["frame"].copy()
        cv2.putText(display, f"Frame {state['idx']}/{frame_count - 1}  (a/d=step, s=select, q=frame 0)",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.imshow(window, display)

        key = cv2.waitKey(20) & 0xFF
        if key == ord("s"):
            break
        elif key == ord("q"):
            show(0)
            break
        elif key == ord("a"):
            cv2.setTrackbarPos("Frame", window, max(0, state["idx"] - 1))
        elif key == ord("d"):
            cv2.setTrackbarPos("Frame", window, min(frame_count - 1, state["idx"] + 1))

    cv2.destroyWindow(window)
    return state["frame"]


def draw_rois(frame):
    """Let the user drag out ROI rectangles over the given frame."""
    h, w = frame.shape[:2]
    print(f"\nFrame size: {w}x{h}")
    print("Instructions:")
    print("  Click and drag to draw a rectangle over each partition")
    print("  Press 'r' to clear all rectangles and start over")
    print("  Press 'q' to quit and continue to labeling\n")

    global frame_display
    base_frame = frame.copy()
    cv2.namedWindow("ROI Finder")
    cv2.setMouseCallback("ROI Finder", mouse_callback)

    while True:
        frame_display = base_frame.copy()

        colors = [(0, 255, 0), (255, 128, 0), (0, 128, 255), (255, 0, 128)]
        for i, (x1, y1, x2, y2) in enumerate(rois):
            color = colors[i % len(colors)]
            cv2.rectangle(frame_display, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame_display, f"Partition {i+1}", (x1 + 5, y1 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        if current_rect and drawing:
            x1, y1, x2, y2 = current_rect
            cv2.rectangle(frame_display, (x1, y1), (x2, y2), (200, 200, 200), 1)

        cv2.putText(frame_display, f"Partitions drawn: {len(rois)}  |  r=reset  q=quit",
                    (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.imshow("ROI Finder", frame_display)

        key = cv2.waitKey(20) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("r"):
            rois.clear()
            print("  Cleared all partitions")

    cv2.destroyAllWindows()
    return rois


def prompt(text, default=None):
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{text}{suffix}: ").strip()
    return value if value else default


def prompt_int(text, default):
    value = prompt(text, str(default))
    try:
        return int(value)
    except (TypeError, ValueError):
        print(f"  Not a number, using default ({default})")
        return default


def slugify(name, fallback):
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    return slug or fallback


def label_partitions(rois, existing_text_queries):
    """Interactively collect metadata for each drawn ROI box."""
    text_queries = list(existing_text_queries)
    drawers = {}

    print("\n--- Label each partition ---")
    for i, (x1, y1, x2, y2) in enumerate(rois, start=1):
        print(f"\nPartition {i}  (roi: [{x1}, {y1}, {x2}, {y2}])")

        default_id = f"partition_{i}"
        display_name = prompt("  Display name", f"Partition {i}")
        partition_id = slugify(prompt("  Partition id", default_id), default_id)

        if text_queries:
            print("  Existing part types: " + ", ".join(f"{n+1}={q}" for n, q in enumerate(text_queries)))
        choice = prompt("  Part type (number to reuse, or type a new one)", text_queries[0] if text_queries else "part")
        if choice.isdigit() and 1 <= int(choice) <= len(text_queries):
            part_type = text_queries[int(choice) - 1]
        else:
            part_type = choice
            if part_type not in text_queries:
                text_queries.append(part_type)

        min_threshold = prompt_int("  min_threshold (LOW alert below this)", 10)
        critical_threshold = prompt_int("  critical_threshold (CRITICAL alert below this)", 3)

        drawers[partition_id] = {
            "name": display_name,
            "roi": [x1, y1, x2, y2],
            "min_threshold": min_threshold,
            "critical_threshold": critical_threshold,
            "part_type": part_type,
        }

    return drawers, text_queries


def format_drawers_block(drawers):
    lines = ["drawers:"]
    for did, d in drawers.items():
        lines.append(f"  {did}:")
        lines.append(f'    name: "{d["name"]}"')
        lines.append(f'    roi: [{", ".join(str(v) for v in d["roi"])}]')
        lines.append(f'    min_threshold: {d["min_threshold"]}')
        lines.append(f'    critical_threshold: {d["critical_threshold"]}')
        lines.append(f'    part_type: "{d["part_type"]}"')
        lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def format_text_queries_block(queries, indent=2):
    pad = " " * indent
    lines = [f"{pad}text_queries:"]
    for q in queries:
        lines.append(f'{pad}  - "{q}"')
    return "\n".join(lines) + "\n"


def replace_block(text, header_regex, new_block):
    """Replace a YAML block (a header line plus its more-indented body) in place."""
    lines = text.splitlines(keepends=True)
    header_re = re.compile(header_regex)

    start = None
    base_indent = None
    for i, line in enumerate(lines):
        if header_re.match(line):
            start = i
            base_indent = len(line) - len(line.lstrip(" "))
            break
    if start is None:
        raise ValueError(f"Could not find a block matching {header_regex!r} in config")

    end = start + 1
    while end < len(lines):
        stripped = lines[end].strip()
        if stripped == "":
            end += 1
            continue
        indent = len(lines[end]) - len(lines[end].lstrip(" "))
        if indent <= base_indent:
            break
        end += 1

    separator = "\n" if end < len(lines) else ""
    new_lines = lines[:start] + [new_block + separator] + lines[end:]
    return "".join(new_lines)


def upsert_scalar(text, header_regex, key, value):
    """Set a `key: value` line inside a YAML block, adding it right after
    the header if the key isn't already present."""
    lines = text.splitlines(keepends=True)
    header_re = re.compile(header_regex)

    start = None
    base_indent = None
    for i, line in enumerate(lines):
        if header_re.match(line):
            start = i
            base_indent = len(line) - len(line.lstrip(" "))
            break
    if start is None:
        raise ValueError(f"Could not find a block matching {header_regex!r} in config")

    child_indent = " " * (base_indent + 2)
    key_re = re.compile(rf"^{re.escape(child_indent)}{re.escape(key)}:\s.*$")

    end = start + 1
    while end < len(lines):
        stripped = lines[end].strip()
        if stripped == "":
            end += 1
            continue
        indent = len(lines[end]) - len(lines[end].lstrip(" "))
        if indent <= base_indent:
            break
        if key_re.match(lines[end]):
            lines[end] = f"{child_indent}{key}: {value}\n"
            return "".join(lines)
        end += 1

    lines.insert(start + 1, f"{child_indent}{key}: {value}\n")
    return "".join(lines)


def find_default_video(config):
    watch_dir = Path(config.get("video", {}).get("watch_directory", "data/videos"))
    extensions = {e.lower().lstrip(".") for e in config.get("video", {}).get("video_extensions", ["mp4"])}
    candidates = [p for p in watch_dir.glob("*") if p.is_file() and p.suffix.lower().lstrip(".") in extensions]
    if not candidates:
        print(f"No videos found in {watch_dir}. Pass a video path explicitly.")
        sys.exit(1)
    return max(candidates, key=lambda p: p.stat().st_mtime)


def main():
    parser = argparse.ArgumentParser(description="Draw and label partitions, then update config.yaml")
    parser.add_argument("video", nargs="?", help="Video to use for drawing (default: newest in watch_directory)")
    parser.add_argument("--config", default="config/config.yaml", help="Config file to update")
    parser.add_argument("--frame", type=int, help="Frame number to draw on (skips the interactive frame picker)")
    args = parser.parse_args()

    config_path = Path(args.config)
    config_text = config_path.read_text()
    config = yaml.safe_load(config_text)

    video_path = Path(args.video) if args.video else find_default_video(config)
    print(f"Using video: {video_path}")

    frame = read_frame_at(video_path, args.frame) if args.frame is not None else select_frame(video_path)

    rois = draw_rois(frame)
    if not rois:
        print("No partitions drawn, nothing to save.")
        return

    existing_queries = config.get("model", {}).get("text_queries", [])
    drawers, text_queries = label_partitions(rois, existing_queries)

    updated_text = replace_block(config_text, r"^drawers:\s*$", format_drawers_block(drawers))
    updated_text = replace_block(updated_text, r"^\s*text_queries:\s*$", format_text_queries_block(text_queries))

    h, w = frame.shape[:2]
    updated_text = upsert_scalar(
        updated_text, r"^video:\s*$", "roi_frame_size",
        f"[{w}, {h}]  # videos must match this frame size or they're skipped as a mismatch"
    )

    backup_path = config_path.with_suffix(config_path.suffix + ".bak")
    shutil.copy(config_path, backup_path)
    config_path.write_text(updated_text)

    print(f"\nSaved {len(drawers)} partition(s) to {config_path}")
    print(f"Previous config backed up to {backup_path}")


if __name__ == "__main__":
    main()
