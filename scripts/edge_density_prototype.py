"""
Edge-density depletion prototype.

Instead of counting individual nails/screws (which OWL-ViT can't do reliably
in a dense pile — see BACKLOG.md), this estimates *pile depth* per partition
using edge density: a deep tangled pile of overlapping metal parts has far
more edges/glare per pixel than a thin single layer, even when both cover
roughly the same area. That gives a percentage-based, spatially-local signal
without needing per-object detection or true depth sensing.

For each video: samples a handful of frames, picks the one with the highest
overall edge density (a cheap proxy for "drawer open, contents visible" vs.
"drawer closed / mid-transition, mostly blank"), then computes per-drawer
edge density (fraction of ROI pixels that are Canny edges) on that frame.

Usage:
    python scripts/edge_density_prototype.py [video ...] [--config config/config.yaml]

With no videos given, processes every video in config.video.watch_directory
and config.video.archive_directory (so it picks up already-processed/archived
videos too).
"""
import argparse
import sys
from pathlib import Path

import cv2
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.core.edge_density import edge_density


def pick_best_frame(video_path, n_samples=6):
    """Sample n_samples frames and return the one with highest overall edge
    density, as a cheap proxy for 'contents visible' vs. 'closed/blank'."""
    cap = cv2.VideoCapture(str(video_path))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_count <= 0:
        cap.release()
        raise ValueError(f"Could not read frame count for {video_path}")

    best = None
    for i in range(n_samples):
        idx = int((i + 1) * frame_count / (n_samples + 1))
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        score = edge_density(gray)
        if best is None or score > best[0]:
            best = (score, idx, frame)

    cap.release()
    if best is None:
        raise ValueError(f"Could not read any frame from {video_path}")
    return best[1], best[2]


def analyze_video(video_path, drawers):
    w_expected, h_expected = None, None
    cap = cv2.VideoCapture(str(video_path))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    frame_idx, frame = pick_best_frame(video_path)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    results = {}
    for drawer_id, d in drawers.items():
        x1, y1, x2, y2 = d["roi"]
        roi = gray[y1:y2, x1:x2]
        if roi.size == 0:
            results[drawer_id] = None
            continue
        results[drawer_id] = edge_density(roi)

    return {"frame_size": (w, h), "frame_idx": frame_idx, "densities": results}


def main():
    parser = argparse.ArgumentParser(description="Edge-density depletion prototype")
    parser.add_argument("videos", nargs="*", help="Video files to analyze (default: all in watch/archive dirs)")
    parser.add_argument("--config", default="config/config.yaml", help="Config file to read drawers/ROIs from")
    args = parser.parse_args()

    config = yaml.safe_load(Path(args.config).read_text())
    drawers = config.get("drawers", {})

    if args.videos:
        videos = [Path(v) for v in args.videos]
    else:
        dirs = [
            Path(config["video"]["watch_directory"]),
            Path(config["video"].get("archive_directory", "data/processed")),
        ]
        extensions = {e.lower().lstrip(".") for e in config["video"].get("video_extensions", ["mp4"])}
        videos = sorted(
            (p for d in dirs if d.exists() for p in d.glob("*") if p.suffix.lower().lstrip(".") in extensions),
            key=lambda p: p.name,
        )

    if not videos:
        print("No videos found.")
        sys.exit(1)

    reference_size = None
    per_video = []
    for video in videos:
        result = analyze_video(video, drawers)
        per_video.append((video, result))
        if reference_size is None:
            reference_size = result["frame_size"]

    print(f"\nROI reference frame size: {reference_size}\n")
    print(f"{'video':40s} {'frame_size':>12s} {'frame#':>7s}  " + "  ".join(f"{str(d):>12s}" for d in drawers))
    for video, result in per_video:
        mismatch = " (ORIENTATION MISMATCH — ROI not valid)" if result["frame_size"] != reference_size else ""
        densities = "  ".join(
            f"{result['densities'][d]*100:11.2f}%" if result['densities'][d] is not None else f"{'n/a':>12s}"
            for d in drawers
        )
        print(f"{video.name:40s} {str(result['frame_size']):>12s} {result['frame_idx']:>7d}  {densities}{mismatch}")

    # Baseline (first video with a matching frame size) vs. last such video
    matching = [(v, r) for v, r in per_video if r["frame_size"] == reference_size]
    if len(matching) >= 2:
        baseline_video, baseline = matching[0]
        latest_video, latest = matching[-1]
        depletion_threshold = config["alerts"].get("depletion_threshold", 0.5)

        print(f"\nBaseline: {baseline_video.name}   Latest: {latest_video.name}")
        print(f"{'drawer':20s} {'baseline':>10s} {'latest':>10s} {'ratio':>8s}  status")
        for drawer_id in drawers:
            b = baseline["densities"][drawer_id]
            l = latest["densities"][drawer_id]
            if not b:
                print(f"{str(drawer_id):20s} {'n/a':>10s}")
                continue
            ratio = l / b
            status = "DEPLETION ALERT" if ratio < depletion_threshold else "ok"
            print(f"{str(drawer_id):20s} {b*100:9.2f}% {l*100:9.2f}% {ratio:7.2f}x  {status}")
    else:
        print("\nNot enough same-orientation videos to compare a baseline against a latest reading.")


if __name__ == "__main__":
    main()
