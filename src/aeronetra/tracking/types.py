"""Data structures for multi-object tracking."""

from dataclasses import dataclass, field


@dataclass
class TrackSummary:
    """Unique-vehicle accounting for one tracked clip.

    ``total_unique`` counts distinct identities, not detections: a car seen in
    200 frames is one vehicle. ``raw_track_ids`` is the count before the
    minimum-length filter, so the gap between the two is flicker rather than
    traffic, which is the number worth reporting alongside the total.
    """

    total_unique: int
    per_class_unique: dict[str, int] = field(default_factory=dict)
    frames_processed: int = 0
    raw_track_ids: int = 0
    dropped_short_tracks: int = 0
    min_track_length: int = 1
