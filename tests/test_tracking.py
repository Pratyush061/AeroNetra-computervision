"""Unit tests for video tracking: the frame loop, association and counting.

These use a scripted stub backend rather than real weights, following the
existing adapter tests: the logic under test is the plumbing around a tracker
(persisting state, assigning frame indices, counting identities), none of which
needs a model to be exercised.
"""

from pathlib import Path

import cv2
import numpy as np
import pytest

from aeronetra.detection.adapters import BaseDetector
from aeronetra.detection.types import BoundingBox, Detection, TrackedDetection
from aeronetra.tracking import (
    draw_tracks,
    summarize_tracks,
    track_class,
    track_frames,
    track_video,
)


def _tracked(track_id: int, class_id: int = 0, frame_index: int = 0) -> TrackedDetection:
    return TrackedDetection(
        detection=Detection(
            box=BoundingBox(10.0, 10.0, 40.0, 40.0),
            class_id=class_id,
            class_name=f"class{class_id}",
            confidence=0.9,
        ),
        track_id=track_id,
        frame_index=frame_index,
    )


class _ScriptedTracker(BaseDetector):
    """A backend that replays a scripted list of per-frame tracks.

    It records the arguments it was called with, which is how the tests check
    that state is persisted and the frame index is stamped by the loop.
    """

    def __init__(self, frames: list[list[TrackedDetection]]):
        super().__init__("stub", {0: "car"}, "cpu")
        self._frames = frames
        self.calls: list[dict] = []

    def load_model(self):
        self.model = object()

    def predict(self, image, conf_thresh=0.25, iou_thresh=0.45):
        raise AssertionError("the tracking loop must call track(), not predict()")

    def track(self, image, persist=True, tracker=None, conf_thresh=0.25, iou_thresh=0.45):
        self.calls.append({"persist": persist, "tracker": tracker})
        return self._frames[len(self.calls) - 1]


class _PredictOnlyDetector(BaseDetector):
    """A minimal backend that implements only the detection contract."""

    def load_model(self):
        self.model = object()

    def predict(self, image, conf_thresh=0.25, iou_thresh=0.45):
        return None


def test_backend_without_tracking_says_so():
    detector = _PredictOnlyDetector("stub", {0: "car"}, "cpu")
    detector.load_model()

    with pytest.raises(NotImplementedError, match="does not support tracking"):
        detector.track(np.zeros((10, 10, 3), dtype=np.uint8))


def test_summarize_counts_identities_not_detections():
    # One vehicle across three frames plus another across two: two vehicles,
    # five detections.
    frames = [
        [_tracked(1), _tracked(2)],
        [_tracked(1), _tracked(2)],
        [_tracked(1)],
    ]

    summary = summarize_tracks(frames)

    assert summary.total_unique == 2
    assert summary.frames_processed == 3
    assert summary.raw_track_ids == 2


def test_summarize_drops_tracks_below_the_minimum_length():
    frames = [[_tracked(1)] for _ in range(5)] + [[_tracked(2)]]

    summary = summarize_tracks(frames, min_track_length=3)

    assert summary.total_unique == 1
    assert summary.raw_track_ids == 2
    assert summary.dropped_short_tracks == 1
    assert summary.min_track_length == 3


def test_summarize_reports_per_class_counts():
    frames = [[_tracked(1, class_id=0)], [_tracked(2, class_id=1)]]

    summary = summarize_tracks(frames, class_names={0: "car", 1: "truck"})

    assert summary.per_class_unique == {"car": 1, "truck": 1}


def test_summarize_rejects_a_minimum_length_below_one():
    with pytest.raises(ValueError, match="min_track_length"):
        summarize_tracks([[_tracked(1)]], min_track_length=0)


def test_track_class_uses_the_majority_and_breaks_ties_low():
    majority = [_tracked(1, class_id=1), _tracked(1, class_id=1), _tracked(1, class_id=2)]
    tied = [_tracked(1, class_id=3), _tracked(1, class_id=1)]

    assert track_class(majority) == 1
    # A tie must not depend on iteration order.
    assert track_class(tied) == 1
    assert track_class(list(reversed(tied))) == 1


def test_track_class_rejects_an_empty_track():
    with pytest.raises(ValueError, match="at least one detection"):
        track_class([])


def test_track_frames_persists_state_and_stamps_the_frame_index():
    adapter = _ScriptedTracker([[_tracked(7)], [_tracked(7)]])
    frames = [np.zeros((20, 20, 3), dtype=np.uint8) for _ in range(2)]

    tracked_frames = track_frames(adapter, frames, tracker="bytetrack.yaml")

    assert [call["persist"] for call in adapter.calls] == [True, True]
    assert [call["tracker"] for call in adapter.calls] == ["bytetrack.yaml", "bytetrack.yaml"]
    assert [frame[0].frame_index for frame in tracked_frames] == [0, 1]


def test_draw_tracks_marks_the_image_without_resizing_it():
    image = np.zeros((60, 60, 3), dtype=np.uint8)

    annotated = draw_tracks(image, [_tracked(3)])

    assert annotated.shape == image.shape
    assert annotated.any(), "the track should have drawn something"


def test_track_video_runs_the_loop_and_writes_an_annotated_copy(tmp_path: Path):
    source = tmp_path / "clip.mp4"
    output = tmp_path / "clip_tracked.mp4"
    _write_synthetic_video(source, frames=6)
    adapter = _ScriptedTracker([[_tracked(1)] for _ in range(6)])

    summary = track_video(adapter, source, output_path=output, min_track_length=2)

    assert summary.frames_processed == 6
    assert summary.total_unique == 1
    assert output.exists() and output.stat().st_size > 0


def test_track_video_stops_at_max_frames(tmp_path: Path):
    source = tmp_path / "clip.mp4"
    _write_synthetic_video(source, frames=6)
    adapter = _ScriptedTracker([[_tracked(1)] for _ in range(3)])

    summary = track_video(adapter, source, max_frames=3)

    assert summary.frames_processed == 3
    assert len(adapter.calls) == 3


def test_track_video_rejects_a_missing_file(tmp_path: Path):
    adapter = _ScriptedTracker([])

    with pytest.raises(ValueError, match="Could not open video"):
        track_video(adapter, tmp_path / "absent.mp4")


def _write_synthetic_video(path: Path, frames: int, size: tuple[int, int] = (64, 48)) -> None:
    """Writes a short clip with a moving square, so the loop has real frames."""
    width, height = size
    writer = cv2.VideoWriter(
        str(path), cv2.VideoWriter_fourcc(*"mp4v"), 5.0, (width, height)
    )
    assert writer.isOpened(), "the test environment cannot write mp4"
    try:
        for index in range(frames):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            cv2.rectangle(frame, (index * 3, 10), (index * 3 + 8, 18), (255, 255, 255), -1)
            writer.write(frame)
    finally:
        writer.release()
