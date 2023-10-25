from .base import GroundTrackerBase
import numpy as np
from norfair import Detection, Tracker

from typing import List, Tuple, Dict


def vqpy_detections_to_norfair_detections(
    vqpy_detections: List[Dict], current_frame_id
) -> List[Detection]:
    """convert detections_as_xywh to norfair detections"""
    norfair_detections: List[Detection] = []

    for detection in vqpy_detections:
        vqpy_bbox = detection['tlbr'].reshape((2,2))
        vqpy_score = np.array([detection['score'], detection['score']])
        vqpy_index = detection['index']
        norfair_detections.append(
            Detection(
                points=vqpy_bbox,
                scores=vqpy_score,
                vqpy_index=vqpy_index,
                vqpy_frame_id=current_frame_id,
            )
        )

    return norfair_detections


def norfair_tracks_to_vqpy_tracks(tracked_objects, current_frame_id):
    vqpy_tracks = []
    for tracked_object in tracked_objects:
        # tracked_object's last_detections not from current frame: tracked_object is not present in current frame (but still classified as "active" by norfair)
        if tracked_object.last_detection.vqpy_frame_id != current_frame_id:
            continue
        # if in current frame, just use vqpy_index from detection
        vqpy_tracks.append(
            {
                "index": tracked_object.last_detection.vqpy_index,
                "track_id": tracked_object.id,
            }
        )
    return vqpy_tracks

# ref: https://github.com/georgia-tech-db/evadb/blob/c637a714c1e68abb5530b20e3ac0d723fe1da3a4/evadb/functions/trackers/nor_fair.py


class NorfairTracker(GroundTrackerBase):
    input_fields = ["tlbr", "score"]
    output_fields = ["track_id"]

    def __init__(self, distance_function="iou", distance_threshold=0.7):
        self.norfair_tracker = Tracker(
            distance_function=distance_function,
            distance_threshold=distance_threshold,
            # https://github.com/tryolabs/norfair/issues/65
            # set initialization_delay to 0 to start tracking immediately
            initialization_delay=0
        )
        self.prev_frame_id = None

    def update(self, frame_id: int,
               data: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Filter the detected data and associate output data
        returns: the current tracked data and the current lost data
        """
        period = frame_id - self.prev_frame_id if self.prev_frame_id is not None else 1
        self.prev_frame_id = frame_id
        detections = vqpy_detections_to_norfair_detections(data, frame_id)
        tracked_objects = self.norfair_tracker.update(
            detections=detections, period=period
        )
        return (norfair_tracks_to_vqpy_tracks(tracked_objects, frame_id), [])