# Counting Methodology

This document explains the methodology and limitations for counting vehicles based on image-level object detection bounding boxes.

## Core Distinction
- **Image-level Count**: The number of bounding boxes (vehicles) detected in a single image.
- **Unique Vehicle Count**: Requires tracking across a video sequence to prevent double-counting. Image-level counting is *not* unique vehicle tracking.

## Challenges with Bounding-Box Counting in Aerial Imagery
Counting vehicles by summing detected bounding boxes is imperfect. Be aware of the following issues:

1. **Missed Detections (False Negatives)**: Models may fail to detect vehicles due to poor lighting, occlusion, or objects being too small.
2. **Duplicate Detections (False Positives)**: High confidence thresholds or inadequate Non-Maximum Suppression (NMS) can lead to the same vehicle being counted multiple times.
3. **Occlusion**: Vehicles partially hidden by trees, buildings, or other vehicles might be missed or detected with a lower confidence.
4. **Tiny Vehicles**: In drone imagery, vehicles can appear very small (few pixels wide). Small object detection is a notoriously hard problem.
5. **Class Confusion**: The model might mistake a van for a car or a truck for a bus, affecting per-class counts.
6. **Frame Edges**: Vehicles cut off by the edges of the image might not be detected or might be counted partially.
7. **Dense Scenes**: In heavy traffic, overlapping boxes make traditional NMS struggle, sometimes suppressing valid detections.
8. **Domain Shift**: Models trained on ground-level imagery (like COCO or UA-DETRAC) often perform poorly on aerial imagery without fine-tuning.

## Mitigation Strategies
- **Filtering**: Use Region of Interest (ROI) filtering to count vehicles only in specific areas.
- **Threshold Tuning**: Adjust confidence and IoU thresholds based on validation performance, not blindly.
- **Area Filtering**: Remove impossibly small or large boxes.
