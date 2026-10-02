"""Dataset parsers and converters.

Per-dataset helpers with overlapping names (``map_category``,
``convert_to_yolo_format``) live in their own submodules; import them from
``aeronetra.datasets.visdrone`` or ``aeronetra.datasets.uavdt`` respectively.
"""

from aeronetra.datasets.uavdt import (
    UAVDT_VEHICLE_CLASSES,
    convert_uavdt_dataset,
    parse_uavdt_row,
)
from aeronetra.datasets.visdrone import (
    VISDRONE_VEHICLE_CLASSES,
    convert_dataset,
    convert_to_yolo_format,
    map_category,
    parse_visdrone_row,
)

__all__ = [
    "UAVDT_VEHICLE_CLASSES",
    "VISDRONE_VEHICLE_CLASSES",
    "convert_dataset",
    "convert_to_yolo_format",
    "convert_uavdt_dataset",
    "map_category",
    "parse_uavdt_row",
    "parse_visdrone_row",
]
