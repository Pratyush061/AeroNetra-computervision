#!/usr/bin/env python3
"""Track vehicles in a video and report the unique count.

This is the Phase 3 demo: the same detector used for image counting, driven
frame by frame through a tracker so each vehicle keeps one identity. ByteTrack
is the default; pass ``--tracker botsort.yaml`` for the more accurate but
roughly four times slower alternative.

Example::

    python scripts/track_video.py \\
        --video data/raw/clip.mp4 \\
        --weights outputs/models/yolo11n_visdrone_best.pt \\
        --model YOLO11n \\
        --min-track-length 5
"""

import argparse
import sys
from pathlib import Path

from aeronetra.config import (
    DEFAULT_CONFIDENCE,
    DEFAULT_IOU,
    get_output_dir,
    load_yaml,
)
from aeronetra.detection.adapters import get_model_adapter
from aeronetra.tracking import DEFAULT_TRACKER, track_video
from aeronetra.utils import ensure_dir


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, help="Input video file")
    parser.add_argument("--weights", required=True, help="Detector weights (.pt or .onnx)")
    parser.add_argument("--model", default="YOLO11n", help="Model name for get_model_adapter()")
    parser.add_argument(
        "--tracker",
        default=DEFAULT_TRACKER,
        help="Tracker config: bytetrack.yaml (default), botsort.yaml, ocsort.yaml, ...",
    )
    parser.add_argument("--conf", type=float, default=DEFAULT_CONFIDENCE)
    parser.add_argument("--iou", type=float, default=DEFAULT_IOU)
    parser.add_argument(
        "--min-track-length",
        type=int,
        default=5,
        help="Frames a track must appear in before it counts as a vehicle",
    )
    parser.add_argument("--max-frames", type=int, default=None, help="Stop after N frames")
    parser.add_argument(
        "--output",
        default=None,
        help="Annotated video path (defaults to outputs/tracking/<clip>_tracked.mp4)",
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--class-names",
        default=None,
        help="YAML file mapping class id -> name, overriding the single 'vehicle' class",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    class_names = {0: "vehicle"}
    if args.class_names:
        loaded = load_yaml(Path(args.class_names))
        class_names = {int(key): str(value) for key, value in loaded.items()}

    output_path = args.output
    if output_path is None:
        output_path = get_output_dir() / "tracking" / f"{Path(args.video).stem}_tracked.mp4"
    ensure_dir(Path(output_path).parent)

    adapter = get_model_adapter(
        model_name=args.model,
        weights_path=args.weights,
        class_names=class_names,
        device=args.device,
    )
    adapter.load_model()

    summary = track_video(
        adapter,
        args.video,
        output_path=output_path,
        tracker=args.tracker,
        conf_thresh=args.conf,
        iou_thresh=args.iou,
        min_track_length=args.min_track_length,
        class_names=class_names,
        max_frames=args.max_frames,
    )

    print(f"Frames processed : {summary.frames_processed}")
    print(f"Unique vehicles  : {summary.total_unique}")
    for name, count in summary.per_class_unique.items():
        print(f"  {name}: {count}")
    print(
        f"Tracks seen      : {summary.raw_track_ids} "
        f"({summary.dropped_short_tracks} dropped as shorter than "
        f"{summary.min_track_length} frames)"
    )
    print(f"Annotated video  : {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
