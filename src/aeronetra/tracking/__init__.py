"""Video multi-object tracking: persistent identities and unique counts.

Phase 3 changes what "count" means. Phase 1 counted independent boxes in a
single image; here a tracker associates those boxes across consecutive frames so
a vehicle keeps one identity, and the count becomes *unique vehicles* rather
than detections. The tracker is inference-time only — it is not trained — so
these helpers build on a detector that was already trained for detection.
"""

from aeronetra.tracking.ops import (
    DEFAULT_TRACKER,
    draw_tracks,
    summarize_tracks,
    track_class,
    track_frames,
    track_video,
)
from aeronetra.tracking.types import TrackSummary

__all__ = [
    "DEFAULT_TRACKER",
    "TrackSummary",
    "draw_tracks",
    "summarize_tracks",
    "track_class",
    "track_frames",
    "track_video",
]
