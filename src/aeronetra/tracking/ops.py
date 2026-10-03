"""Operations for turning per-frame detections into persistent tracks.

The tracker is chosen by name and swapped without touching the calling code,
mirroring how ``get_model_adapter()`` makes the detector swappable. Both live
behind the same two calls: build a detector, then drive frames through
:func:`track_frames` or :func:`track_video`.
"""

from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path

import cv2
import numpy as np

from aeronetra.detection.adapters import BaseDetector
from aeronetra.detection.types import TrackedDetection
from aeronetra.tracking.types import TrackSummary

# ByteTrack is the default because it is the lightest tracker Ultralytics ships:
# linear Kalman + IoU association with a two-stage low-confidence rescue, no
# appearance model. BoT-SORT is more accurate on UAV footage — it compensates
# for camera motion — but costs roughly four times the runtime, so it stays a
# documented alternative rather than the default.
DEFAULT_TRACKER = "bytetrack.yaml"


def track_class(detections: list[TrackedDetection]) -> int:
    """The class a whole track is reported as: its most frequent class id.

    A track's class can flicker frame to frame, since a small vehicle can be
    read as car in one frame and van in the next. The majority vote is stable
    and cheap; ties break to the lowest class id so the result is deterministic
    rather than dependent on iteration order.
    """
    if not detections:
        raise ValueError("track_class() needs at least one detection")
    counts = Counter(d.class_id for d in detections)
    return min(counts, key=lambda cid: (-counts[cid], cid))


def summarize_tracks(
    frames: Iterable[list[TrackedDetection]],
    min_track_length: int = 1,
    class_names: dict[int, str] | None = None,
) -> TrackSummary:
    """Counts unique vehicles across already-tracked frames.

    ``min_track_length`` drops tracks seen in fewer than that many frames. A
    detector's false positive usually survives a frame or two before the tracker
    drops it, so this filter is what separates traffic from flicker — and it is
    the difference between a unique count and a count of every transient id.
    """
    if min_track_length < 1:
        raise ValueError(f"min_track_length must be >= 1, got {min_track_length}")

    names = class_names or {}
    per_track: dict[int, list[TrackedDetection]] = defaultdict(list)
    frames_processed = 0
    for frame in frames:
        frames_processed += 1
        for tracked in frame:
            per_track[tracked.track_id].append(tracked)

    per_class: Counter[str] = Counter()
    total = 0
    dropped = 0
    for detections in per_track.values():
        if len(detections) < min_track_length:
            dropped += 1
            continue
        total += 1
        cid = track_class(detections)
        per_class[names.get(cid, str(cid))] += 1

    return TrackSummary(
        total_unique=total,
        per_class_unique=dict(sorted(per_class.items())),
        frames_processed=frames_processed,
        raw_track_ids=len(per_track),
        dropped_short_tracks=dropped,
        min_track_length=min_track_length,
    )


def track_frames(
    adapter: BaseDetector,
    frames: Iterable[np.ndarray],
    tracker: str = DEFAULT_TRACKER,
    conf_thresh: float = 0.25,
    iou_thresh: float = 0.45,
) -> list[list[TrackedDetection]]:
    """Runs the detector and tracker over consecutive frames of one stream.

    ``persist=True`` is passed on every call so the tracker keeps its state,
    which is exactly what makes an identity persist. Frames must therefore come
    from a single video, in order; mixing sources here would let one video's
    identities carry into another.
    """
    tracked_frames: list[list[TrackedDetection]] = []
    for index, frame in enumerate(frames):
        tracked = adapter.track(
            frame,
            persist=True,
            tracker=tracker,
            conf_thresh=conf_thresh,
            iou_thresh=iou_thresh,
        )
        for item in tracked:
            item.frame_index = index
        tracked_frames.append(tracked)
    return tracked_frames


def _track_color(track_id: int) -> tuple[int, int, int]:
    """A stable, well-separated BGR colour for a track id.

    A deterministic hash beats random colours: the same id keeps the same colour
    across frames and across runs, which is what makes a clip readable by eye.
    Stepping the hue by the golden angle keeps neighbouring ids far apart.
    """
    hue = int((track_id * 137) % 180)
    hsv = np.uint8([[[hue, 200, 255]]])
    blue, green, red = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0, 0]
    return int(blue), int(green), int(red)


def draw_tracks(
    image: np.ndarray,
    tracked: list[TrackedDetection],
    thickness: int = 2,
) -> np.ndarray:
    """Draws boxes labelled with their persistent track id and class.

    The id is in the label because that is the whole point of this phase: two
    boxes on the same vehicle across frames should carry the same number, and
    that is only checkable if the number is visible.
    """
    for item in tracked:
        box = item.box
        top_left = (int(round(box.xmin)), int(round(box.ymin)))
        bottom_right = (int(round(box.xmax)), int(round(box.ymax)))
        color = _track_color(item.track_id)
        cv2.rectangle(image, top_left, bottom_right, color, thickness)
        label = f"ID {item.track_id} {item.class_name}"
        cv2.putText(
            image,
            label,
            (top_left[0], max(top_left[1] - 6, 12)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            cv2.LINE_AA,
        )
    return image


def track_video(
    adapter: BaseDetector,
    video_path: str | Path,
    output_path: str | Path | None = None,
    tracker: str = DEFAULT_TRACKER,
    conf_thresh: float = 0.25,
    iou_thresh: float = 0.45,
    min_track_length: int = 1,
    class_names: dict[int, str] | None = None,
    max_frames: int | None = None,
) -> TrackSummary:
    """Tracks a video file and returns its unique-vehicle summary.

    When ``output_path`` is given, an annotated copy is written with each box
    labelled by track id and the running unique count burned into the corner, so
    the count can be checked against the footage rather than trusted from stdout
    alone.

    ``max_frames`` bounds the work for a quick look at a long clip.
    """
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    writer = None
    tracked_frames: list[list[TrackedDetection]] = []
    seen_ids: set[int] = set()
    try:
        index = 0
        while max_frames is None or index < max_frames:
            ok, frame = capture.read()
            if not ok:
                break

            tracked = adapter.track(
                frame,
                persist=True,
                tracker=tracker,
                conf_thresh=conf_thresh,
                iou_thresh=iou_thresh,
            )
            for item in tracked:
                item.frame_index = index
                seen_ids.add(item.track_id)
            tracked_frames.append(tracked)

            if output_path is not None:
                annotated = draw_tracks(frame.copy(), tracked)
                cv2.putText(
                    annotated,
                    f"unique vehicles: {len(seen_ids)}",
                    (12, 28),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2,
                    cv2.LINE_AA,
                )
                if writer is None:
                    height, width = annotated.shape[:2]
                    fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
                    writer = cv2.VideoWriter(
                        str(output_path),
                        cv2.VideoWriter_fourcc(*"mp4v"),
                        fps,
                        (width, height),
                    )
                    if not writer.isOpened():
                        raise ValueError(f"Could not open video writer for {output_path}")
                writer.write(annotated)
            index += 1
    finally:
        capture.release()
        if writer is not None:
            writer.release()

    return summarize_tracks(
        tracked_frames,
        min_track_length=min_track_length,
        class_names=class_names,
    )
