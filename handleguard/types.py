"""Shared vocabulary for the whole pipeline.

FROZEN after 7 Sep midday. Three lanes build against these dataclasses in
parallel; changing one mid-flight breaks the other two. If you genuinely need a
new field, announce it in STATE.md before editing.

Imports stdlib + numpy ONLY. This module must stay importable with no torch, no
cv2, no fastapi, no sqlalchemy — it is the one thing every other module depends
on, so it cannot depend on anything heavy.

Unit convention, and the single most important thing in this file:

    Every distance in TrackFeatures is expressed in OBJECT HEIGHTS, and every
    velocity in OBJECT HEIGHTS PER SECOND.

A carton that falls 1.5x its own height fell 1.5 units whether the camera is 3 m
or 8 m away. Pixel thresholds silently stop firing the moment someone nudges the
tripod, and we will be nudging the tripod. Detectors read these normalized
fields and must never touch raw pixel boxes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

# Roles are how detectors ask for tracks without hardcoding class names.
# Mapped from configs/products.yaml.
Role = str  # "actor" | "product" | "support" | "equipment"

BBox = tuple[float, float, float, float]  # x1, y1, x2, y2 in pixels


# --------------------------------------------------------------------------- #
# Perception
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Frame:
    """One decoded frame at inference resolution.

    `t` is seconds from video start and is the ONLY time source downstream.
    Frame skipping happens once, in video.reader, so nothing else needs to know
    the stride — `dt` between consecutive Frames is whatever it is.
    """

    index: int  # index in the decoded (post-skip) sequence
    t: float  # seconds from video start
    image: np.ndarray  # HxWx3 BGR
    w: int
    h: int


@dataclass(frozen=True)
class Detection:
    cls: str  # key from products.yaml, e.g. "carton"
    role: Role
    conf: float
    xyxy: BBox


@dataclass
class Track:
    """A detection with identity persisted across frames.

    Mutable by design — the tracker updates it in place each frame.
    """

    id: int
    cls: str
    role: Role
    xyxy: BBox
    conf: float
    first_frame: int
    last_frame: int
    age: int = 0  # frames this track has been seen
    missed: int = 0  # consecutive frames currently lost

    @property
    def height(self) -> float:
        return max(self.xyxy[3] - self.xyxy[1], 1e-6)

    @property
    def width(self) -> float:
        return max(self.xyxy[2] - self.xyxy[0], 1e-6)

    @property
    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.xyxy
        return (x1 + x2) / 2.0, (y1 + y2) / 2.0

    @property
    def bottom_center(self) -> tuple[float, float]:
        x1, _, x2, y2 = self.xyxy
        return (x1 + x2) / 2.0, y2


# --------------------------------------------------------------------------- #
# Temporal features — the scale-invariant layer
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class TrackFeatures:
    """Smoothed, scale-normalized motion state for one track at one frame.

    Read this, not `Track.xyxy`, inside behaviour detectors.
    """

    track_id: int
    t: float

    h_px: float  # box height in pixels — the normalizer, kept for debugging
    cx: float  # centre x, normalized 0-1 by frame width
    cy: float  # centre y, normalized 0-1 by frame height

    # Motion, in object-heights and object-heights/sec. +vy is DOWNWARD
    # (image y grows downward and we keep it that way — no sign surprises).
    vx: float = 0.0
    vy: float = 0.0
    ax: float = 0.0
    ay: float = 0.0

    #: |dx| / (|dx| + |dy|) over the smoothing window. ~0 = pure vertical
    #: (drop), ~1 = pure horizontal (throw/drag). Undefined-safe: 0.0 when
    #: the object has not moved.
    horizontal_ratio: float = 0.0

    #: Distance from box bottom edge down to the floor line, in object heights.
    #: 0 means resting on the floor. None when no floor model is configured.
    floor_gap: float | None = None

    area_px: float = 0.0
    zone: str | None = None

    #: Track ids that appear to physically support this one (overlapping and
    #: immediately below). Feeds stacking and overhang behaviours.
    supported_by: tuple[int, ...] = ()

    #: True when a person track overlaps this product in a hand-like position.
    held_by_person: bool = False

    @property
    def speed(self) -> float:
        """Object-heights per second."""
        return float(np.hypot(self.vx, self.vy))


# --------------------------------------------------------------------------- #
# Behaviour and risk
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class BehaviourEvent:
    """One firing of one detector.

    Detectors emit these freely, possibly on many consecutive frames for the
    same real-world event. events.dedup collapses them. A detector must NOT
    deduplicate, cool down, or assign a risk score — see behaviours/base.py.
    """

    behaviour_id: str  # "B01"
    name: str  # "drop"
    track_ids: tuple[int, ...]
    start_frame: int
    end_frame: int
    start_t: float
    end_t: float

    #: 0-1. Starts at config `base_severity`; a detector may scale it +/-0.15
    #: by magnitude. "How bad is this KIND of event."
    severity: float

    #: 0-1. The detector's own certainty that the event occurred at all.
    #: NEVER folded into severity or risk. See base.confidence_from().
    confidence: float

    #: Measured quantities that justified the firing. JSON-serializable scalars
    #: only — these render directly into the human-readable explanation.
    evidence: dict[str, Any] = field(default_factory=dict)

    zone: str | None = None

    @property
    def duration(self) -> float:
        return max(self.end_t - self.start_t, 0.0)


@dataclass(frozen=True)
class RiskScore:
    """Risk and confidence, deliberately kept apart.

    Risk answers "how harmful could this be if real".
    Confidence answers "how sure are we it is real".
    Collapsing them into one number destroys the supervisor's ability to triage,
    so the UI shows both in separate columns and so does this dataclass.
    """

    score: float  # 0-100
    band: str  # low | medium | high | critical
    confidence: float  # 0-1, passed through from the event

    #: Only the components that applied to this event, each 0-1.
    components: dict[str, float] = field(default_factory=dict)

    #: Weights actually used, AFTER renormalization over the applicable
    #: components. Needed so the UI breakdown adds up to the score shown.
    weights_used: dict[str, float] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Incident — what a supervisor actually sees
# --------------------------------------------------------------------------- #

REVIEW_NEW = "new"
REVIEW_CONFIRMED = "confirmed"
REVIEW_FALSE_POSITIVE = "false_positive"
REVIEW_NEEDS_INVESTIGATION = "needs_investigation"


@dataclass
class Incident:
    id: str  # "INC-0007"
    behaviour_id: str
    name: str

    video_id: str
    session: str  # "S1" | "S3" | "public_heldout" — provenance for metrics
    camera: str

    start_t: float
    end_t: float

    risk: RiskScore

    #: Evidence-based, template-generated. Never claims confirmed damage, never
    #: infers intent, never identifies a person. See risk/explain.py.
    explanation: str

    #: SOP-backed corrective action text from configs/sop_rules.yaml.
    sop: list[str] = field(default_factory=list)

    clip_path: str | None = None
    thumb_path: str | None = None

    track_ids: tuple[int, ...] = ()
    zone: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    review_status: str = REVIEW_NEW
    review_note: str = ""
    created_at: str = ""

    @property
    def duration(self) -> float:
        return max(self.end_t - self.start_t, 0.0)
