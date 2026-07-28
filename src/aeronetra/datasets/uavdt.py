"""
UAVDT dataset adapter interface.

Note on Format Differences:
UAVDT (Unmanned Aerial Vehicle Benchmark: Object Detection and Tracking) annotations
differ significantly from VisDrone. While VisDrone provides detailed vehicle classes
and bounding boxes directly for detection, UAVDT often focuses on tracking (MOT)
and has fewer explicit classes (e.g., car, truck, bus).
The coordinate format and the meaning of occlusion/truncation flags also vary.

Until the exact raw format is rigorously inspected and verified, this module
provides a stub interface. Do NOT fabricate a working converter.
"""
from pathlib import Path
from typing import Dict

def convert_uavdt_dataset(images_dir: Path, labels_dir: Path, output_dir: Path, dry_run: bool = False) -> Dict[str, int]:
    """
    Interface for converting UAVDT dataset to YOLO format.

    TODO:
    1. Inspect raw UAVDT annotation format (MOT vs DET).
    2. Identify column mappings for bbox (e.g. frame_index, target_id, bbox_left, bbox_top, bbox_width, bbox_height, score, class, truncation, occlusion).
    3. Implement class mapping for UAVDT vehicle categories.
    4. Handle sequence-based vs image-based directories.
    5. Write tests using fixtures based on actual UAVDT rows.
    """
    raise NotImplementedError(
        "UAVDT conversion is not yet implemented. Please inspect the dataset format "
        "and complete this adapter before using it."
    )
